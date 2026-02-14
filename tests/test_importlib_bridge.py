import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import wenyan


class 匯入橋接測試(unittest.TestCase):
    def _清模組(self, 根名: str) -> None:
        for 模組名 in list(sys.modules):
            if 模組名 == 根名 or 模組名.startswith(f"{根名}."):
                sys.modules.pop(模組名, None)

    def test_import_wy_模組(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            (根 / "甲.wy").write_text(
                "吾有一言。曰「「中」」。名之曰「乙」。",
                encoding="utf-8",
            )
            sys.path.insert(0, str(根))
            try:
                self._清模組("甲")
                模組 = importlib.import_module("甲")
                self.assertEqual(getattr(模組, "乙", None), "中")
            finally:
                self._清模組("甲")
                sys.path.remove(str(根))

    def test_import_wy_套件與子模組(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            套件目錄 = 根 / "套件"
            套件目錄.mkdir()
            (套件目錄 / "序.wy").write_text(
                "吾有一數。曰一。名之曰「甲」。",
                encoding="utf-8",
            )
            (套件目錄 / "子模組.wy").write_text(
                "吾有一數。曰二。名之曰「乙」。",
                encoding="utf-8",
            )
            sys.path.insert(0, str(根))
            try:
                self._清模組("套件")
                套件 = importlib.import_module("套件")
                子模組 = importlib.import_module("套件.子模組")
                self.assertEqual(getattr(套件, "甲", None), 1)
                self.assertEqual(getattr(子模組, "乙", None), 2)
            finally:
                self._清模組("套件")
                sys.path.remove(str(根))

    def test_from_import_可讀_wy_導出(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            (根 / "甲.wy").write_text(
                "吾有一言。曰「「橋」」。名之曰「乙」。",
                encoding="utf-8",
            )
            sys.path.insert(0, str(根))
            try:
                self._清模組("甲")
                作用域: dict[str, object] = {}
                exec("from 甲 import 乙", 作用域, 作用域)
                self.assertEqual(作用域.get("乙"), "橋")
            finally:
                self._清模組("甲")
                sys.path.remove(str(根))

    def test_顯式載入API(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            (根 / "甲.wy").write_text(
                "吾有一數。曰三。名之曰「乙」。",
                encoding="utf-8",
            )
            sys.path.insert(0, str(根))
            try:
                self._清模組("甲")
                模組 = wenyan.載入文言模組("甲")
                self.assertEqual(getattr(模組, "乙", None), 3)
                self.assertIs(模組, sys.modules.get("甲"))
            finally:
                self._清模組("甲")
                sys.path.remove(str(根))

    def test_匯入鉤子安裝卸載冪等(self) -> None:
        def _尋者數() -> int:
            return sum(
                1
                for 尋者 in sys.meta_path
                if isinstance(尋者, wenyan.文言模組尋者)
            )

        wenyan.卸載文言匯入鉤子()
        self.assertEqual(_尋者數(), 0)
        wenyan.安裝文言匯入鉤子()
        wenyan.安裝文言匯入鉤子()
        self.assertEqual(_尋者數(), 1)
        wenyan.卸載文言匯入鉤子()
        self.assertEqual(_尋者數(), 0)
        wenyan.安裝文言匯入鉤子()


if __name__ == "__main__":
    unittest.main()
