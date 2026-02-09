import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import wenyan


class 命令列選項測試(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
