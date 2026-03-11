#!/usr/bin/env python3
"""Wenyan benchmark suite inspired by pyperf + pyperformance.

This script provides:
- pyperf-like measurement kernel (autorange + warmups + samples)
- pyperformance-like benchmark suite management (manifest + groups)
- comparison report between two JSON results

The benchmark target is Wenyan language implementation (`wenyan.py`) itself.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import statistics
import subprocess
import sys
import time
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable, Iterable, Sequence


預設略過範例 = {
    "clock.wy": "需圖形/DOM 環境，非純 stdout。",
    "tree.wy": "需圖形輸出，非純 stdout。",
    "tree2.wy": "需圖形輸出，非純 stdout。",
}

預設清單檔 = Path("benchmark/wyperformance/MANIFEST")


@dataclass(frozen=True)
class 基準定義:
    """Benchmark declaration parsed from manifest."""

    名稱: str
    案例: str
    標籤: tuple[str, ...]
    說明: str


@dataclass(frozen=True)
class 運行設定:
    """Single benchmark run configuration."""

    樣本數: int
    熱身數: int
    最短秒數: float
    最大迭代: int


@dataclass(frozen=True)
class 運行紀錄:
    """Single benchmark run result."""

    值列: list[float]
    熱身列: list[tuple[int, float]]
    迭代: int


@dataclass(frozen=True)
class 基準結果:
    """One benchmark item output in suite JSON."""

    metadata: dict[str, object]
    runs: list[dict[str, object]]


def 解析參數(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: CLI args excluding program name.

    Returns:
        Parsed argparse namespace.
    """

    parser = argparse.ArgumentParser(description="Wenyan benchmark suite（wyperformance）。")
    子命令 = parser.add_subparsers(dest="cmd")

    跑 = 子命令.add_parser("run", help="執行基準並輸出 JSON。")
    跑.add_argument("--manifest", default=str(預設清單檔), help="MANIFEST 路徑。")
    跑.add_argument(
        "--benchmarks",
        default="<default>",
        help="逗號分隔清單，可含負項（如 a,b,-c）；預設為 <default>。",
    )
    跑.add_argument("--examples-dir", default="examples", help="範例目錄（預設：examples）。")
    跑.add_argument("--include-skipped", action="store_true", help="包含預設略過範例。")
    跑.add_argument("--samples", type=int, default=9, help="每個 benchmark 的樣本數。")
    跑.add_argument("--warmups", type=int, default=1, help="每個 benchmark 的熱身次數。")
    跑.add_argument("--min-time", type=float, default=0.10, help="自動校準最短秒數。")
    跑.add_argument("--max-loops", type=int, default=65536, help="自動校準迭代上限。")
    跑.add_argument("--fast", action="store_true", help="快速模式。")
    跑.add_argument("--rigorous", action="store_true", help="嚴格模式。")
    跑.add_argument("--output", default="benchmark/results/wyperformance.json", help="輸出 JSON。")
    跑.add_argument("--append", action="store_true", help="若輸出檔存在則附加。")

    列 = 子命令.add_parser("list", help="列出可用 benchmark。")
    列.add_argument("--manifest", default=str(預設清單檔), help="MANIFEST 路徑。")

    列組 = 子命令.add_parser("list_groups", help="列出 benchmark 群組。")
    列組.add_argument("--manifest", default=str(預設清單檔), help="MANIFEST 路徑。")

    比 = 子命令.add_parser("compare", help="比較兩份 JSON 結果。")
    比.add_argument("baseline_json", help="基準 JSON。")
    比.add_argument("changed_json", help="新結果 JSON。")
    比.add_argument(
        "-O",
        "--output-style",
        choices=("normal", "table"),
        default="normal",
        help="輸出風格（normal/table）。",
    )
    比.add_argument("--csv", default="", help="可選：輸出 CSV 路徑。")

    參數 = parser.parse_args(list(argv))
    if 參數.cmd is None:
        參數.cmd = "run"
    return 參數


def _取命令第一行(命令: Sequence[str], 工作目錄: Path, 逾時秒數: float = 10.0) -> str:
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
        合併 = " ".join((進程.stderr or 進程.stdout).split())
        if 合併:
            return f"rc={進程.returncode} {合併[:160]}"
        return f"rc={進程.returncode}"

    for 行 in (進程.stdout + "\n" + 進程.stderr).splitlines():
        行 = 行.strip()
        if 行:
            return 行
    return "unknown"


def 載入清單(路徑: Path) -> tuple[dict[str, 基準定義], dict[str, list[tuple[str, str]]]]:
    """Parse MANIFEST and return benchmark definitions + groups.

    Args:
        路徑: Manifest file path.

    Returns:
        (benchmark_definitions, groups)
    """

    內容 = 路徑.read_text(encoding="utf-8")
    區段: str | None = None
    群組名: str | None = None
    基準表: dict[str, 基準定義] = {}
    群組表: dict[str, list[tuple[str, str]]] = {}

    for 原行 in 內容.splitlines():
        行 = 原行.split("#", 1)[0].strip()
        if not 行:
            continue
        if 行.startswith("[") and 行.endswith("]"):
            名 = 行[1:-1].strip()
            if 名 == "benchmarks":
                區段 = "benchmarks"
                群組名 = None
            elif 名.startswith("group "):
                區段 = "group"
                群組名 = 名.split(" ", 1)[1].strip()
                if not 群組名:
                    raise ValueError(f"群組名不可為空：{原行}")
                群組表.setdefault(群組名, [])
            else:
                raise ValueError(f"未知區段：{名}")
            continue

        if 區段 == "benchmarks":
            if 行.startswith("name\t"):
                continue
            欄 = 行.split("\t")
            if len(欄) < 2:
                raise ValueError(f"benchmarks 行欄位不足：{原行}")
            名稱 = 欄[0].strip()
            案例 = 欄[1].strip()
            標籤文 = 欄[2].strip() if len(欄) >= 3 else ""
            說明 = 欄[3].strip() if len(欄) >= 4 else ""
            if not 名稱 or not 案例:
                raise ValueError(f"benchmarks 行缺名稱或案例：{原行}")
            if 名稱 in 基準表:
                raise ValueError(f"benchmark 重複：{名稱}")
            標籤 = tuple(x for x in 標籤文.replace(",", " ").split() if x)
            基準表[名稱] = 基準定義(名稱, 案例, 標籤, 說明)
            continue

        if 區段 == "group":
            assert 群組名 is not None
            操作 = "+"
            目標 = 行
            if 行[0] in "+-":
                操作 = 行[0]
                目標 = 行[1:].strip()
            if not 目標:
                raise ValueError(f"group 行缺目標：{原行}")
            群組表[群組名].append((操作, 目標))
            continue

        raise ValueError(f"內容不在任何區段：{原行}")

    群組表.setdefault("all", [("+", "<all>")])
    if "default" not in 群組表:
        群組表["default"] = [("+", "<all>")]
    return 基準表, 群組表


def _解析選擇字串(文字: str) -> tuple[list[str], list[str]]:
    項列 = [x.strip() for x in 文字.split(",") if x.strip()]
    if not 項列 or 項列 == ["<default>"]:
        return ["default"], []

    正項: list[str] = []
    負項: list[str] = []
    for 項 in 項列:
        if 項.startswith("-"):
            名 = 項[1:].strip()
            if 名:
                負項.append(名)
        else:
            正項.append(項)
    if not 正項:
        正項 = ["all"]
    return 正項, 負項


def _解析群組(
    名稱: str,
    基準表: dict[str, 基準定義],
    群組表: dict[str, list[tuple[str, str]]],
    _路徑: tuple[str, ...] = (),
) -> list[str]:
    if 名稱 in _路徑:
        路 = " -> ".join(_路徑 + (名稱,))
        raise ValueError(f"群組循環：{路}")
    if 名稱 == "<all>" or 名稱 == "all":
        return list(基準表)
    if 名稱 in 基準表:
        return [名稱]
    if 名稱 not in 群組表:
        raise ValueError(f"未知 benchmark 或群組：{名稱}")

    結果: list[str] = []
    已有: set[str] = set()
    for 操作, 目標 in 群組表[名稱]:
        名列 = _解析群組(目標, 基準表, 群組表, _路徑 + (名稱,))
        if 操作 == "+":
            for 名 in 名列:
                if 名 not in 已有:
                    結果.append(名)
                    已有.add(名)
        elif 操作 == "-":
            排除 = set(名列)
            結果 = [名 for 名 in 結果 if 名 not in 排除]
            已有 = set(結果)
        else:
            raise ValueError(f"未知操作：{操作}")
    return 結果


def 選擇基準(
    文字: str,
    基準表: dict[str, 基準定義],
    群組表: dict[str, list[tuple[str, str]]],
) -> list[基準定義]:
    """Resolve benchmark selection expression.

    Args:
        文字: CLI selection expression from `--benchmarks`.
        基準表: Benchmark definitions.
        群組表: Group operations.

    Returns:
        Ordered selected benchmarks.
    """

    正項, 負項 = _解析選擇字串(文字)
    名單: list[str] = []
    已有: set[str] = set()
    for 項 in 正項:
        for 名 in _解析群組(項, 基準表, 群組表):
            if 名 not in 已有:
                名單.append(名)
                已有.add(名)

    排除: set[str] = set()
    for 項 in 負項:
        排除.update(_解析群組(項, 基準表, 群組表))
    名單 = [名 for 名 in 名單 if 名 not in 排除]
    return [基準表[名] for 名 in 名單]


def 載入範例(
    範例目錄: Path,
    包含略過: bool,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Load examples as benchmark dataset.

    Args:
        範例目錄: Directory containing `*.wy`.
        包含略過: Whether to include GUI-oriented examples.

    Returns:
        (examples, skip_notes)
    """

    略過說明: list[str] = []
    例列: list[tuple[str, str]] = []
    for 路徑 in sorted(範例目錄.glob("*.wy")):
        原因 = 預設略過範例.get(路徑.name)
        if 原因 and not 包含略過:
            略過說明.append(f"{路徑.name}: {原因}")
            continue
        內容 = 路徑.read_text(encoding="utf-8")
        例列.append((str(路徑.resolve()), 內容))
    return 例列, 略過說明


def _自動校準(
    作業: Callable[[int], int],
    最短秒數: float,
    最大迭代: int,
) -> int:
    迭代 = 1
    while True:
        起 = time.perf_counter()
        作業(迭代)
        秒 = time.perf_counter() - 起
        if 秒 >= 最短秒數 or 迭代 >= 最大迭代:
            return 迭代
        迭代 *= 2


def _跑一基準(
    名稱: str,
    作業: Callable[[int], int],
    設定: 運行設定,
) -> tuple[基準結果, dict[str, float]]:
    # Smoke test first for clearer failures.
    作業(1)

    迭代 = _自動校準(作業, 設定.最短秒數, 設定.最大迭代)
    熱身列: list[tuple[int, float]] = []
    for _ in range(設定.熱身數):
        起 = time.perf_counter()
        作業(迭代)
        秒 = (time.perf_counter() - 起) / 迭代
        熱身列.append((迭代, 秒))

    值列: list[float] = []
    for _ in range(設定.樣本數):
        起 = time.perf_counter()
        作業(迭代)
        秒 = (time.perf_counter() - 起) / 迭代
        值列.append(秒)

    運行 = 運行紀錄(值列=值列, 熱身列=熱身列, 迭代=迭代)
    統計 = {
        "min": min(值列),
        "max": max(值列),
        "mean": statistics.mean(值列),
        "median": statistics.median(值列),
        "stdev": statistics.stdev(值列) if len(值列) >= 2 else 0.0,
    }
    結果 = 基準結果(
        metadata={
            "name": 名稱,
            "unit": "second",
            "loops": 迭代,
            "warmups": 設定.熱身數,
            "samples": 設定.樣本數,
        },
        runs=[
            {
                "values": list(運行.值列),
                "warmups": [[圈, 值] for 圈, 值 in 運行.熱身列],
                "metadata": {
                    "name": 名稱,
                    "unit": "second",
                    "loops": 運行.迭代,
                },
            }
        ],
    )
    return 結果, 統計


def _表格列寬(表: Sequence[Sequence[str]]) -> list[int]:
    列寬 = [0] * len(表[0])
    for 列 in 表:
        for i, 值 in enumerate(列):
            列寬[i] = max(列寬[i], len(值))
    return 列寬


def _格式化表格(表: Sequence[Sequence[str]]) -> str:
    列寬 = _表格列寬(表)
    邊界 = "+" + "+".join("-" * (w + 2) for w in 列寬) + "+"
    標頭分隔 = "+" + "+".join("=" * (w + 2) for w in 列寬) + "+"
    行列 = [邊界]
    for i, 列 in enumerate(表):
        行 = "|" + "|".join(f" {值.ljust(列寬[j])} " for j, 值 in enumerate(列)) + "|"
        行列.append(行)
        行列.append(標頭分隔 if i == 0 else 邊界)
    return "\n".join(行列)


def _讀結果(path: Path) -> tuple[dict[str, list[float]], dict[str, object]]:
    資料 = json.loads(path.read_text(encoding="utf-8"))
    結果: dict[str, list[float]] = {}
    for 基準 in 資料.get("benchmarks", []):
        metadata = 基準.get("metadata", {})
        名 = metadata.get("name")
        runs = 基準.get("runs", [])
        if not isinstance(名, str) or not runs:
            continue
        run0 = runs[0]
        值列 = run0.get("values", [])
        if isinstance(值列, list) and all(isinstance(x, (int, float)) for x in 值列):
            結果[名] = [float(x) for x in 值列]
    meta = 資料.get("metadata", {})
    if not isinstance(meta, dict):
        meta = {}
    return 結果, meta


_T_DIST_95_CONF_LEVELS = [
    0.0,
    12.706,
    4.303,
    3.182,
    2.776,
    2.571,
    2.447,
    2.365,
    2.306,
    2.262,
    2.228,
    2.201,
    2.179,
    2.160,
    2.145,
    2.131,
    2.120,
    2.110,
    2.101,
    2.093,
    2.086,
    2.080,
    2.074,
    2.069,
    2.064,
    2.060,
    2.056,
    2.052,
    2.048,
    2.045,
    2.042,
]


def _tdist95(df: int) -> float:
    if df >= 200:
        return 1.960
    if df >= 100:
        return 1.984
    if df >= 80:
        return 1.990
    if df >= 60:
        return 2.000
    if df >= 50:
        return 2.009
    if df >= 40:
        return 2.021
    if df >= len(_T_DIST_95_CONF_LEVELS):
        return _T_DIST_95_CONF_LEVELS[-1]
    return _T_DIST_95_CONF_LEVELS[df]


def _顯著性(基準值列: list[float], 新值列: list[float]) -> tuple[bool, float]:
    if len(基準值列) != len(新值列):
        return False, 0.0
    if len(基準值列) < 2:
        return False, 0.0
    基均 = statistics.mean(基準值列)
    新均 = statistics.mean(新值列)
    if abs(基均 - 新均) <= (基均 + 新均) * 0.01:
        return False, 0.0

    自由度 = len(基準值列) + len(新值列) - 2
    基方 = statistics.variance(基準值列)
    新方 = statistics.variance(新值列)
    合併 = ((len(基準值列) - 1) * 基方 + (len(新值列) - 1) * 新方) / 自由度
    誤差 = math.sqrt((2.0 * 合併) / len(基準值列))
    if 誤差 == 0.0:
        return False, 0.0
    t值 = (基均 - 新均) / 誤差
    return abs(t值) >= _tdist95(自由度), t值


def _幾何平均(比率列: Iterable[float]) -> float | None:
    有效 = [x for x in 比率列 if x > 0.0 and math.isfinite(x)]
    if not 有效:
        return None
    return math.exp(sum(math.log(x) for x in 有效) / len(有效))


def _比較輸出(
    基準表: dict[str, list[float]],
    新表: dict[str, list[float]],
    輸出風格: str,
) -> tuple[str, list[tuple[str, float, float, float, str]]]:
    共有 = sorted(set(基準表) & set(新表))
    if not 共有:
        raise ValueError("兩份結果無共同 benchmark。")

    列: list[tuple[str, float, float, float, str]] = []
    比率列: list[float] = []
    for 名 in 共有:
        基均 = statistics.mean(基準表[名])
        新均 = statistics.mean(新表[名])
        比率 = 新均 / 基均 if 基均 > 0 else float("inf")
        比率列.append(比率)
        顯著, t值 = _顯著性(基準表[名], 新表[名])
        if 顯著:
            顯著文 = f"Significant (t={t值:.2f})"
        else:
            顯著文 = "Not significant"
        列.append((名, 基均, 新均, 比率, 顯著文))

    幾何 = _幾何平均(比率列)
    if 輸出風格 == "table":
        表: list[list[str]] = [["Benchmark", "Baseline", "Changed", "Change", "Significance"]]
        for 名, 基均, 新均, 比率, 顯著文 in 列:
            if 比率 >= 1.0:
                變化 = f"{比率:.2f}x slower"
            else:
                變化 = f"{(1.0 / 比率):.2f}x faster"
            表.append([名, f"{基均:.6f} s", f"{新均:.6f} s", 變化, 顯著文])
        if 幾何 is not None:
            if 幾何 >= 1.0:
                變化 = f"{幾何:.2f}x slower"
            else:
                變化 = f"{(1.0 / 幾何):.2f}x faster"
            表.append(["Geometric mean", "(ref)", "-", 變化, "-"])
        return _格式化表格(表), 列

    行: list[str] = []
    for 名, 基均, 新均, 比率, 顯著文 in 列:
        if 比率 >= 1.0:
            變化 = f"{比率:.2f}x slower"
        else:
            變化 = f"{(1.0 / 比率):.2f}x faster"
        行.append(
            f"- {名}: {基均:.6f} s -> {新均:.6f} s ({變化}) [{顯著文}]"
        )
    if 幾何 is not None:
        if 幾何 >= 1.0:
            變化 = f"{幾何:.2f}x slower"
        else:
            變化 = f"{(1.0 / 幾何):.2f}x faster"
        行.append(f"- Geometric mean: {變化}")
    return "\n".join(行), 列


def _建立作業映射(例列: list[tuple[str, str]]) -> dict[str, Callable[[int], int]]:
    import wenyan  # noqa: PLC0415 - local import for benchmark runner

    前處理列: list[tuple[str, str]] = []
    for 文檔名, 原文 in 例列:
        環境 = wenyan._建立編譯環境()
        前處理列.append((文檔名, wenyan._前處理源碼(原文, 文檔名, 環境)))

    def preprocess(迭代: int) -> int:
        累計 = 0
        for _ in range(迭代):
            for 文檔名, 原文 in 例列:
                環境 = wenyan._建立編譯環境()
                累計 += len(wenyan._前處理源碼(原文, 文檔名, 環境))
        return 累計

    def lexer(迭代: int) -> int:
        累計 = 0
        for _ in range(迭代):
            for 文檔名, 文 in 前處理列:
                for _符 in wenyan.詞法分析器(文, 文檔名):
                    累計 += 1
        return 累計

    def parser(迭代: int) -> int:
        累計 = 0
        for _ in range(迭代):
            for 文檔名, 文 in 前處理列:
                程 = wenyan.文法分析器(文, 文檔名).解析程式()
                累計 += len(程.句列)
        return 累計

    def compile_ast(迭代: int) -> int:
        累計 = 0
        for _ in range(迭代):
            for 文檔名, 原文 in 例列:
                模組樹 = wenyan.編譯為PythonAST(原文, 文檔名)
                累計 += len(模組樹.body)
        return 累計

    def compile_code(迭代: int) -> int:
        累計 = 0
        for _ in range(迭代):
            for 文檔名, 原文 in 例列:
                模組樹 = wenyan.編譯為PythonAST(原文, 文檔名)
                代碼 = compile(模組樹, 文檔名, "exec")
                累計 += 代碼.co_stacksize
        return 累計

    def execute(迭代: int) -> int:
        累計 = 0
        空輸出 = io.StringIO()
        for _ in range(迭代):
            for 文檔名, 原文 in 例列:
                模組樹 = wenyan.編譯為PythonAST(原文, 文檔名)
                代碼 = compile(模組樹, 文檔名, "exec")
                執行域: dict[str, object] = {
                    "__name__": "__main__",
                    "__file__": 文檔名,
                    "__wenyan_no_output_hanzi__": True,
                }
                with redirect_stdout(空輸出):
                    exec(代碼, 執行域, 執行域)
                累計 += len(執行域)
        return 累計

    return {
        "preprocess": preprocess,
        "lexer": lexer,
        "parser": parser,
        "compile_ast": compile_ast,
        "compile_code": compile_code,
        "execute": execute,
    }


def _命令_run(參數: argparse.Namespace) -> int:
    if 參數.fast and 參數.rigorous:
        print("[錯誤] --fast 與 --rigorous 不可同時使用。")
        return 2
    if 參數.samples <= 0:
        print("[錯誤] --samples 必須 >= 1。")
        return 2
    if 參數.warmups < 0:
        print("[錯誤] --warmups 必須 >= 0。")
        return 2
    if 參數.min_time <= 0:
        print("[錯誤] --min-time 必須 > 0。")
        return 2
    if 參數.max_loops <= 0:
        print("[錯誤] --max-loops 必須 >= 1。")
        return 2

    工作目錄 = Path(__file__).resolve().parents[1]
    清單路徑 = (工作目錄 / 參數.manifest).resolve()
    範例目錄 = Path(參數.examples_dir).expanduser()
    if not 範例目錄.is_absolute():
        範例目錄 = (工作目錄 / 範例目錄).resolve()
    輸出路徑 = Path(參數.output).expanduser()
    if not 輸出路徑.is_absolute():
        輸出路徑 = (工作目錄 / 輸出路徑).resolve()

    基準表, 群組表 = 載入清單(清單路徑)
    選中 = 選擇基準(參數.benchmarks, 基準表, 群組表)
    if not 選中:
        print("[錯誤] 無 benchmark 可執行。")
        return 2

    例列, 略過說明 = 載入範例(範例目錄, 參數.include_skipped)
    if not 例列:
        print("[錯誤] 範例集為空。")
        return 2

    設定 = 運行設定(
        樣本數=參數.samples,
        熱身數=參數.warmups,
        最短秒數=參數.min_time,
        最大迭代=參數.max_loops,
    )
    if 參數.fast:
        設定 = 運行設定(樣本數=3, 熱身數=1, 最短秒數=0.02, 最大迭代=min(設定.最大迭代, 1024))
    elif 參數.rigorous:
        設定 = 運行設定(樣本數=15, 熱身數=max(3, 設定.熱身數), 最短秒數=max(0.20, 設定.最短秒數), 最大迭代=設定.最大迭代)

    作業映射 = _建立作業映射(例列)

    print(f"Python benchmark suite (Wenyan) - {len(選中)} benchmarks")
    結果列: list[基準結果] = []
    for i, 定義 in enumerate(選中, start=1):
        if 定義.案例 not in 作業映射:
            print(f"[{i}/{len(選中)}] {定義.名稱} ... ERROR: 未知案例 {定義.案例}")
            return 2
        print(f"[{i}/{len(選中)}] {定義.名稱} ... ", end="", flush=True)
        結果, 統計 = _跑一基準(定義.名稱, 作業映射[定義.案例], 設定)
        結果.metadata["tags"] = list(定義.標籤)
        if 定義.說明:
            結果.metadata["description"] = 定義.說明
        結果列.append(結果)
        print(
            "ok (median={:.6f}s mean={:.6f}s stdev={:.6f}s)".format(
                統計["median"], 統計["mean"], 統計["stdev"]
            )
        )

    產生時間 = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    git提交 = _取命令第一行(["git", "rev-parse", "HEAD"], 工作目錄)

    資料 = {
        "version": "wyperf-1.0",
        "metadata": {
            "generated_at_utc": 產生時間,
            "python_version": sys.version.splitlines()[0],
            "python_executable": sys.executable,
            "python_implementation": sys.implementation.name,
            "git_commit": git提交,
            "manifest": str(清單路徑),
            "examples_dir": str(範例目錄),
            "examples_count": len(例列),
            "samples": 設定.樣本數,
            "warmups": 設定.熱身數,
            "min_time_s": 設定.最短秒數,
            "max_loops": 設定.最大迭代,
            "benchmarks_expr": 參數.benchmarks,
            "skip_notes": 略過說明,
        },
        "benchmarks": [asdict(x) for x in 結果列],
    }

    輸出路徑.parent.mkdir(parents=True, exist_ok=True)
    if 參數.append and 輸出路徑.exists():
        原 = json.loads(輸出路徑.read_text(encoding="utf-8"))
        原準 = 原.get("benchmarks", [])
        if not isinstance(原準, list):
            print("[錯誤] --append 目標檔格式錯誤（benchmarks 非 list）。")
            return 2
        名到位: dict[str, int] = {}
        for i, 項 in enumerate(原準):
            名 = 項.get("metadata", {}).get("name") if isinstance(項, dict) else None
            if isinstance(名, str):
                名到位[名] = i
        for 新項 in 資料["benchmarks"]:
            名 = 新項["metadata"]["name"]
            if 名 in 名到位:
                原準[名到位[名]]["runs"].extend(新項["runs"])
            else:
                原準.append(新項)
        原["benchmarks"] = 原準
        原meta = 原.get("metadata", {})
        if isinstance(原meta, dict):
            原meta["last_append_at_utc"] = 產生時間
        輸出路徑.write_text(json.dumps(原, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        if 輸出路徑.exists():
            print(f"[錯誤] 輸出檔已存在：{輸出路徑}（可改用 --append）。")
            return 2
        輸出路徑.write_text(json.dumps(資料, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("")
    print(f"result: {輸出路徑}")
    return 0


def _命令_list(參數: argparse.Namespace) -> int:
    工作目錄 = Path(__file__).resolve().parents[1]
    清單路徑 = (工作目錄 / 參數.manifest).resolve()
    基準表, _ = 載入清單(清單路徑)
    for 名 in sorted(基準表):
        定義 = 基準表[名]
        標籤 = ",".join(定義.標籤)
        print(f"{定義.名稱}\t{定義.案例}\t{標籤}\t{定義.說明}")
    print(f"\nTotal: {len(基準表)} benchmarks")
    return 0


def _命令_list_groups(參數: argparse.Namespace) -> int:
    工作目錄 = Path(__file__).resolve().parents[1]
    清單路徑 = (工作目錄 / 參數.manifest).resolve()
    基準表, 群組表 = 載入清單(清單路徑)
    for 群 in sorted(群組表):
        try:
            名列 = _解析群組(群, 基準表, 群組表)
        except ValueError as 例外:
            print(f"{群}: ERROR {例外}")
            continue
        print(f"{群} ({len(名列)}):")
        for 名 in 名列:
            print(f"- {名}")
        print("")
    return 0


def _命令_compare(參數: argparse.Namespace) -> int:
    基準檔 = Path(參數.baseline_json).expanduser().resolve()
    新檔 = Path(參數.changed_json).expanduser().resolve()
    基準表, _ = _讀結果(基準檔)
    新表, _ = _讀結果(新檔)
    try:
        文本, 列 = _比較輸出(基準表, 新表, 參數.output_style)
    except ValueError as 例外:
        print(f"[錯誤] {例外}")
        return 2
    print(文本)

    if 參數.csv:
        csv路徑 = Path(參數.csv).expanduser().resolve()
        csv路徑.parent.mkdir(parents=True, exist_ok=True)
        with csv路徑.open("w", encoding="utf-8", newline="") as 檔案:
            writer = csv.writer(檔案)
            writer.writerow(["benchmark", "baseline_mean_s", "changed_mean_s", "ratio", "significance"])
            for 名, 基均, 新均, 比率, 顯著文 in 列:
                writer.writerow([名, f"{基均:.9f}", f"{新均:.9f}", f"{比率:.9f}", 顯著文])
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Program entrypoint."""

    參數 = 解析參數(sys.argv[1:] if argv is None else argv)
    if 參數.cmd == "list":
        return _命令_list(參數)
    if 參數.cmd == "list_groups":
        return _命令_list_groups(參數)
    if 參數.cmd == "compare":
        return _命令_compare(參數)
    return _命令_run(參數)


if __name__ == "__main__":
    raise SystemExit(main())

