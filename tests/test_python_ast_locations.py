import ast
import io
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import wenyan


def _需位置節點(節點: ast.AST) -> bool:
    return "lineno" in getattr(type(節點), "_attributes", ())


def _檢查AST位置完整(測試: unittest.TestCase, 模組樹: ast.Module) -> None:
    for 節點 in ast.walk(模組樹):
        if not _需位置節點(節點):
            continue
        for 欄 in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            值 = getattr(節點, 欄, None)
            測試.assertIsInstance(值, int, f"{type(節點).__name__}.{欄} 缺失")
        行 = int(getattr(節點, "lineno"))
        列 = int(getattr(節點, "col_offset"))
        末行 = int(getattr(節點, "end_lineno"))
        末列 = int(getattr(節點, "end_col_offset"))
        測試.assertGreaterEqual(行, 1)
        測試.assertGreaterEqual(列, 0)
        測試.assertGreaterEqual(末行, 行)
        測試.assertGreaterEqual(末列, 0)
        if 末行 == 行:
            測試.assertGreaterEqual(末列, 列)


class PythonAST位置測試(unittest.TestCase):
    def test_禁用_fix_missing_locations_仍可編譯(self) -> None:
        源碼 = "吾有一數。曰一。書之。"
        with patch("ast.fix_missing_locations", side_effect=AssertionError("forbidden")):
            模組樹 = wenyan.編譯為PythonAST(源碼, "<測試>")
            程式碼 = compile(模組樹, "<測試>", "exec")
        self.assertIsNotNone(程式碼)

    def test_AST_四字段完整_含複雜範例(self) -> None:
        範例路徑 = Path(__file__).resolve().parents[1] / "examples" / "divination.wy"
        源碼列 = [
            ("<簡>", "吾有一數。曰一。書之。"),
            (
                "<術>",
                "吾有一術。名之曰「加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。"
                "加「甲」以「乙」。乃得矣。"
                "是謂「加」之術也。"
                "施「加」於一。於二。書之。",
            ),
            (str(範例路徑), 範例路徑.read_text(encoding="utf-8")),
        ]
        for 文檔名, 源碼 in 源碼列:
            模組樹 = wenyan.編譯為PythonAST(源碼, 文檔名)
            _檢查AST位置完整(self, 模組樹)
            compile(模組樹, 文檔名, "exec")

    def test_輸出格式函錨定首句(self) -> None:
        源碼 = "\n\n吾有一數。曰一。書之。"
        模組樹 = wenyan.編譯為PythonAST(源碼, "<首句>")
        函列 = [
            節
            for 節 in 模組樹.body
            if isinstance(節, ast.FunctionDef) and 節.name == "__輸出格式值"
        ]
        self.assertEqual(len(函列), 1)
        self.assertEqual(函列[0].lineno, 3)

    def test_術呼叫輔助函錨定術定義句(self) -> None:
        源碼 = (
            "\n"
            + textwrap.dedent(
                """
                吾有一術。名之曰「加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乃得矣。
                是謂「加」之術也。
                施「加」於一。於二。書之。
                """
            ).strip()
        )
        模組樹 = wenyan.編譯為PythonAST(源碼, "<術錨>")
        術呼函列 = [
            節
            for 節 in 模組樹.body
            if isinstance(節, ast.FunctionDef) and 節.name.startswith("__調用")
        ]
        self.assertTrue(術呼函列)
        for 函 in 術呼函列:
            self.assertEqual(函.lineno, 2)

    def test_宏匯入_例外_名值Python表式_可編譯與執行(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            (根 / "宏經.wy").write_text(
                "或云「「書「甲」焉」」。蓋謂「「吾有一言。曰「甲」。書之」」。",
                encoding="utf-8",
            )
            主檔 = 根 / "主.wy"
            主檔.write_text(
                textwrap.dedent(
                    """
                    吾嘗觀「「宏經」」之書。
                    書「「甲」」焉。

                    姑妄行此。
                    嗚呼。「「大禍」」之禍。
                    如事不諧。
                    豈「「大禍」」之禍歟。名之曰「禍」。
                    夫「禍」之「「名」」。書之。
                    乃作罷。

                    夫len([1,2,3])。書之。
                    """
                ).strip(),
                encoding="utf-8",
            )
            模組樹 = wenyan.編譯為PythonAST(
                主檔.read_text(encoding="utf-8"),
                str(主檔),
            )
            _檢查AST位置完整(self, 模組樹)
            程式碼 = compile(模組樹, str(主檔), "exec")
            緩衝 = io.StringIO()
            with redirect_stdout(緩衝):
                exec(程式碼, {"__name__": "__main__", "__file__": str(主檔)})


if __name__ == "__main__":
    unittest.main()
