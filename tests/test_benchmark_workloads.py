import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _載入模組(檔名: str, 模組名: str):
    腳本路徑 = Path(__file__).resolve().parents[1] / "scripts" / 檔名
    規格 = importlib.util.spec_from_file_location(模組名, 腳本路徑)
    if 規格 is None or 規格.loader is None:
        raise RuntimeError(f"無法載入 {檔名}")
    模組 = importlib.util.module_from_spec(規格)
    sys.modules[規格.name] = 模組
    規格.loader.exec_module(模組)
    return 模組


測試模組 = _載入模組("benchmark_workloads.py", "benchmark_workloads")


class 工作負載清單測試(unittest.TestCase):
    def test_載入與選擇工作負載(self) -> None:
        清單文 = """
[workloads]
name\tpath\ttags\tsize\tsuites\tprofiles\tdescription
a\ta.wy\tsmoke\tS\tcompiler,runtime\tci,release\tA
b\tb.wy\tmacro\tM\tcompiler\trelease\tB

[group default]
a

[group ci]
a

[group release]
a
b
"""
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            清單路徑 = 根 / "MANIFEST"
            清單路徑.write_text(清單文, encoding="utf-8")
            (根 / "a.wy").write_text("吾有一數。曰一。書之。", encoding="utf-8")
            (根 / "b.wy").write_text("吾有一數。曰二。書之。", encoding="utf-8")

            工作負載表, 群組表 = 測試模組.載入工作負載清單(清單路徑)
            選中, 略過 = 測試模組.選擇工作負載(
                "release",
                工作負載表,
                群組表,
                套件="compiler",
                配置="release",
            )
            self.assertEqual([x.名稱 for x in 選中], ["a", "b"])
            self.assertEqual(略過, [])

            已載入 = 測試模組.載入工作負載源碼(根, 選中)
            self.assertEqual([x[0].名稱 for x in 已載入], ["a", "b"])
            self.assertIn("吾有一數", 已載入[0][2])


if __name__ == "__main__":
    unittest.main()
