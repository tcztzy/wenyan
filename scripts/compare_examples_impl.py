#!/usr/bin/env python3
from __future__ import annotations

"""Compare example outputs between two Wenyan implementations.

Usage:
    uv run python scripts/compare_examples_impl.py

The default comparison uses:
- `npx @wenyan/cli --no-outputHanzi`
- `uv run python wenyan.py --no-outputHanzi`

Most examples are compared by `stdout` and return code. A few GUI-oriented
examples are skipped by default because they require browser/Tk runtime instead
of pure stdout execution.
"""

import argparse
import difflib
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


預設略過範例 = {
    "clock.wy": "依賴畫譜與計時器，需圖形/DOM 執行環境，不屬純 stdout 對照。",
    "tree.wy": "依賴畫譜圖形輸出，不屬純 stdout 對照。",
    "tree2.wy": "依賴畫譜圖形輸出，不屬純 stdout 對照。",
}


@dataclass
class 執行結果:
    """Single implementation execution result.

    Attributes:
        命令: Full shell-split command actually executed.
        返回碼: Process return code. None means failed to launch or timeout.
        標準出: Captured stdout.
        標準誤: Captured stderr.
        逾時: Whether timeout happened.
        例外: Launch/runtime exception message, if any.
    """

    命令: list[str]
    返回碼: int | None
    標準出: str
    標準誤: str
    逾時: bool
    例外: str | None


@dataclass
class 範例對照結果:
    """Comparison result for one example file."""

    路徑: Path
    甲: 執行結果
    乙: 執行結果
    一致: bool


def 解析命令列(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        argv: Raw argument list.

    Returns:
        Parsed argparse namespace.
    """

    parser = argparse.ArgumentParser(
        description="對照 examples/*.wy 在兩個 Wenyan 實作下的執行結果是否一致。"
    )
    parser.add_argument(
        "--examples-dir",
        default="examples",
        help="範例目錄（預設：examples）。",
    )
    parser.add_argument(
        "--impl-a-cmd",
        default="npx @wenyan/cli --no-outputHanzi",
        help="實作 A 命令前綴（預設：npx @wenyan/cli --no-outputHanzi）。",
    )
    parser.add_argument(
        "--impl-b-cmd",
        default="uv run python wenyan.py --no-outputHanzi",
        help="實作 B 命令前綴（預設：uv run python wenyan.py --no-outputHanzi）。",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=8.0,
        help="每次執行逾時秒數（預設：8）。",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=40,
        help="每個不一致案例最多顯示幾行 unified diff（預設：40）。",
    )
    parser.add_argument(
        "--include-skipped",
        action="store_true",
        help="包含預設略過範例一併執行。",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="有不一致（或執行失敗）時回傳非 0。",
    )
    return parser.parse_args(list(argv))


def 執行一例(
    命令前綴: Sequence[str],
    範例路徑: Path,
    工作目錄: Path,
    逾時秒數: float,
) -> 執行結果:
    """Execute one implementation on one example.

    Args:
        命令前綴: Command prefix (already split).
        範例路徑: Example file path.
        工作目錄: Working directory.
        逾時秒數: Timeout in seconds.

    Returns:
        Captured execution result.
    """

    命令 = [*命令前綴, str(範例路徑)]
    try:
        進程 = subprocess.run(
            命令,
            cwd=str(工作目錄),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=逾時秒數,
            check=False,
        )
    except subprocess.TimeoutExpired as 例外:
        return 執行結果(
            命令=命令,
            返回碼=None,
            標準出=例外.stdout or "",
            標準誤=例外.stderr or "",
            逾時=True,
            例外=f"TimeoutExpired: {逾時秒數}s",
        )
    except OSError as 例外:
        return 執行結果(
            命令=命令,
            返回碼=None,
            標準出="",
            標準誤="",
            逾時=False,
            例外=f"{type(例外).__name__}: {例外}",
        )

    return 執行結果(
        命令=命令,
        返回碼=進程.returncode,
        標準出=進程.stdout,
        標準誤=進程.stderr,
        逾時=False,
        例外=None,
    )


def 產生差異片段(甲出: str, 乙出: str, 最大行數: int) -> list[str]:
    """Generate capped unified diff lines for stdout differences."""

    差異 = list(
        difflib.unified_diff(
            甲出.splitlines(),
            乙出.splitlines(),
            fromfile="impl-a.stdout",
            tofile="impl-b.stdout",
            lineterm="",
        )
    )
    if len(差異) <= 最大行數:
        return 差異
    保留 = 差異[:最大行數]
    保留.append(f"...（尚有 {len(差異) - 最大行數} 行差異未顯示）")
    return 保留


def 摘要(text: str, limit: int = 160) -> str:
    """Return one-line compact summary for stderr/exception display."""

    單行 = " ".join(text.split())
    if len(單行) <= limit:
        return 單行
    return f"{單行[:limit]}..."


def main(argv: Sequence[str] | None = None) -> int:
    """Program entrypoint."""

    參數 = 解析命令列(sys.argv[1:] if argv is None else argv)

    工作目錄 = Path(__file__).resolve().parents[1]
    範例目錄 = (工作目錄 / 參數.examples_dir).resolve()
    if not 範例目錄.exists():
        print(f"[錯誤] 範例目錄不存在：{範例目錄}")
        return 2

    命令甲 = shlex.split(參數.impl_a_cmd)
    命令乙 = shlex.split(參數.impl_b_cmd)
    if not 命令甲 or not 命令乙:
        print("[錯誤] 實作命令不可為空。")
        return 2

    全部範例 = sorted(範例目錄.glob("*.wy"))
    略過清單: list[tuple[Path, str]] = []
    待測範例: list[Path] = []

    for 路徑 in 全部範例:
        原因 = 預設略過範例.get(路徑.name)
        if 原因 and not 參數.include_skipped:
            略過清單.append((路徑, 原因))
            continue
        待測範例.append(路徑)

    print("=== Wenyan 實作對照 ===")
    print(f"實作 A：{命令甲}")
    print(f"實作 B：{命令乙}")
    print(f"範例總數：{len(全部範例)}")
    print(f"預設略過：{len(略過清單)}")
    print(f"實際對照：{len(待測範例)}")
    print()

    if 略過清單:
        print("[略過範例]")
        for 路徑, 原因 in 略過清單:
            print(f"- {路徑.relative_to(工作目錄)}：{原因}")
        print()

    對照結果列: list[範例對照結果] = []
    for 路徑 in 待測範例:
        相對 = 路徑.relative_to(工作目錄)
        print(f"[執行] {相對}")
        甲結果 = 執行一例(命令甲, 相對, 工作目錄, 參數.timeout)
        乙結果 = 執行一例(命令乙, 相對, 工作目錄, 參數.timeout)
        一致 = (
            甲結果.返回碼 == 乙結果.返回碼
            and 甲結果.標準出 == 乙結果.標準出
            and 甲結果.例外 is None
            and 乙結果.例外 is None
        )
        對照結果列.append(
            範例對照結果(路徑=相對, 甲=甲結果, 乙=乙結果, 一致=一致)
        )

    一致列 = [項 for 項 in 對照結果列 if 項.一致]
    不一致列 = [項 for 項 in 對照結果列 if not 項.一致]

    print()
    print("[結果摘要]")
    print(f"- 一致：{len(一致列)}")
    print(f"- 不一致：{len(不一致列)}")

    if 不一致列:
        print()
        print("[不一致明細]")
        for 項 in 不一致列:
            print(f"- {項.路徑}")
            print(
                "  impl-a:",
                f"rc={項.甲.返回碼}",
                f"stdout={len(項.甲.標準出)} bytes",
                "timeout" if 項.甲.逾時 else "",
            )
            if 項.甲.例外:
                print(f"    例外：{摘要(項.甲.例外)}")
            if 項.甲.標準誤:
                print(f"    stderr：{摘要(項.甲.標準誤)}")

            print(
                "  impl-b:",
                f"rc={項.乙.返回碼}",
                f"stdout={len(項.乙.標準出)} bytes",
                "timeout" if 項.乙.逾時 else "",
            )
            if 項.乙.例外:
                print(f"    例外：{摘要(項.乙.例外)}")
            if 項.乙.標準誤:
                print(f"    stderr：{摘要(項.乙.標準誤)}")

            if 項.甲.標準出 != 項.乙.標準出:
                差異 = 產生差異片段(
                    項.甲.標準出, 項.乙.標準出, 參數.max_diff_lines
                )
                if 差異:
                    print("    stdout diff:")
                    for 行 in 差異:
                        print(f"      {行}")
            print()

    if 參數.fail_on_diff and 不一致列:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
