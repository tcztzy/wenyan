import contextlib
import io
import re
import unittest
from pathlib import Path

import wenyan


def 取規則字面量(規格文: str, 規則名: str) -> list[str]:
    模式 = rf"^{規則名}\s*:([^;]+);"
    符合 = re.search(模式, 規格文, re.MULTILINE)
    if 符合 is None:
        raise AssertionError(f"missing grammar rule: {規則名}")
    return re.findall(r"'([^']+)'", 符合.group(1))


class 規格同步測試(unittest.TestCase):
    def test_wy_spec涵蓋宿主關鍵詞型別與數字字元(self) -> None:
        規格文 = Path("wy.spec").read_text(encoding="utf-8")
        全字面量 = set(re.findall(r"'([^']+)'", 規格文))

        self.assertLessEqual(set(wenyan.關鍵詞), 全字面量)
        self.assertEqual(set(wenyan.內建型別詞), set(取規則字面量(規格文, "TYPE")))

        數字字元 = (
            set(取規則字面量(規格文, "INT_NUM_KEYWORDS"))
            | set(取規則字面量(規格文, "FLOAT_NUM_KEYWORDS"))
            | {"負", "·", "又"}
        )
        self.assertEqual(wenyan.數值字符, 數字字元)
        self.assertNotIn("穣", 數字字元)
        self.assertIn("穰", 數字字元)

    def test_AST_SPEC記錄當前下標與其餘語義(self) -> None:
        文 = Path("AST_SPEC.md").read_text(encoding="utf-8")

        self.assertIn("取物(容器, 索引)", 文)
        self.assertIn("之其餘", 文)
        self.assertIn("其餘值()", 文)
        self.assertIn("獨立成值會報文法錯", 文)

    def test_AST_SPEC記錄條件式與JS專用策略(self) -> None:
        文 = Path("AST_SPEC.md").read_text(encoding="utf-8")

        self.assertIn("`&&` 優先於 `||`", 文)
        self.assertIn("lib/js/*.wy", 文)
        self.assertIn("lib/py/", 文)
        self.assertIn("JSON.stringify", 文)
        self.assertIn("String.fromCharCode", 文)

    def test_JS庫皆有Python等價層(self) -> None:
        js列 = sorted(Path("lib/js").glob("*.wy"))
        self.assertTrue(js列)
        for 路徑 in js列:
            with self.subTest(庫=路徑.name):
                self.assertTrue((Path("lib/py") / 路徑.name).is_file())

    def test_同步示例宿主與自舉雙端可跑(self) -> None:
        路徑 = Path("examples/syntax_sync.wy")

        宿主出 = io.StringIO()
        宿主誤 = io.StringIO()
        with contextlib.redirect_stdout(宿主出), contextlib.redirect_stderr(宿主誤):
            宿主碼 = wenyan.主術([str(路徑)])

        自舉出 = io.StringIO()
        自舉誤 = io.StringIO()
        with contextlib.redirect_stdout(自舉出), contextlib.redirect_stderr(自舉誤):
            自舉碼 = wenyan.自舉主術([str(路徑)])

        self.assertEqual(宿主碼, 0)
        self.assertEqual(自舉碼, 0)
        self.assertEqual(宿主誤.getvalue(), "")
        self.assertEqual(自舉誤.getvalue(), "")
        self.assertEqual(宿主出.getvalue(), "-1.2\n0.23\n1.23\n")
        self.assertEqual(自舉出.getvalue(), 宿主出.getvalue())


if __name__ == "__main__":
    unittest.main()
