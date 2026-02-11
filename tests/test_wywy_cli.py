import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import wenyan


class 自舉命令列測試(unittest.TestCase):
    def test_自舉命令無參可執行主術(self) -> None:
        標準誤 = io.StringIO()
        with redirect_stderr(標準誤):
            結果 = wenyan.自舉主術([])

        self.assertEqual(結果, 0)
        self.assertEqual(標準誤.getvalue(), "")

    def test_自舉命令可解譯檔案(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            路徑 = Path(目錄) / "例.wy"
            路徑.write_text("吾有一數。曰二。名之曰「甲」。夫「甲」。書之。", encoding="utf-8")

            標準出 = io.StringIO()
            標準誤 = io.StringIO()
            with redirect_stdout(標準出), redirect_stderr(標準誤):
                結果 = wenyan.自舉主術([str(路徑)])

        self.assertEqual(結果, 0)
        self.assertEqual(標準出.getvalue(), "2\n")
        self.assertEqual(標準誤.getvalue(), "")

    def test_自舉命令可由標準入讀入(self) -> None:
        標準入 = io.StringIO("吾有一數。曰三。書之。")
        標準出 = io.StringIO()
        標準誤 = io.StringIO()
        with mock.patch("sys.stdin", 標準入), redirect_stdout(標準出), redirect_stderr(標準誤):
            結果 = wenyan.自舉主術(["-"])

        self.assertEqual(結果, 0)
        self.assertEqual(標準出.getvalue(), "3\n")
        self.assertEqual(標準誤.getvalue(), "")

    def test_自舉命令可執行自舉檔(self) -> None:
        路徑 = Path(__file__).resolve().parents[1] / "wenyan.wy"

        標準誤 = io.StringIO()
        with redirect_stderr(標準誤):
            結果 = wenyan.自舉主術([str(路徑)])

        self.assertEqual(結果, 0)
        self.assertEqual(標準誤.getvalue(), "")

    def test_自舉命令遇檔案錯誤會回傳一(self) -> None:
        標準誤 = io.StringIO()
        with redirect_stderr(標準誤):
            結果 = wenyan.自舉主術(["無此檔案.wy"])

        self.assertEqual(結果, 1)
        self.assertIn("無此檔案.wy", 標準誤.getvalue())

    def test_自舉命令可呈現自舉文法之禍(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            路徑 = Path(目錄) / "錯誤.wy"
            路徑.write_text("以施「甲」。", encoding="utf-8")

            標準誤 = io.StringIO()
            with redirect_stderr(標準誤):
                結果 = wenyan.自舉主術([str(路徑)])

        self.assertEqual(結果, 1)
        self.assertIn("文法之禍：以施需先取", 標準誤.getvalue())

    def test_自舉命令不回退宿主執行(self) -> None:
        路徑 = Path(__file__).resolve().parents[1] / "examples" / "factorial.wy"

        標準出 = io.StringIO()
        標準誤 = io.StringIO()
        with mock.patch.object(wenyan, "主術", side_effect=AssertionError("不應回退宿主")):
            with redirect_stdout(標準出), redirect_stderr(標準誤):
                結果 = wenyan.自舉主術([str(路徑)])

        self.assertEqual(結果, 0)
        self.assertEqual(標準出.getvalue(), "120\n")
        self.assertEqual(標準誤.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
