import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from wenyan import 主術


class 範例測試(unittest.TestCase):
    def test_範例(self):
        範例路徑列表 = sorted(Path("examples").glob("*.wy"))
        self.assertTrue(範例路徑列表, "未找到範例檔案")
        原命令列參數 = list(sys.argv)
        緩衝 = io.StringIO()
        try:
            for 路徑 in 範例路徑列表:
                with self.subTest(例=str(路徑)):
                    sys.argv = ["wenyan", "--tokens", str(路徑)]
                    # 主術目前會印出 tokens；避免測試輸出污染。
                    with redirect_stdout(緩衝):
                        主術()
        finally:
            sys.argv = 原命令列參數


if __name__ == "__main__":
    unittest.main()
