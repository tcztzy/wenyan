"""以標準庫追蹤 unittest 行覆蓋。

此腳本只依賴標準庫，供 CI 或本機以 100% 行覆蓋門檻檢查指定 Python
源檔。它以 `sys.settrace` 收集目標檔案的 line event，避免對整個標準庫
產生逐行記錄。
"""

import argparse
import contextlib
import io
import sys
import types
import unittest
from pathlib import Path
from types import FrameType
from typing import NoReturn


class 覆蓋結果:
    """單檔行覆蓋結果。

    Args:
        路徑: 被測源檔。
        可執行行: 編譯後可產生 bytecode 的行號集合。
        已覆蓋行: 測試期間實際執行的行號集合。

    Attributes:
        路徑: 被測源檔。
        可執行行: 可計入覆蓋率的行。
        已覆蓋行: 已執行且屬於可執行行的行。
    """

    def __init__(self, 路徑: Path, 可執行行: set[int], 已覆蓋行: set[int]) -> None:
        self.路徑 = 路徑
        self.可執行行 = 可執行行
        self.已覆蓋行 = 已覆蓋行 & 可執行行

    @property
    def 缺失行(self) -> list[int]:
        """回傳未覆蓋行號。

        Returns:
            由小到大的未覆蓋行號。
        """

        return sorted(self.可執行行 - self.已覆蓋行)

    @property
    def 百分比(self) -> float:
        """回傳行覆蓋百分比。

        Returns:
            覆蓋百分比；空檔案視為 100%。
        """

        if not self.可執行行:
            return 100.0
        return len(self.已覆蓋行) * 100.0 / len(self.可執行行)


def 取可執行行(路徑: Path) -> set[int]:
    """以 Python code object 取可執行行。

    Args:
        路徑: Python 源檔路徑。

    Returns:
        源檔中會映射到 bytecode 的行號集合。

    Raises:
        OSError: 檔案不可讀時拋出。
        SyntaxError: 檔案不可編譯時拋出。
    """

    文字 = 路徑.read_text(encoding="utf-8")
    根碼 = compile(文字, str(路徑), "exec")
    待訪 = [根碼]
    行集: set[int] = set()
    while 待訪:
        碼 = 待訪.pop()
        for _始, _止, 行號 in 碼.co_lines():
            if 行號 is not None and 行號 > 0:
                行集.add(行號)
        待訪.extend(值 for 值 in 碼.co_consts if isinstance(值, types.CodeType))
    return 行集


def 追蹤測試(
    源列: list[Path], 測試目錄: str, 樣式: str, 靜默: bool
) -> tuple[bool, dict[Path, set[int]]]:
    """執行 unittest discovery 並收集目標源檔行號。

    Args:
        源列: 要追蹤的 Python 源檔。
        測試目錄: unittest discovery 起始目錄。
        樣式: 測試檔名樣式。
        靜默: 是否壓低 unittest 輸出。

    Returns:
        `(測試是否成功, 每檔已覆蓋行號)`。
    """

    命中: dict[Path, set[int]] = {路.resolve(): set() for 路 in 源列}
    目標 = {str(路) for 路 in 命中}

    def 追蹤(frame: FrameType, event: str, arg: object) -> object:
        檔名 = str(Path(frame.f_code.co_filename).resolve())
        if event == "call":
            if 檔名 in 目標:
                return 追蹤
            return None
        if event == "line":
            路徑 = Path(檔名).resolve()
            if str(路徑) in 目標:
                命中[路徑].add(frame.f_lineno)
            return 追蹤
        return 追蹤

    緩衝 = io.StringIO()
    輸出 = 緩衝 if 靜默 else sys.stderr
    sys.settrace(追蹤)
    try:
        套件 = unittest.TestLoader().discover(測試目錄, pattern=樣式)
        結果 = unittest.TextTestRunner(stream=輸出, verbosity=1).run(套件)
    finally:
        sys.settrace(None)
    if 靜默 and not 結果.wasSuccessful():
        sys.stderr.write(緩衝.getvalue())
    return 結果.wasSuccessful(), 命中


def 計算覆蓋(
    源列: list[Path], 測試目錄: str, 樣式: str, 靜默: bool
) -> tuple[bool, list[覆蓋結果]]:
    """執行測試並計算指定源檔覆蓋率。

    Args:
        源列: 要檢查的 Python 源檔。
        測試目錄: unittest discovery 起始目錄。
        樣式: 測試檔名樣式。
        靜默: 是否壓低 unittest 輸出。

    Returns:
        `(測試是否成功, 覆蓋結果列)`。
    """

    測試成功, 命中 = 追蹤測試(源列, 測試目錄, 樣式, 靜默)
    結果列 = [
        覆蓋結果(路.resolve(), 取可執行行(路.resolve()), 命中[路.resolve()])
        for 路 in 源列
    ]
    return 測試成功, 結果列


def 建參數解析器() -> argparse.ArgumentParser:
    """建立 CLI 參數解析器。

    Returns:
        可解析覆蓋門禁參數的 `ArgumentParser`。
    """

    解析器 = argparse.ArgumentParser(description="Run a stdlib line coverage gate.")
    解析器.add_argument(
        "--source",
        action="append",
        default=[],
        help="Python source file to require coverage for. Repeatable.",
    )
    解析器.add_argument(
        "--tests", default="tests", help="unittest discovery start directory."
    )
    解析器.add_argument(
        "--pattern", default="test_*.py", help="unittest discovery file pattern."
    )
    解析器.add_argument(
        "--fail-under",
        type=float,
        default=100.0,
        help="required per-file line coverage percent.",
    )
    解析器.add_argument(
        "--show-missing",
        type=int,
        default=25,
        help="maximum missing line numbers to print per file.",
    )
    解析器.add_argument(
        "--quiet", action="store_true", help="hide passing unittest output."
    )
    return 解析器


def 失敗(訊息: str) -> NoReturn:
    """印出錯誤並結束。

    Args:
        訊息: 給使用者看的錯誤訊息。

    Raises:
        SystemExit: 永遠以狀態碼 2 結束。
    """

    raise SystemExit(f"error: {訊息}")


def 主術(argv: list[str] | None = None) -> int:
    """執行覆蓋門禁。

    Args:
        argv: CLI 參數；`None` 時取 `sys.argv`。

    Returns:
        0 表示測試與覆蓋門檻皆通過；1 表示測試或覆蓋不足。
    """

    參數 = 建參數解析器().parse_args(argv)
    源列 = [Path(路).resolve() for 路 in 參數.source]
    if not 源列:
        失敗("至少指定一個 --source")
    for 路 in 源列:
        if not 路.is_file():
            失敗(f"source not found: {路}")

    測試成功, 結果列 = 計算覆蓋(源列, 參數.tests, 參數.pattern, 參數.quiet)
    覆蓋成功 = True
    for 結果 in 結果列:
        相對 = 結果.路徑
        with contextlib.suppress(ValueError):
            相對 = 結果.路徑.relative_to(Path.cwd())
        print(
            f"{相對}: {len(結果.已覆蓋行)}/{len(結果.可執行行)} "
            f"lines ({結果.百分比:.2f}%)"
        )
        if 結果.百分比 < 參數.fail_under:
            覆蓋成功 = False
            缺失 = 結果.缺失行[: 參數.show_missing]
            print(f"missing: {', '.join(str(行) for 行 in 缺失)}")
            if len(結果.缺失行) > len(缺失):
                print(f"... and {len(結果.缺失行) - len(缺失)} more")

    if not 測試成功:
        return 1
    return 0 if 覆蓋成功 else 1


if __name__ == "__main__":
    raise SystemExit(主術())
