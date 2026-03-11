import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


def _載入模組():
    腳本路徑 = Path(__file__).resolve().parents[1] / "scripts" / "wyperformance.py"
    規格 = importlib.util.spec_from_file_location("wyperformance", 腳本路徑)
    if 規格 is None or 規格.loader is None:
        raise RuntimeError("無法載入 wyperformance.py")
    模組 = importlib.util.module_from_spec(規格)
    sys.modules[規格.name] = 模組
    規格.loader.exec_module(模組)
    return 模組


測試模組 = _載入模組()


class 文言效能套件測試(unittest.TestCase):
    def test_清單解析與選擇(self) -> None:
        清單文 = """
[benchmarks]
name\tcase\ttags\tdescription
a\tlexer\tdefault,core\tA
b\tparser\tcore\tB
c\tcompile_ast\t\tC

[group default]
a
b

[group core]
a
b

[group tiny]
+a
-b
"""
        with tempfile.TemporaryDirectory() as 目錄:
            清單路徑 = Path(目錄) / "MANIFEST"
            清單路徑.write_text(清單文, encoding="utf-8")

            基準表, 群組表 = 測試模組.載入清單(清單路徑)
            預設 = 測試模組.選擇基準("<default>", 基準表, 群組表)
            self.assertEqual([x.名稱 for x in 預設], ["a", "b"])

            核心減b = 測試模組.選擇基準("core,-b", 基準表, 群組表)
            self.assertEqual([x.名稱 for x in 核心減b], ["a"])

            純排除 = 測試模組.選擇基準("-c", 基準表, 群組表)
            self.assertEqual([x.名稱 for x in 純排除], ["a", "b"])

    def test_run可產生結果檔(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            目錄路徑 = Path(目錄)
            範例目錄 = 目錄路徑 / "examples"
            範例目錄.mkdir()
            (範例目錄 / "a.wy").write_text("吾有一數。曰一。書之。", encoding="utf-8")

            輸出檔 = 目錄路徑 / "res.json"
            退出碼 = 測試模組.main(
                [
                    "run",
                    "--examples-dir",
                    str(範例目錄),
                    "--benchmarks",
                    "lexer",
                    "--samples",
                    "1",
                    "--warmups",
                    "0",
                    "--min-time",
                    "0.0001",
                    "--max-loops",
                    "2",
                    "--output",
                    str(輸出檔),
                ]
            )
            self.assertEqual(退出碼, 0)
            self.assertTrue(輸出檔.exists())

            資料 = json.loads(輸出檔.read_text(encoding="utf-8"))
            self.assertEqual(資料["version"], "wyperf-1.0")
            self.assertEqual(len(資料["benchmarks"]), 1)
            self.assertEqual(資料["benchmarks"][0]["metadata"]["name"], "lexer")
            值列 = 資料["benchmarks"][0]["runs"][0]["values"]
            self.assertEqual(len(值列), 1)
            self.assertGreater(值列[0], 0.0)

    def test_compare可輸出表格與csv(self) -> None:
        基準資料 = {
            "version": "wyperf-1.0",
            "metadata": {"python_version": "3.12"},
            "benchmarks": [
                {
                    "metadata": {"name": "lexer"},
                    "runs": [{"values": [1.0, 1.1, 0.9], "warmups": [], "metadata": {}}],
                }
            ],
        }
        新資料 = {
            "version": "wyperf-1.0",
            "metadata": {"python_version": "3.12"},
            "benchmarks": [
                {
                    "metadata": {"name": "lexer"},
                    "runs": [{"values": [0.8, 0.85, 0.82], "warmups": [], "metadata": {}}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as 目錄:
            目錄路徑 = Path(目錄)
            基準檔 = 目錄路徑 / "base.json"
            新檔 = 目錄路徑 / "new.json"
            csv檔 = 目錄路徑 / "out.csv"
            基準檔.write_text(json.dumps(基準資料, ensure_ascii=False), encoding="utf-8")
            新檔.write_text(json.dumps(新資料, ensure_ascii=False), encoding="utf-8")

            標準出 = io.StringIO()
            with redirect_stdout(標準出):
                退出碼 = 測試模組.main(
                    [
                        "compare",
                        str(基準檔),
                        str(新檔),
                        "--output-style",
                        "table",
                        "--csv",
                        str(csv檔),
                    ]
                )
            self.assertEqual(退出碼, 0)
            輸出文 = 標準出.getvalue()
            self.assertIn("Benchmark", 輸出文)
            self.assertIn("lexer", 輸出文)
            self.assertTrue(csv檔.exists())
            csv文 = csv檔.read_text(encoding="utf-8")
            self.assertIn("benchmark,baseline_mean_s,changed_mean_s,ratio,significance", csv文)


if __name__ == "__main__":
    unittest.main()

