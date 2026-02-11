#!/usr/bin/env python3
from __future__ import annotations

"""Benchmark Wenyan runtime matrix on examples/*.wy.

This script compares three execution families:
- `wenyan.py` on tox-listed Python factors (resolved by `uv python`)
- `wywy` (self-host via `wenyan.wy`) on tox-listed Python factors
- `@wenyan/cli` on Node/Bun/Deno (direct JS entry)
- `wywy` style on Node/Bun/Deno (`@wenyan/cli wenyan.wy <example>`)

Output files:
- JSON: machine-readable benchmark records
- CSV: easy spreadsheet/chart import
- Markdown: ready-to-paste table for README
"""

import argparse
import csv
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

預設略過範例 = {
    "clock.wy": "需圖形/DOM 環境，非純 stdout。",
    "tree.wy": "需圖形輸出，非純 stdout。",
    "tree2.wy": "需圖形輸出，非純 stdout。",
}

預設CPython環境 = (
    "py38",
    "py39",
    "py310",
    "py311",
    "py312",
    "py313",
    "py314",
)

預設自由執行緒環境 = (
    "py313t",
    "py314t",
)


@dataclass
class 運行目標:
    """A benchmark target runtime."""

    名稱: str
    分組: str
    引擎: str
    命令前綴: list[str]
    版本: str
    可用: bool
    不可用原因: str | None = None


@dataclass
class 運行結果:
    """Benchmark result record for one target runtime."""

    名稱: str
    分組: str
    引擎: str
    版本: str
    狀態: str
    原因: str | None
    命令前綴: list[str]
    例數: int
    輪次秒數: list[float]
    總耗時中位數秒: float | None
    每例中位數秒: float | None
    啟動探針中位數秒: float | None
    啟動探針平均秒: float | None


def 解析參數(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Raw argument list.

    Returns:
        Parsed args namespace.
    """

    parser = argparse.ArgumentParser(description="對比 Wenyan 多運行時的 benchmark。")
    parser.add_argument("--examples-dir", default="examples", help="範例目錄（預設：examples）。")
    parser.add_argument("--rounds", type=int, default=1, help="完整資料集輪次（預設：1）。")
    parser.add_argument(
        "--startup-rounds",
        type=int,
        default=5,
        help="啟動探針輪次（預設：5）。",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="每次單檔執行逾時秒數（預設：90）。",
    )
    parser.add_argument(
        "--include-skipped",
        action="store_true",
        help="包含預設略過的圖形範例。",
    )
    parser.add_argument(
        "--include-free-threading",
        action="store_true",
        help="包含 tox 的 py313t/py314t。",
    )
    parser.add_argument(
        "--no-install-missing-python",
        action="store_true",
        help="缺少解譯器時不自動 `uv python install`。",
    )
    parser.add_argument(
        "--cli-js",
        default="",
        help="@wenyan/cli 的 index.min.js 絕對路徑（預設：自動準備快取）。",
    )
    parser.add_argument(
        "--cli-cache-dir",
        default=str(Path(tempfile.gettempdir()) / "wenyan-cli-bench"),
        help="自動準備 @wenyan/cli 的 npm cache 目錄。",
    )
    parser.add_argument(
        "--no-cli-setup",
        action="store_true",
        help="不自動 npm 安裝 @wenyan/cli；若缺少則略過 JS 類目。",
    )
    parser.add_argument(
        "--result-json",
        default="benchmark/results/examples_runtime_benchmark.json",
        help="JSON 結果檔路徑。",
    )
    parser.add_argument(
        "--result-csv",
        default="benchmark/results/examples_runtime_benchmark.csv",
        help="CSV 結果檔路徑。",
    )
    parser.add_argument(
        "--result-md",
        default="benchmark/results/examples_runtime_benchmark.md",
        help="Markdown 結果檔路徑。",
    )
    return parser.parse_args(list(argv))


def 取摘要(text: str, limit: int = 180) -> str:
    """Return compact one-line summary.

    Args:
        text: Source text.
        limit: Max returned length.

    Returns:
        Compacted and truncated text.
    """

    單行 = " ".join(text.split())
    if len(單行) <= limit:
        return 單行
    return f"{單行[:limit]}..."


def 執行命令取輸出(
    命令: Sequence[str],
    工作目錄: Path,
    逾時秒數: float,
) -> tuple[int | None, str, str, str | None]:
    """Run a command and capture outputs.

    Args:
        命令: Full command list.
        工作目錄: Process cwd.
        逾時秒數: Timeout in seconds.

    Returns:
        (returncode, stdout, stderr, error_string)
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
    except subprocess.TimeoutExpired:
        return None, "", "", f"timeout>{逾時秒數:.1f}s"
    except OSError as 例外:
        return None, "", "", f"{type(例外).__name__}: {例外}"

    return 進程.returncode, 進程.stdout, 進程.stderr, None


def 測時執行(
    命令: Sequence[str],
    工作目錄: Path,
    逾時秒數: float,
) -> tuple[bool, float | None, str | None]:
    """Run one command with timing and concise failure reason.

    Args:
        命令: Full command list.
        工作目錄: Process cwd.
        逾時秒數: Timeout in seconds.

    Returns:
        (success, elapsed_seconds, reason_if_failed)
    """

    起 = time.perf_counter()
    try:
        進程 = subprocess.run(
            list(命令),
            cwd=str(工作目錄),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=逾時秒數,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, None, f"timeout>{逾時秒數:.1f}s"
    except OSError as 例外:
        return False, None, f"{type(例外).__name__}: {例外}"

    秒數 = time.perf_counter() - 起
    if 進程.returncode == 0:
        return True, 秒數, None

    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(命令, 工作目錄, 逾時秒數)
    if 例外:
        return False, 秒數, 例外
    摘要 = 取摘要(標準誤 or 標準出)
    return False, 秒數, f"rc={返回碼}, {摘要}"


def 取命令第一行(
    命令: Sequence[str],
    工作目錄: Path,
    逾時秒數: float = 20.0,
) -> str:
    """Run command and return first non-empty line from stdout/stderr.

    Args:
        命令: Full command list.
        工作目錄: Process cwd.
        逾時秒數: Timeout seconds.

    Returns:
        First non-empty line or fallback marker.
    """

    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(命令, 工作目錄, 逾時秒數)
    if 例外:
        return f"{例外}"
    if 返回碼 not in (0, None):
        合併 = (標準誤 or 標準出).strip()
        if 合併:
            return f"rc={返回碼} {取摘要(合併)}"
        return f"rc={返回碼}"

    for 行 in (標準出 + "\n" + 標準誤).splitlines():
        行 = 行.strip()
        if 行:
            return 行
    return "unknown"


def 取tox環境名單(工作目錄: Path) -> tuple[list[str], str | None]:
    """Load default tox env list.

    Args:
        工作目錄: Repository root.

    Returns:
        (env_names, error_message)
    """

    命令 = ["uv", "run", "tox", "-q", "list", "-d", "--no-desc"]
    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(命令, 工作目錄, 30.0)
    if 例外:
        return [], f"tox list failed: {例外}"
    if 返回碼 != 0:
        return [], f"tox list rc={返回碼}: {取摘要(標準誤 or 標準出)}"
    名單 = [行.strip() for 行 in 標準出.splitlines() if 行.strip()]
    return 名單, None


def 篩Python環境(全部環境: Sequence[str], 包含自由執行緒: bool) -> list[str]:
    """Select python env factors for benchmark.

    Args:
        全部環境: Full tox env list.
        包含自由執行緒: Whether to include py313t/py314t.

    Returns:
        Ordered env list.
    """

    目標 = set(預設CPython環境)
    if 包含自由執行緒:
        目標.update(預設自由執行緒環境)

    結果: list[str] = []
    for 名稱 in 預設CPython環境:
        if 名稱 in 全部環境:
            結果.append(名稱)
    if 包含自由執行緒:
        for 名稱 in 預設自由執行緒環境:
            if 名稱 in 全部環境:
                結果.append(名稱)

    for 名稱 in 全部環境:
        if 名稱.startswith("pypy") and 名稱 not in 結果:
            結果.append(名稱)
        if 名稱.startswith("graalpy") and 名稱 not in 結果:
            結果.append(名稱)

    return [名稱 for 名稱 in 結果 if 名稱 in 目標 or 名稱.startswith(("pypy", "graalpy"))]


def tox環境轉uv請求(環境名: str) -> str | None:
    """Map tox env factor to `uv python` request string.

    Args:
        環境名: tox env name, e.g. `py312`, `pypy310`, `graalpy312`.

    Returns:
        uv request string or None when unmapped.
    """

    def _轉版本片段(片段: str) -> str | None:
        if not 片段:
            return None
        自由執行緒 = 片段.endswith("t")
        純數 = 片段[:-1] if 自由執行緒 else 片段
        if not 純數.startswith("3") or len(純數) < 2:
            return None
        次版 = 純數[1:]
        if not 次版.isdigit():
            return None
        尾綴 = "t" if 自由執行緒 else ""
        return f"3.{int(次版)}{尾綴}"

    if 環境名.startswith("pypy"):
        版本 = _轉版本片段(環境名[4:])
        return None if 版本 is None else f"pypy{版本}"
    if 環境名.startswith("graalpy"):
        版本 = _轉版本片段(環境名[7:])
        return None if 版本 is None else f"graalpy{版本}"
    if 環境名.startswith("py"):
        版本 = _轉版本片段(環境名[2:])
        return None if 版本 is None else f"cpython{版本}"
    return None


def 準備uv解譯器(
    工作目錄: Path,
    環境名: str,
    允許安裝: bool,
) -> tuple[Path | None, str | None]:
    """Resolve interpreter path via `uv python find` by tox env factor.

    Args:
        工作目錄: Repository root.
        環境名: tox env name.
        允許安裝: Whether missing interpreters may be installed via uv.

    Returns:
        (python_path, unavailable_reason)
    """

    請求 = tox環境轉uv請求(環境名)
    if 請求 is None:
        return None, f"unsupported tox env: {環境名}"

    查找命令 = ["uv", "python", "find", "--managed-python", 請求]
    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(查找命令, 工作目錄, 30.0)
    if 例外 is None and 返回碼 == 0:
        路徑字串 = 標準出.strip().splitlines()
        if 路徑字串:
            路徑 = Path(路徑字串[0]).expanduser()
            if 路徑.exists():
                return 路徑, None

    if not 允許安裝:
        訊息 = 取摘要(標準誤 or 標準出) or "interpreter not found"
        return None, f"{請求} unavailable: {訊息}"

    安裝命令 = ["uv", "python", "install", 請求]
    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(安裝命令, 工作目錄, 1200.0)
    if 例外:
        return None, f"uv install failed: {例外}"
    if 返回碼 != 0:
        return None, f"uv install rc={返回碼}: {取摘要(標準誤 or 標準出)}"

    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(查找命令, 工作目錄, 30.0)
    if 例外:
        return None, f"uv find after install failed: {例外}"
    if 返回碼 != 0:
        return None, f"uv find rc={返回碼}: {取摘要(標準誤 or 標準出)}"
    路徑字串 = 標準出.strip().splitlines()
    if not 路徑字串:
        return None, f"{請求} installed but path not found"
    路徑 = Path(路徑字串[0]).expanduser()
    if not 路徑.exists():
        return None, f"path does not exist: {路徑}"
    return 路徑, None


def 確保CLI腳本(
    工作目錄: Path,
    cli_js: str,
    cli_cache_dir: str,
    no_cli_setup: bool,
) -> tuple[Path | None, str | None]:
    """Resolve local @wenyan/cli JS entry file.

    Args:
        工作目錄: Repository root.
        cli_js: Optional explicit JS path.
        cli_cache_dir: Cache dir for npm install.
        no_cli_setup: If true, skip auto-setup.

    Returns:
        (cli_js_path, unavailable_reason)
    """

    if cli_js:
        路徑 = Path(cli_js).expanduser().resolve()
        if 路徑.exists():
            return 路徑, None
        return None, f"cli js not found: {路徑}"

    目標 = (
        Path(cli_cache_dir).expanduser().resolve() / "node_modules" / "@wenyan" / "cli" / "index.min.js"
    )
    if 目標.exists():
        return 目標, None

    if no_cli_setup:
        return None, "cli js missing and --no-cli-setup enabled"

    npm = shutil.which("npm")
    if not npm:
        return None, "npm not found"

    快取目錄 = Path(cli_cache_dir).expanduser().resolve()
    快取目錄.mkdir(parents=True, exist_ok=True)
    命令 = [npm, "install", "--silent", "--prefix", str(快取目錄), "@wenyan/cli"]
    返回碼, 標準出, 標準誤, 例外 = 執行命令取輸出(命令, 工作目錄, 600.0)
    if 例外:
        return None, f"npm install failed: {例外}"
    if 返回碼 != 0:
        return None, f"npm install rc={返回碼}: {取摘要(標準誤 or 標準出)}"
    if not 目標.exists():
        return None, f"cli js not produced: {目標}"
    return 目標, None


def 建立運行矩陣(
    工作目錄: Path,
    python環境: Sequence[str],
    cli腳本: Path | None,
    cli不可用原因: str | None,
    安裝缺失Python: bool,
) -> list[運行目標]:
    """Build all benchmark targets.

    Args:
        工作目錄: Repository root.
        python環境: Selected tox env names.
        cli腳本: Local CLI JS path if available.
        cli不可用原因: Reason when JS path unavailable.
        安裝缺失Python: Whether to auto-install missing interpreters via uv.

    Returns:
        Target runtime list.
    """

    目標: list[運行目標] = []

    for 環境名 in python環境:
        路徑, 原因 = 準備uv解譯器(
            工作目錄=工作目錄,
            環境名=環境名,
            允許安裝=安裝缺失Python,
        )
        if 路徑 is None:
            目標.append(
                運行目標(
                    名稱=f"wenyan.py[{環境名}]",
                    分組="wenyan.py",
                    引擎=環境名,
                    命令前綴=[],
                    版本="",
                    可用=False,
                    不可用原因=原因,
                )
            )
            目標.append(
                運行目標(
                    名稱=f"wywy[{環境名}]",
                    分組="wywy-python",
                    引擎=環境名,
                    命令前綴=[],
                    版本="",
                    可用=False,
                    不可用原因=原因,
                )
            )
            continue

        python版本 = 取命令第一行([str(路徑), "-V"], 工作目錄)
        目標.append(
            運行目標(
                名稱=f"wenyan.py[{環境名}]",
                分組="wenyan.py",
                引擎=環境名,
                命令前綴=[str(路徑), "wenyan.py", "--no-outputHanzi"],
                版本=python版本,
                可用=True,
                不可用原因=None,
            )
        )
        目標.append(
            運行目標(
                名稱=f"wywy[{環境名}]",
                分組="wywy-python",
                引擎=環境名,
                命令前綴=[str(路徑), "scripts/wywy_runner.py", "wenyan.wy"],
                版本=python版本,
                可用=True,
                不可用原因=None,
            )
        )

    js引擎 = ("node", "bun", "deno")
    for 引擎 in js引擎:
        路徑 = shutil.which(引擎)
        if not 路徑:
            原因 = f"{引擎} not found"
            目標.append(
                運行目標(
                    名稱=f"cli[{引擎}]",
                    分組="cli-js",
                    引擎=引擎,
                    命令前綴=[],
                    版本="",
                    可用=False,
                    不可用原因=原因,
                )
            )
            目標.append(
                運行目標(
                    名稱=f"wywy[{引擎}]",
                    分組="wywy-js",
                    引擎=引擎,
                    命令前綴=[],
                    版本="",
                    可用=False,
                    不可用原因=原因,
                )
            )
            continue

        if cli腳本 is None:
            原因 = cli不可用原因 or "cli js unavailable"
            目標.append(
                運行目標(
                    名稱=f"cli[{引擎}]",
                    分組="cli-js",
                    引擎=引擎,
                    命令前綴=[],
                    版本="",
                    可用=False,
                    不可用原因=原因,
                )
            )
            目標.append(
                運行目標(
                    名稱=f"wywy[{引擎}]",
                    分組="wywy-js",
                    引擎=引擎,
                    命令前綴=[],
                    版本="",
                    可用=False,
                    不可用原因=原因,
                )
            )
            continue

        if 引擎 == "deno":
            cli前綴 = [路徑, "run", "-A", str(cli腳本), "--no-outputHanzi"]
            cli版本 = 取命令第一行([路徑, "--version"], 工作目錄)
        else:
            cli前綴 = [路徑, str(cli腳本), "--no-outputHanzi"]
            cli版本 = 取命令第一行([路徑, "-v"], 工作目錄)

        目標.append(
            運行目標(
                名稱=f"cli[{引擎}]",
                分組="cli-js",
                引擎=引擎,
                命令前綴=cli前綴,
                版本=cli版本,
                可用=True,
                不可用原因=None,
            )
        )
        目標.append(
            運行目標(
                名稱=f"wywy[{引擎}]",
                分組="wywy-js",
                引擎=引擎,
                命令前綴=[*cli前綴, "wenyan.wy"],
                版本=cli版本,
                可用=True,
                不可用原因=None,
            )
        )

    return 目標


def 跑完整資料集(
    目標: 運行目標,
    範例列: Sequence[Path],
    輪次: int,
    工作目錄: Path,
    逾時秒數: float,
) -> tuple[list[float], str | None]:
    """Run full dataset rounds for one target.

    Args:
        目標: Runtime target.
        範例列: Example paths.
        輪次: Number of rounds.
        工作目錄: Repository root.
        逾時秒數: Timeout per file.

    Returns:
        (round_durations, failure_reason)
    """

    輪次秒數: list[float] = []
    for 輪 in range(輪次):
        print(f"  - round {輪 + 1}/{輪次}")
        開始 = time.perf_counter()
        for 索引, 範例 in enumerate(範例列, start=1):
            命令 = [*目標.命令前綴, str(範例)]
            成功, _, 原因 = 測時執行(命令, 工作目錄, 逾時秒數)
            if not 成功:
                return 輪次秒數, f"{範例.name}: {原因}"
            if 索引 % 14 == 0 or 索引 == len(範例列):
                print(f"    {索引}/{len(範例列)}")
        輪次秒數.append(time.perf_counter() - 開始)
    return 輪次秒數, None


def 跑啟動探針(
    目標: 運行目標,
    啟動範例: Path,
    輪次: int,
    工作目錄: Path,
    逾時秒數: float,
) -> tuple[list[float], str | None]:
    """Run startup probe on one tiny example.

    Args:
        目標: Runtime target.
        啟動範例: Probe example path.
        輪次: Probe iterations.
        工作目錄: Repository root.
        逾時秒數: Timeout per run.

    Returns:
        (probe_durations, failure_reason)
    """

    秒數列: list[float] = []
    for _ in range(輪次):
        命令 = [*目標.命令前綴, str(啟動範例)]
        成功, 秒數, 原因 = 測時執行(命令, 工作目錄, 逾時秒數)
        if not 成功:
            return 秒數列, f"startup probe failed: {原因}"
        if 秒數 is None:
            return 秒數列, "startup probe no timing"
        秒數列.append(秒數)
    return 秒數列, None


def 寫CSV(路徑: Path, 結果列: Sequence[運行結果]) -> None:
    """Write benchmark results as CSV.

    Args:
        路徑: Output path.
        結果列: Benchmark records.
    """

    路徑.parent.mkdir(parents=True, exist_ok=True)
    with 路徑.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "name",
                "group",
                "engine",
                "version",
                "status",
                "reason",
                "examples",
                "median_total_s",
                "median_per_example_s",
                "startup_median_s",
                "startup_mean_s",
                "round_seconds",
                "command_prefix",
            ]
        )
        for 記錄 in 結果列:
            writer.writerow(
                [
                    記錄.名稱,
                    記錄.分組,
                    記錄.引擎,
                    記錄.版本,
                    記錄.狀態,
                    記錄.原因 or "",
                    記錄.例數,
                    "" if 記錄.總耗時中位數秒 is None else f"{記錄.總耗時中位數秒:.6f}",
                    "" if 記錄.每例中位數秒 is None else f"{記錄.每例中位數秒:.6f}",
                    "" if 記錄.啟動探針中位數秒 is None else f"{記錄.啟動探針中位數秒:.6f}",
                    "" if 記錄.啟動探針平均秒 is None else f"{記錄.啟動探針平均秒:.6f}",
                    ";".join(f"{x:.6f}" for x in 記錄.輪次秒數),
                    " ".join(記錄.命令前綴),
                ]
            )


def 寫Markdown(
    路徑: Path,
    結果列: Sequence[運行結果],
    產生時間: str,
    例數: int,
    略過說明: Sequence[str],
    輪次: int,
    啟動輪次: int,
) -> None:
    """Write a Markdown summary with table + ASCII bars.

    Args:
        路徑: Output path.
        結果列: Benchmark records.
        產生時間: ISO timestamp.
        例數: Number of benchmark examples.
        略過說明: Skip notes.
        輪次: Dataset rounds.
        啟動輪次: Startup probe rounds.
    """

    路徑.parent.mkdir(parents=True, exist_ok=True)
    成功列 = [r for r in 結果列 if r.狀態 == "ok" and r.每例中位數秒 is not None]
    成功列.sort(key=lambda x: x.每例中位數秒 if x.每例中位數秒 is not None else float("inf"))
    全列 = sorted(
        結果列,
        key=lambda x: (
            0 if x.狀態 == "ok" else 1,
            x.每例中位數秒 if x.每例中位數秒 is not None else float("inf"),
            x.名稱,
        ),
    )

    行: list[str] = []
    行.append("# Wenyan Runtime Benchmark (examples/*.wy)")
    行.append("")
    行.append(f"- generated_at_utc: `{產生時間}`")
    行.append(f"- benchmark_examples: `{例數}`")
    行.append(f"- full_rounds: `{輪次}`")
    行.append(f"- startup_probe_rounds: `{啟動輪次}`")
    if 略過說明:
        行.append("- skipped_examples:")
        for 項 in 略過說明:
            行.append(f"  - {項}")
    行.append("")

    行.append("## Matrix")
    行.append("")
    行.append(
        "| runtime | group | version | status | total_median_s | per_example_median_s | startup_median_s | note |"
    )
    行.append("|---|---|---|---|---:|---:|---:|---|")
    for 記錄 in 全列:
        行.append(
            "| {名稱} | {分組} | {版本} | {狀態} | {總} | {每例} | {啟動} | {說明} |".format(
                名稱=記錄.名稱,
                分組=記錄.分組,
                版本=記錄.版本 or "-",
                狀態=記錄.狀態,
                總="-" if 記錄.總耗時中位數秒 is None else f"{記錄.總耗時中位數秒:.6f}",
                每例="-" if 記錄.每例中位數秒 is None else f"{記錄.每例中位數秒:.6f}",
                啟動="-" if 記錄.啟動探針中位數秒 is None else f"{記錄.啟動探針中位數秒:.6f}",
                說明=(記錄.原因 or "-").replace("|", "\\|"),
            )
        )

    行.append("")
    行.append("## Per-example Bar (lower is better)")
    行.append("")
    行.append("| runtime | per_example_median_s | bar |")
    行.append("|---|---:|---|")
    if 成功列:
        最大值 = max(r.每例中位數秒 or 0.0 for r in 成功列)
        for 記錄 in 成功列:
            值 = 記錄.每例中位數秒 or 0.0
            比例 = 值 / 最大值 if 最大值 > 0 else 0.0
            長度 = max(1, int(比例 * 36))
            條 = "#" * 長度
            行.append(f"| {記錄.名稱} | {值:.6f} | `{條}` |")
    else:
        行.append("| - | - | - |")

    路徑.write_text("\n".join(行) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Program entrypoint."""

    參數 = 解析參數(sys.argv[1:] if argv is None else argv)
    if 參數.rounds <= 0:
        print("[錯誤] --rounds 必須 >= 1")
        return 2
    if 參數.startup_rounds <= 0:
        print("[錯誤] --startup-rounds 必須 >= 1")
        return 2

    工作目錄 = Path(__file__).resolve().parents[1]
    範例目錄 = (工作目錄 / 參數.examples_dir).resolve()
    if not 範例目錄.exists():
        print(f"[錯誤] 範例目錄不存在：{範例目錄}")
        return 2

    全部範例 = sorted(範例目錄.glob("*.wy"))
    略過說明: list[str] = []
    範例列: list[Path] = []
    for 路徑 in 全部範例:
        原因 = 預設略過範例.get(路徑.name)
        if 原因 and not 參數.include_skipped:
            略過說明.append(f"{路徑.name}: {原因}")
            continue
        範例列.append(路徑.relative_to(工作目錄))
    if not 範例列:
        print("[錯誤] 無可用 benchmark 範例。")
        return 2

    啟動範例 = Path(參數.examples_dir) / "helloworld.wy"
    if not (工作目錄 / 啟動範例).exists():
        啟動範例 = 範例列[0]

    tox環境, tox錯誤 = 取tox環境名單(工作目錄)
    if tox錯誤:
        print(f"[錯誤] {tox錯誤}")
        return 2

    python環境 = 篩Python環境(tox環境, 參數.include_free_threading)
    cli腳本, cli不可用原因 = 確保CLI腳本(
        工作目錄=工作目錄,
        cli_js=參數.cli_js,
        cli_cache_dir=參數.cli_cache_dir,
        no_cli_setup=參數.no_cli_setup,
    )

    目標列 = 建立運行矩陣(
        工作目錄=工作目錄,
        python環境=python環境,
        cli腳本=cli腳本,
        cli不可用原因=cli不可用原因,
        安裝缺失Python=not 參數.no_install_missing_python,
    )

    print("=== Wenyan Runtime Benchmark Matrix ===")
    print(f"examples: {len(範例列)}")
    print(f"rounds: {參數.rounds}")
    print(f"startup_rounds: {參數.startup_rounds}")
    print(f"timeout_per_file: {參數.timeout}s")
    if 略過說明:
        print("skipped:")
        for 項 in 略過說明:
            print(f"  - {項}")
    print()

    結果列: list[運行結果] = []
    for 目標 in 目標列:
        print(f"[target] {目標.名稱}")
        if not 目標.可用:
            print(f"  - skip: {目標.不可用原因}")
            結果列.append(
                運行結果(
                    名稱=目標.名稱,
                    分組=目標.分組,
                    引擎=目標.引擎,
                    版本=目標.版本,
                    狀態="skipped",
                    原因=目標.不可用原因,
                    命令前綴=目標.命令前綴,
                    例數=len(範例列),
                    輪次秒數=[],
                    總耗時中位數秒=None,
                    每例中位數秒=None,
                    啟動探針中位數秒=None,
                    啟動探針平均秒=None,
                )
            )
            continue

        輪次秒數, 失敗原因 = 跑完整資料集(
            目標=目標,
            範例列=範例列,
            輪次=參數.rounds,
            工作目錄=工作目錄,
            逾時秒數=參數.timeout,
        )
        if 失敗原因:
            print(f"  - fail: {失敗原因}")
            結果列.append(
                運行結果(
                    名稱=目標.名稱,
                    分組=目標.分組,
                    引擎=目標.引擎,
                    版本=目標.版本,
                    狀態="failed",
                    原因=失敗原因,
                    命令前綴=目標.命令前綴,
                    例數=len(範例列),
                    輪次秒數=輪次秒數,
                    總耗時中位數秒=None,
                    每例中位數秒=None,
                    啟動探針中位數秒=None,
                    啟動探針平均秒=None,
                )
            )
            continue

        啟動秒數, 探針錯誤 = 跑啟動探針(
            目標=目標,
            啟動範例=啟動範例,
            輪次=參數.startup_rounds,
            工作目錄=工作目錄,
            逾時秒數=參數.timeout,
        )
        if 探針錯誤:
            print(f"  - fail: {探針錯誤}")
            結果列.append(
                運行結果(
                    名稱=目標.名稱,
                    分組=目標.分組,
                    引擎=目標.引擎,
                    版本=目標.版本,
                    狀態="failed",
                    原因=探針錯誤,
                    命令前綴=目標.命令前綴,
                    例數=len(範例列),
                    輪次秒數=輪次秒數,
                    總耗時中位數秒=None,
                    每例中位數秒=None,
                    啟動探針中位數秒=None,
                    啟動探針平均秒=None,
                )
            )
            continue

        總中位數 = statistics.median(輪次秒數)
        每例中位數 = 總中位數 / len(範例列)
        啟動中位數 = statistics.median(啟動秒數)
        啟動平均 = statistics.mean(啟動秒數)
        print(
            "  - ok: total_median={:.3f}s per_example={:.4f}s startup_median={:.4f}s".format(
                總中位數,
                每例中位數,
                啟動中位數,
            )
        )
        結果列.append(
            運行結果(
                名稱=目標.名稱,
                分組=目標.分組,
                引擎=目標.引擎,
                版本=目標.版本,
                狀態="ok",
                原因=None,
                命令前綴=目標.命令前綴,
                例數=len(範例列),
                輪次秒數=輪次秒數,
                總耗時中位數秒=總中位數,
                每例中位數秒=每例中位數,
                啟動探針中位數秒=啟動中位數,
                啟動探針平均秒=啟動平均,
            )
        )

    json路徑 = (工作目錄 / 參數.result_json).resolve()
    csv路徑 = (工作目錄 / 參數.result_csv).resolve()
    md路徑 = (工作目錄 / 參數.result_md).resolve()

    產生時間 = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    git提交 = 取命令第一行(["git", "rev-parse", "HEAD"], 工作目錄)

    資料 = {
        "meta": {
            "generated_at_utc": 產生時間,
            "cwd": str(工作目錄),
            "git_commit": git提交,
            "examples_dir": str(範例目錄),
            "examples_count": len(範例列),
            "rounds": 參數.rounds,
            "startup_rounds": 參數.startup_rounds,
            "timeout_per_file_seconds": 參數.timeout,
            "skip_notes": 略過說明,
            "cli_js": str(cli腳本) if cli腳本 else None,
            "cli_unavailable_reason": cli不可用原因,
            "python_envs_from_tox": python環境,
            "auto_install_missing_python": not 參數.no_install_missing_python,
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
        例數=len(範例列),
        略過說明=略過說明,
        輪次=參數.rounds,
        啟動輪次=參數.startup_rounds,
    )

    print("\n=== output ===")
    print(f"json: {json路徑}")
    print(f"csv : {csv路徑}")
    print(f"md  : {md路徑}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
