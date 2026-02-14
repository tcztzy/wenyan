import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

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

    def test_不輸出漢字陣列格式與官版相容(self) -> None:
        充語 = "".join(f"充「甲」以{值}。" for 值 in ["十二", "六", "三", "十", "五", "十六", "八", "四", "二", "一", "一"])
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
        self.assertEqual(實得, "{\"甲\":1,\"乙\":[2,2.5]}")


if __name__ == "__main__":
    unittest.main()
