import contextlib
import io
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import check_line_coverage as 門禁


class 行覆蓋門禁測試(unittest.TestCase):
    def test_可執行行含巢狀函數(self) -> None:
        with tempfile.TemporaryDirectory() as 暫:
            源 = Path(暫) / "m.py"
            源.write_text(
                textwrap.dedent(
                    """
                    def f():
                        def g():
                            return 1
                        return g()
                    """
                ),
                encoding="utf-8",
            )

            行 = 門禁.取可執行行(源)

        self.assertIn(2, 行)
        self.assertIn(3, 行)
        self.assertIn(4, 行)
        self.assertIn(5, 行)

    def test_主術於全覆蓋時成功(self) -> None:
        with tempfile.TemporaryDirectory() as 暫:
            根 = Path(暫)
            源 = 根 / "mod.py"
            測試目錄 = 根 / "tests"
            測試目錄.mkdir()
            源.write_text(
                "def 加一(數):\n    return 數 + 1\n",
                encoding="utf-8",
            )
            (測試目錄 / "test_mod.py").write_text(
                "import unittest\n"
                "import mod\n\n"
                "class 測(unittest.TestCase):\n"
                "    def test_加一(self):\n"
                "        self.assertEqual(mod.加一(1), 2)\n",
                encoding="utf-8",
            )

            with self._臨時路徑(根), contextlib.redirect_stdout(io.StringIO()) as 出:
                狀態 = 門禁.主術(
                    [
                        "--source",
                        str(源),
                        "--tests",
                        str(測試目錄),
                        "--fail-under",
                        "100",
                        "--quiet",
                    ]
                )

        self.assertEqual(狀態, 0)
        self.assertIn("100.00%", 出.getvalue())

    def test_主術於覆蓋不足時失敗並列缺失(self) -> None:
        with tempfile.TemporaryDirectory() as 暫:
            根 = Path(暫)
            源 = 根 / "mod.py"
            測試目錄 = 根 / "tests"
            測試目錄.mkdir()
            源.write_text(
                "def 加一(數):\n    return 數 + 1\n\ndef 未測():\n    return 0\n",
                encoding="utf-8",
            )
            (測試目錄 / "test_mod.py").write_text(
                "import unittest\n"
                "import mod\n\n"
                "class 測(unittest.TestCase):\n"
                "    def test_加一(self):\n"
                "        self.assertEqual(mod.加一(1), 2)\n",
                encoding="utf-8",
            )

            with self._臨時路徑(根), contextlib.redirect_stdout(io.StringIO()) as 出:
                狀態 = 門禁.主術(
                    [
                        "--source",
                        str(源),
                        "--tests",
                        str(測試目錄),
                        "--fail-under",
                        "100",
                        "--quiet",
                    ]
                )

        self.assertEqual(狀態, 1)
        self.assertIn("missing:", 出.getvalue())

    @contextlib.contextmanager
    def _臨時路徑(self, 根: Path):
        import sys

        sys.path.insert(0, str(根))
        try:
            yield
        finally:
            sys.path.remove(str(根))
            sys.modules.pop("mod", None)
            sys.modules.pop("test_mod", None)


if __name__ == "__main__":
    unittest.main()
