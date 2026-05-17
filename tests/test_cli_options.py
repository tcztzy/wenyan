import io
import marshal
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, cast

import wenyan


class 命令列選項測試(unittest.TestCase):
    def _執行文言(self, 源碼: str):
        模組樹 = wenyan.編譯為PythonAST(源碼, "<測試>")
        執行域 = {
            "__name__": "__main__",
            "__file__": "<測試>",
            "__wenyan_no_output_hanzi__": True,
        }
        程式碼 = compile(模組樹, "<測試>", "exec")
        標準出 = io.StringIO()
        with redirect_stdout(標準出):
            exec(程式碼, 執行域)
        return 標準出.getvalue(), 執行域

    def test_說明含不輸出漢字選項(self) -> None:
        標準出 = io.StringIO()
        標準誤 = io.StringIO()
        with redirect_stdout(標準出), redirect_stderr(標準誤):
            結果 = wenyan.主術(["--help"])
        self.assertEqual(結果, 0)
        self.assertIn("--no-outputHanzi", 標準出.getvalue())
        self.assertIn("--jit", 標準出.getvalue())
        self.assertIn("--jit=llvm", 標準出.getvalue())
        self.assertEqual(標準誤.getvalue(), "")

    def test_不輸出漢字選項可執行且輸出阿拉伯數(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            路徑 = Path(目錄) / "例.wy"
            路徑.write_text("吾有一數。曰一。書之。", encoding="utf-8")

            標準出 = io.StringIO()
            標準誤 = io.StringIO()
            with redirect_stdout(標準出), redirect_stderr(標準誤):
                結果 = wenyan.主術(["--no-outputHanzi", str(路徑)])

        self.assertEqual(結果, 0)
        self.assertEqual(標準出.getvalue(), "1\n")
        self.assertEqual(標準誤.getvalue(), "")

    def test_JIT選項可執行且輸出不變(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            路徑 = Path(目錄) / "例.wy"
            路徑.write_text("吾有一數。曰一。書之。", encoding="utf-8")

            標準出 = io.StringIO()
            標準誤 = io.StringIO()
            with redirect_stdout(標準出), redirect_stderr(標準誤):
                結果 = wenyan.主術(["--jit", "--no-outputHanzi", str(路徑)])

        self.assertEqual(結果, 0)
        self.assertEqual(標準出.getvalue(), "1\n")
        self.assertEqual(標準誤.getvalue(), "")

    def test_LLVM_JIT選項可執行且缺後端時靜默回退(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            路徑 = Path(目錄) / "例.wy"
            路徑.write_text("吾有一數。曰一。書之。", encoding="utf-8")

            標準出 = io.StringIO()
            標準誤 = io.StringIO()
            with redirect_stdout(標準出), redirect_stderr(標準誤):
                結果 = wenyan.主術(["--jit=llvm", "--no-outputHanzi", str(路徑)])

        self.assertEqual(結果, 0)
        self.assertEqual(標準出.getvalue(), "1\n")
        self.assertEqual(標準誤.getvalue(), "")

    def test_JIT未知後端回傳用法錯誤(self) -> None:
        標準出 = io.StringIO()
        標準誤 = io.StringIO()
        with redirect_stdout(標準出), redirect_stderr(標準誤):
            結果 = wenyan.主術(["--jit=bad", "例.wy"])

        self.assertEqual(結果, 2)
        self.assertEqual(標準出.getvalue(), "")
        self.assertIn("未知 JIT 後端：bad", 標準誤.getvalue())

    def test_JIT編譯快取重用無匯入程式碼(self) -> None:
        wenyan._文言程式碼快取.clear()
        源碼 = "吾有一數。曰一。書之。"
        首次 = wenyan._編譯文言程式碼(源碼, "<快取>", 使用快取=True)
        再次 = wenyan._編譯文言程式碼(源碼, "<快取>", 使用快取=True)
        self.assertIs(首次, 再次)

        LLVM首次 = wenyan._編譯文言程式碼(源碼, "<快取>", 使用快取=True, JIT後端="llvm")
        LLVM再次 = wenyan._編譯文言程式碼(源碼, "<快取>", 使用快取=True, JIT後端="llvm")
        self.assertIs(LLVM首次, LLVM再次)
        self.assertIsNot(首次, LLVM首次)

        匯入源碼 = "吾嘗觀『math』之書。"
        匯入首次 = wenyan._編譯文言程式碼(匯入源碼, "<匯入>", 使用快取=True)
        匯入再次 = wenyan._編譯文言程式碼(匯入源碼, "<匯入>", 使用快取=True)
        self.assertIsNot(匯入首次, 匯入再次)

    def test_JIT磁碟快取可跨記憶體快取重用(self) -> None:
        源碼 = "吾有一數。曰一。書之。"
        with tempfile.TemporaryDirectory() as 目錄:
            路徑 = Path(目錄) / "例.wy"
            路徑.write_text(源碼, encoding="utf-8")
            快取路徑 = wenyan._取JIT快取路徑(str(路徑))
            LLVM快取路徑 = wenyan._取JIT快取路徑(str(路徑), "llvm")
            self.assertIsNotNone(快取路徑)
            self.assertIsNotNone(LLVM快取路徑)
            self.assertNotEqual(快取路徑, LLVM快取路徑)

            wenyan._文言程式碼快取.clear()
            wenyan._編譯文言程式碼(源碼, str(路徑), 使用快取=True)
            assert 快取路徑 is not None
            self.assertTrue(Path(快取路徑).is_file())

            def 不可編譯(_內容: str, _文檔名: str = "<言>") -> object:
                raise AssertionError("不應重新編譯")

            原編譯 = wenyan.編譯為PythonAST
            wenyan._文言程式碼快取.clear()
            模組 = cast(Any, wenyan)
            模組.編譯為PythonAST = 不可編譯
            try:
                程式碼 = wenyan._編譯文言程式碼(源碼, str(路徑), 使用快取=True)
            finally:
                模組.編譯為PythonAST = 原編譯

            標準出 = io.StringIO()
            with redirect_stdout(標準出):
                exec(
                    程式碼,
                    {
                        "__name__": "__main__",
                        "__file__": str(路徑),
                        "__wenyan_no_output_hanzi__": True,
                        "__wenyan_jit_enabled__": True,
                    },
                )
            self.assertEqual(標準出.getvalue(), "1\n")

    def test_JIT磁碟快取壞檔與失效記錄會回退(self) -> None:
        源碼 = "吾有一數。曰一。書之。"
        程式碼 = compile("pass", "<快取>", "exec")
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            self.assertIsNone(wenyan._取JIT快取路徑("<stdin>"))
            self.assertIsNone(wenyan._取JIT快取路徑(str(根 / "無.wy")))
            self.assertIsNone(wenyan._讀JIT磁碟快取(str(根 / "無.wyc"), 源碼, True))

            壞檔 = 根 / "壞.wyc"
            壞檔.write_bytes(b"bad")
            self.assertIsNone(wenyan._讀JIT磁碟快取(str(壞檔), 源碼, True))

            非記錄 = 根 / "非記錄.wyc"
            with 非記錄.open("wb") as 檔案:
                marshal.dump("不是記錄", 檔案)
            self.assertIsNone(wenyan._讀JIT磁碟快取(str(非記錄), 源碼, True))

            後端不符 = 根 / "後端不符.wyc"
            with 後端不符.open("wb") as 檔案:
                marshal.dump(
                    (wenyan.版本號, sys.version_info[:2], 源碼, True, "llvm", 程式碼),
                    檔案,
                )
            self.assertIsNone(wenyan._讀JIT磁碟快取(str(後端不符), 源碼, True))

            失效 = 根 / "失效.wyc"
            with 失效.open("wb") as 檔案:
                marshal.dump(
                    (wenyan.版本號, sys.version_info[:2], "別文", True, 程式碼), 檔案
                )
            self.assertIsNone(wenyan._讀JIT磁碟快取(str(失效), 源碼, True))

            阻塞 = 根 / "阻塞"
            阻塞.write_text("", encoding="utf-8")
            wenyan._寫JIT磁碟快取(str(阻塞 / "例.wyc"), 源碼, True, 程式碼)

    def test_不輸出漢字陣列格式與官版相容(self) -> None:
        充語 = "".join(
            f"充「甲」以{值}。"
            for 值 in [
                "十二",
                "六",
                "三",
                "十",
                "五",
                "十六",
                "八",
                "四",
                "二",
                "一",
                "一",
            ]
        )
        源碼 = f"吾有一列。名之曰「甲」。{充語}夫「甲」。書之。"
        實得, _ = self._執行文言(源碼)
        期望 = "\n".join(
            [
                "[",
                "  12, 6, 3, 10, 5,",
                "  16, 8, 4,  2, 1,",
                "   1",
                "]",
                "",
            ]
        )
        self.assertEqual(實得, 期望)

    def test_不輸出漢字長列遵循一百項截斷(self) -> None:
        長列充語 = "".join(f"充「甲」以{i}。" for i in range(1, 114))
        實得, _ = self._執行文言(f"吾有一列。名之曰「甲」。{長列充語}夫「甲」。書之。")
        self.assertIn("... 13 more items", 實得)

    def test_不輸出漢字陣列可含空無(self) -> None:
        實得, _ = self._執行文言(
            "吾有一元。名之曰「空」。吾有一列。名之曰「甲」。充「甲」以一。以「空」。以三。夫「甲」。書之。"
        )
        self.assertEqual(實得, "[ 1, None, 3 ]\n")

    def test_JSON_stringify整數浮點輸出整數(self) -> None:
        _, 執行域 = self._執行文言("")
        JSON類 = 執行域["JSON"]
        實得 = JSON類.stringify({"甲": 1.0, "乙": [2.0, 2.5]})
        self.assertEqual(實得, '{"甲":1,"乙":[2,2.5]}')


if __name__ == "__main__":
    unittest.main()
