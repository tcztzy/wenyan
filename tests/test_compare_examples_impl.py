import importlib.util
import sys
import unittest
from pathlib import Path


def _載入對照腳本模組():
    腳本路徑 = Path(__file__).resolve().parents[1] / "scripts" / "compare_examples_impl.py"
    規格 = importlib.util.spec_from_file_location("compare_examples_impl", 腳本路徑)
    if 規格 is None or 規格.loader is None:
        raise RuntimeError("無法載入 compare_examples_impl.py")
    模組 = importlib.util.module_from_spec(規格)
    sys.modules[規格.name] = 模組
    規格.loader.exec_module(模組)
    return 模組


對照腳本 = _載入對照腳本模組()


class 對照腳本測試(unittest.TestCase):
    def test_import日期時間行可正規化(self) -> None:
        原輸出 = (
            "問天地好在。\n"
            "西元二〇二六年丙午年正月初一日甲子日子正二刻三分四十秒\n"
            "算經\n"
        )
        實得 = 對照腳本.正規化標準出(Path("examples/import.wy"), 原輸出)
        self.assertEqual(實得, "問天地好在。\n<日時>\n算經\n")

    def test_非import範例輸出不改動(self) -> None:
        原輸出 = "甲\n乙\n"
        實得 = 對照腳本.正規化標準出(Path("examples/fizzbuzz.wy"), 原輸出)
        self.assertEqual(實得, 原輸出)


if __name__ == "__main__":
    unittest.main()
