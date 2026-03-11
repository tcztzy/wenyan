#!/usr/bin/env python3
"""Benchmark Wenyan compiler pipeline on examples/*.wy.

This benchmark suite is inspired by CPython's `pyperformance` workflow:
run a small set of stable workloads multiple times, record medians, and
compare two result JSONs to spot regressions.

The focus here is *compiler* cost (lexer/parser/transformer/compile),
not program runtime.

Outputs:
- JSON: machine-readable benchmark records
- CSV: easy spreadsheet/chart import
- Markdown: ready-to-paste summary table
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import math
import statistics
import subprocess
import sys
import timeit
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable, Iterable, Sequence


預設略過範例 = {
    "clock.wy": "需圖形/DOM 環境，非純 stdout。",
    "tree.wy": "需圖形輸出，非純 stdout。",
    "tree2.wy": "需圖形輸出，非純 stdout。",
}

預設基準 = ("preprocess", "lexer", "parser", "compile_ast", "compile_code")


@dataclass(frozen=True)
class 基準結果:
    """Single benchmark case result."""

    名稱: str
    狀態: str
    原因: str | None
    例數: int
    自動迭代次數: int
    樣本秒: list[float]
    中位數秒: float | None
    平均秒: float | None
    每例中位數秒: float | None


def 解析參數(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Raw argv list (excluding program name).

    Returns:
        Parsed argparse namespace.
    """

    parser = argparse.ArgumentParser(description="Wenyan 編譯器管線 microbench。")
    子命令 = parser.add_subparsers(dest="cmd")

    跑 = 子命令.add_parser("run", help="執行 benchmark 並輸出 JSON/CSV/MD。")
    跑.add_argument("--examples-dir", default="examples", help="範例目錄（預設：examples）。")
    跑.add_argument("--samples", type=int, default=7, help="每個基準取樣次數（預設：7）。")
    跑.add_argument(
        "--min-time",
        type=float,
        default=0.20,
        help="自動決定迭代次數時的目標秒數（預設：0.20）。",
    )
    跑.add_argument(
        "--max-number",
        type=int,
        default=64,
        help="自動決定迭代次數的上限（預設：64）。",
    )
    跑.add_argument(
        "--bench",
        action="append",
        default=[],
        help=f"僅跑指定基準（可重複）。可用：{', '.join(預設基準)}。",
    )
    跑.add_argument("--include-skipped", action="store_true", help="包含預設略過的圖形範例。")
    跑.add_argument(
        "--quick",
        action="store_true",
        help="快速模式（samples=3, min_time=0.05, max_number=16）。",
    )
    跑.add_argument(
        "--result-json",
        default="benchmark/results/compiler_pipeline_benchmark.json",
        help="JSON 結果檔路徑。",
    )
    跑.add_argument(
        "--result-csv",
        default="benchmark/results/compiler_pipeline_benchmark.csv",
        help="CSV 結果檔路徑。",
    )
    跑.add_argument(
        "--result-md",
        default="benchmark/results/compiler_pipeline_benchmark.md",
        help="Markdown 結果檔路徑。",
    )

    比 = 子命令.add_parser("compare", help="對照兩份 benchmark JSON（類似 pyperformance compare）。")
    比.add_argument("baseline_json", help="基準 JSON（較舊/基線）。")
    比.add_argument("contender_json", help="對照 JSON（較新/候選）。")
    比.add_argument(
        "--format",
        choices=("md", "text"),
        default="md",
        help="輸出格式（預設：md）。",
    )

    參數 = parser.parse_args(list(argv))
    if 參數.cmd is None:
        參數.cmd = "run"
    return 參數


def 取摘要(text: str, limit: int = 180) -> str:
    """Return compact one-line summary.

    Args:
        text: Source text (stdout/stderr).
        limit: Maximum returned length.

    Returns:
        One-line compact summary.
    """

    單行 = " ".join(text.split())
    if len(單行) <= limit:
        return 單行
    return f"{單行[:limit]}..."


def 取命令第一行(命令: Sequence[str], 工作目錄: Path, 逾時秒數: float = 10.0) -> str:
    """Run command and return first non-empty line from stdout/stderr.

    Args:
        命令: Full command list.
        工作目錄: Process working directory.
        逾時秒數: Timeout in seconds.

    Returns:
        First non-empty output line, or a compact error marker.
    """

    try:
        進程 = subprocess.run(
            list(命令),
            cwd=str(工作目錄),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=逾時秒數,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as 例外:
        return f"{type(例外).__name__}: {例外}"

    if 進程.returncode != 0:
        合併 = (進程.stderr or 進程.stdout).strip()
        if 合併:
            return f"rc={進程.returncode} {取摘要(合併)}"
        return f"rc={進程.returncode}"

    for 行 in (進程.stdout + "\n" + 進程.stderr).splitlines():
        行 = 行.strip()
        if 行:
            return 行
    return "unknown"


def 載入範例(範例目錄: Path, 包含略過: bool) -> tuple[list[tuple[str, str]], list[str]]:
    """Load example sources into memory.

    Args:
        範例目錄: Directory containing `*.wy` files.
        包含略過: Whether to include GUI-oriented examples normally skipped.

    Returns:
        (examples, skip_notes). Each example is (document_name, source_text).
    """

    略過說明: list[str] = []
    例列: list[tuple[str, str]] = []
    for 路徑 in sorted(範例目錄.glob("*.wy")):
        原因 = 預設略過範例.get(路徑.name)
        if 原因 and not 包含略過:
            略過說明.append(f"{路徑.name}: {原因}")
            continue
        內容 = 路徑.read_text(encoding="utf-8")
        # Use the path as 文檔名 for correct relative-import behavior.
        例列.append((str(路徑.resolve()), 內容))
    return 例列, 略過說明


def _自動決定迭代次數(
    計時器: timeit.Timer,
    目標秒數: float,
    上限: int,
) -> int:
    """Decide a stable loop count (like `timeit autorange` with a cap).

    Args:
        計時器: timeit Timer wrapping one benchmark callable.
        目標秒數: Minimum total runtime target for a single sample.
        上限: Maximum loop count.

    Returns:
        Loop count to use for sampling.
    """
    次數 = 1
    while True:
        gc.collect()
        秒 = 計時器.timeit(number=次數)
        if 秒 >= 目標秒數 or 次數 >= 上限:
            return 次數
        次數 *= 2


def _測量基準(
    名稱: str,
    函數: Callable[[], int],
    例數: int,
    樣本數: int,
    目標秒數: float,
    迭代上限: int,
) -> 基準結果:
    """Measure one benchmark callable and compute summary statistics.

    Args:
        名稱: Benchmark case name.
        函數: Workload callable. Return value is a lightweight sink.
        例數: Number of examples in dataset.
        樣本數: Number of samples to collect.
        目標秒數: Minimum total runtime target for autorange.
        迭代上限: Max loop count for autorange.

    Returns:
        A benchmark record with samples + median/mean.
    """
    try:
        函數()
    except Exception as 例外:  # pragma: no cover - benchmark runner should not crash
        return 基準結果(
            名稱=名稱,
            狀態="error",
            原因=f"{type(例外).__name__}: {例外}",
            例數=例數,
            自動迭代次數=0,
            樣本秒=[],
            中位數秒=None,
            平均秒=None,
            每例中位數秒=None,
        )

    計時器 = timeit.Timer(函數)
    次數 = _自動決定迭代次數(計時器, 目標秒數, 迭代上限)

    樣本秒: list[float] = []
    for _ in range(樣本數):
        gc.collect()
        秒 = 計時器.timeit(number=次數)
        樣本秒.append(秒 / 次數)

    中位數 = statistics.median(樣本秒)
    平均 = statistics.mean(樣本秒)
    每例中位數 = 中位數 / 例數 if 例數 > 0 else None
    return 基準結果(
        名稱=名稱,
        狀態="ok",
        原因=None,
        例數=例數,
        自動迭代次數=次數,
        樣本秒=樣本秒,
        中位數秒=中位數,
        平均秒=平均,
        每例中位數秒=每例中位數,
    )


def 寫CSV(路徑: Path, 結果列: Sequence[基準結果]) -> None:
    """Write benchmark results as a CSV file.

    Args:
        路徑: Output CSV path.
        結果列: Benchmark records.
    """
    路徑.parent.mkdir(parents=True, exist_ok=True)
    with 路徑.open("w", encoding="utf-8", newline="") as 檔案:
        writer = csv.writer(檔案)
        writer.writerow(
            [
                "name",
                "status",
                "reason",
                "examples",
                "autorange_number",
                "median_total_s",
                "mean_total_s",
                "median_per_example_s",
                "samples_s",
            ]
        )
        for 記錄 in 結果列:
            writer.writerow(
                [
                    記錄.名稱,
                    記錄.狀態,
                    記錄.原因 or "",
                    記錄.例數,
                    記錄.自動迭代次數,
                    "" if 記錄.中位數秒 is None else f"{記錄.中位數秒:.9f}",
                    "" if 記錄.平均秒 is None else f"{記錄.平均秒:.9f}",
                    "" if 記錄.每例中位數秒 is None else f"{記錄.每例中位數秒:.9f}",
                    ";".join(f"{x:.9f}" for x in 記錄.樣本秒),
                ]
            )


def 寫Markdown(
    路徑: Path,
    結果列: Sequence[基準結果],
    產生時間: str,
    Python版本: str,
    Wenyan版本: str,
    略過說明: Sequence[str],
    樣本數: int,
    目標秒數: float,
) -> None:
    """Write a Markdown summary table.

    Args:
        路徑: Output Markdown path.
        結果列: Benchmark records.
        產生時間: ISO timestamp in UTC.
        Python版本: `sys.version` first line.
        Wenyan版本: `wenyan.版本號`.
        略過說明: Skip notes.
        樣本數: Number of samples per benchmark case.
        目標秒數: Autorange min-time target.
    """
    路徑.parent.mkdir(parents=True, exist_ok=True)
    排序列 = sorted(
        結果列,
        key=lambda r: (
            0 if r.狀態 == "ok" else 1,
            r.中位數秒 if r.中位數秒 is not None else float("inf"),
            r.名稱,
        ),
    )

    行: list[str] = []
    行.append("# Wenyan Compiler Pipeline Benchmark (examples/*.wy)")
    行.append("")
    行.append(f"- generated_at_utc: `{產生時間}`")
    行.append(f"- python: `{Python版本}`")
    行.append(f"- wenyan.py: `{Wenyan版本}`")
    行.append(f"- samples: `{樣本數}`")
    行.append(f"- min_time_s: `{目標秒數}`")
    if 略過說明:
        行.append("- skipped_examples:")
        for 項 in 略過說明:
            行.append(f"  - {項}")
    行.append("")

    行.append("## Cases (lower is better)")
    行.append("")
    行.append("| case | status | median_total_s | median_per_example_s | note |")
    行.append("|---|---|---:|---:|---|")
    for 記錄 in 排序列:
        行.append(
            "| {名} | {狀} | {總} | {每例} | {註} |".format(
                名=記錄.名稱,
                狀=記錄.狀態,
                總="-" if 記錄.中位數秒 is None else f"{記錄.中位數秒:.6f}",
                每例="-" if 記錄.每例中位數秒 is None else f"{記錄.每例中位數秒:.6f}",
                註=(記錄.原因 or "-").replace("|", "\\|"),
            )
        )

    路徑.write_text("\n".join(行) + "\n", encoding="utf-8")


def _讀結果(path: Path) -> tuple[dict[str, float], dict[str, object]]:
    """Load result JSON and return a name->median mapping + meta dict.

    Args:
        path: Benchmark result JSON path.

    Returns:
        (medians, meta).
    """
    資料 = json.loads(path.read_text(encoding="utf-8"))
    結果: dict[str, float] = {}
    for 記錄 in 資料.get("results", []):
        if 記錄.get("狀態") != "ok":
            continue
        名稱 = 記錄.get("名稱")
        中位數 = 記錄.get("中位數秒")
        if isinstance(名稱, str) and isinstance(中位數, (int, float)):
            結果[名稱] = float(中位數)
    meta = 資料.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    return 結果, meta


def _幾何平均(比率: Iterable[float]) -> float | None:
    """Compute geometric mean for ratios (skip non-finite/<=0 values)."""
    列 = [x for x in 比率 if x > 0.0 and math.isfinite(x)]
    if not 列:
        return None
    return math.exp(sum(math.log(x) for x in 列) / len(列))


def compare(基準JSON: Path, 對照JSON: Path, 輸出格式: str) -> int:
    """Compare two benchmark JSONs and print a table (pyperformance-like).

    Args:
        基準JSON: Baseline JSON file.
        對照JSON: Contender JSON file.
        輸出格式: `md` or `text`.

    Returns:
        Process exit code.
    """
    基準表, 基準meta = _讀結果(基準JSON)
    對照表, 對照meta = _讀結果(對照JSON)

    名單 = sorted(set(基準表) & set(對照表))
    if not 名單:
        print("[錯誤] 兩份結果無共同基準項（或皆非 ok）。")
        return 2

    比率列 = [對照表[名] / 基準表[名] for 名 in 名單]
    幾何 = _幾何平均(比率列)

    if 輸出格式 == "text":
        print(f"baseline: {基準JSON}")
        print(f"contender: {對照JSON}")
        print("")
        for 名 in 名單:
            基 = 基準表[名]
            新 = 對照表[名]
            比率 = 新 / 基
            print(f"- {名}: {基:.6f}s -> {新:.6f}s ({比率:.3f}x)")
        if 幾何 is not None:
            print(f"\ngeo_mean: {幾何:.3f}x")
        return 0

    # md
    基準py = str(基準meta.get("python") or "-")
    對照py = str(對照meta.get("python") or "-")
    print("# Wenyan Compiler Benchmark Compare")
    print("")
    print(f"- baseline_python: `{基準py}`")
    print(f"- contender_python: `{對照py}`")
    print("")
    print("| case | baseline_median_s | contender_median_s | delta | ratio |")
    print("|---|---:|---:|---:|---:|")
    for 名 in 名單:
        基 = 基準表[名]
        新 = 對照表[名]
        差 = 新 - 基
        比率 = 新 / 基
        print(f"| {名} | {基:.6f} | {新:.6f} | {差:+.6f} | {比率:.3f} |")
    if 幾何 is not None:
        print("")
        print(f"- geo_mean_ratio: `{幾何:.3f}x`")
    return 0


def run(參數: argparse.Namespace) -> int:
    """Run benchmark suite and write JSON/CSV/MD outputs.

    Args:
        參數: Parsed CLI args for the `run` subcommand.

    Returns:
        Process exit code.
    """
    if 參數.samples <= 0:
        print("[錯誤] --samples 必須 >= 1")
        return 2
    if 參數.min_time <= 0:
        print("[錯誤] --min-time 必須 > 0")
        return 2
    if 參數.max_number <= 0:
        print("[錯誤] --max-number 必須 >= 1")
        return 2

    if 參數.quick:
        參數.samples = 3
        參數.min_time = 0.05
        參數.max_number = min(參數.max_number, 16)

    工作目錄 = Path(__file__).resolve().parents[1]
    範例目錄 = (工作目錄 / 參數.examples_dir).resolve()
    if not 範例目錄.exists():
        print(f"[錯誤] 範例目錄不存在：{範例目錄}")
        return 2

    # Ensure repository root is importable when running via absolute script path.
    if str(工作目錄) not in sys.path:
        sys.path.insert(0, str(工作目錄))

    import wenyan  # noqa: PLC0415 - local import for benchmark runner

    範例列, 略過說明 = 載入範例(範例目錄, 參數.include_skipped)
    if not 範例列:
        print("[錯誤] 無可用範例可跑 benchmark。")
        return 2

    # Preprocess once so lexer/parser microbench always runs on a valid source
    # stream (some examples rely on macros/import-time expansion).
    處理後列: list[tuple[str, str]] = []
    for 文檔名, 原文 in 範例列:
        環境 = wenyan._建立編譯環境()
        處理後列.append((文檔名, wenyan._前處理源碼(原文, 文檔名, 環境)))

    目標基準: list[str]
    if 參數.bench:
        目標基準 = [x for x in 參數.bench if x]
    else:
        目標基準 = list(預設基準)

    for 名 in 目標基準:
        if 名 not in 預設基準:
            print(f"[錯誤] 未知基準：{名}")
            return 2

    def _詞法() -> int:
        總 = 0
        for 文檔名, 內容 in 處理後列:
            for _ in wenyan.詞法分析器(內容, 文檔名):
                總 += 1
        return 總

    def _文法() -> int:
        總 = 0
        for 文檔名, 內容 in 處理後列:
            程 = wenyan.文法分析器(內容, 文檔名).解析程式()
            總 += len(程.句列)
        return 總

    def _前處理() -> int:
        總 = 0
        for 文檔名, 原文 in 範例列:
            環境 = wenyan._建立編譯環境()
            處理後 = wenyan._前處理源碼(原文, 文檔名, 環境)
            總 += len(處理後)
        return 總

    def _編譯AST() -> int:
        總 = 0
        for 文檔名, 內容 in 範例列:
            模組樹 = wenyan.編譯為PythonAST(內容, 文檔名)
            總 += len(模組樹.body)
        return 總

    def _編譯代碼() -> int:
        總 = 0
        for 文檔名, 內容 in 範例列:
            模組樹 = wenyan.編譯為PythonAST(內容, 文檔名)
            代碼 = compile(模組樹, 文檔名, "exec")
            總 += 代碼.co_stacksize
        return 總

    基準表: dict[str, Callable[[], int]] = {
        "preprocess": _前處理,
        "lexer": _詞法,
        "parser": _文法,
        "compile_ast": _編譯AST,
        "compile_code": _編譯代碼,
    }

    結果列: list[基準結果] = []
    print(f"=== compiler pipeline benchmark: {len(範例列)} examples ===")
    for 名 in 目標基準:
        print(f"- {名} ... ", end="", flush=True)
        結果 = _測量基準(
            名稱=名,
            函數=基準表[名],
            例數=len(範例列),
            樣本數=參數.samples,
            目標秒數=參數.min_time,
            迭代上限=參數.max_number,
        )
        if 結果.狀態 == "ok" and 結果.中位數秒 is not None:
            print(f"ok median={結果.中位數秒:.6f}s per_example={結果.每例中位數秒:.6f}s")
        else:
            print(f"error: {結果.原因}")
        結果列.append(結果)

    產生時間 = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    git提交 = 取命令第一行(["git", "rev-parse", "HEAD"], 工作目錄)
    python版本 = sys.version.splitlines()[0]
    wenyan版本 = getattr(wenyan, "版本號", "unknown")

    json路徑 = (工作目錄 / 參數.result_json).resolve()
    csv路徑 = (工作目錄 / 參數.result_csv).resolve()
    md路徑 = (工作目錄 / 參數.result_md).resolve()

    資料 = {
        "meta": {
            "generated_at_utc": 產生時間,
            "cwd": str(工作目錄),
            "git_commit": git提交,
            "python": python版本,
            "python_executable": sys.executable,
            "python_implementation": sys.implementation.name,
            "wenyan_version": wenyan版本,
            "examples_dir": str(範例目錄),
            "examples_count": len(範例列),
            "samples": 參數.samples,
            "min_time_s": 參數.min_time,
            "max_number": 參數.max_number,
            "benches": 目標基準,
            "skip_notes": 略過說明,
        },
        "results": [asdict(x) for x in 結果列],
    }

    json路徑.parent.mkdir(parents=True, exist_ok=True)
    json路徑.write_text(json.dumps(資料, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    寫CSV(csv路徑, 結果列)
    寫Markdown(
        路徑=md路徑,
        結果列=結果列,
        產生時間=產生時間,
        Python版本=python版本,
        Wenyan版本=str(wenyan版本),
        略過說明=略過說明,
        樣本數=參數.samples,
        目標秒數=參數.min_time,
    )

    print("\n=== output ===")
    print(f"json: {json路徑}")
    print(f"csv : {csv路徑}")
    print(f"md  : {md路徑}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Program entrypoint."""
    參數 = 解析參數(sys.argv[1:] if argv is None else argv)
    if 參數.cmd == "compare":
        return compare(
            基準JSON=Path(參數.baseline_json).expanduser().resolve(),
            對照JSON=Path(參數.contender_json).expanduser().resolve(),
            輸出格式=參數.format,
        )
    return run(參數)


if __name__ == "__main__":
    raise SystemExit(main())
