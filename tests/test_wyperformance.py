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
    腳本目錄 = str(腳本路徑.parent)
    if 腳本目錄 not in sys.path:
        sys.path.insert(0, 腳本目錄)
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
            工作負載檔 = 目錄路徑 / "a.wy"
            工作負載檔.write_text("吾有一數。曰一。書之。", encoding="utf-8")
            工作負載清單 = 目錄路徑 / "WORKLOADS"
            工作負載清單.write_text(
                "\n".join(
                    [
                        "[workloads]",
                        "name\tpath\ttags\tsize\tsuites\tprofiles\tdescription",
                        "tiny\ta.wy\tsmoke\tS\tcompiler,runtime\tci,release\tTiny",
                        "",
                        "[group default]",
                        "tiny",
                        "",
                        "[group ci]",
                        "tiny",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            輸出檔 = 目錄路徑 / "res.json"
            摘要檔 = 目錄路徑 / "res.md"
            退出碼 = 測試模組.main(
                [
                    "run",
                    "--workloads-manifest",
                    str(工作負載清單),
                    "--profile",
                    "ci",
                    "--benchmarks",
                    "lexer_only",
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
                    "--summary-md",
                    str(摘要檔),
                ]
            )
            self.assertEqual(退出碼, 0)
            self.assertTrue(輸出檔.exists())
            self.assertTrue(摘要檔.exists())

            資料 = json.loads(輸出檔.read_text(encoding="utf-8"))
            self.assertEqual(資料["version"], "wyperf-1.0")
            self.assertEqual(len(資料["benchmarks"]), 1)
            self.assertEqual(資料["benchmarks"][0]["metadata"]["name"], "lexer_only")
            self.assertEqual(資料["metadata"]["profile"], "ci")
            self.assertEqual(資料["metadata"]["workload_names"], ["tiny"])
            峰值 = 資料["benchmarks"][0]["metadata"]["peak_memory_bytes"]
            if 測試模組._可量測峰值記憶體():
                self.assertGreater(峰值, 0)
            else:
                self.assertIsNone(峰值)
            值列 = 資料["benchmarks"][0]["runs"][0]["values"]
            self.assertEqual(len(值列), 1)
            self.assertGreater(值列[0], 0.0)
            摘要文 = 摘要檔.read_text(encoding="utf-8")
            self.assertIn("Wenyan Benchmark Summary", 摘要文)
            self.assertIn("lexer_only", 摘要文)

    def test_無_tracemalloc_仍可跑基準(self) -> None:
        原追蹤 = 測試模組.tracemalloc
        測試模組.tracemalloc = None
        try:
            結果, 統計 = 測試模組._跑一基準(
                "noop",
                lambda 迭代: 迭代,
                測試模組.運行設定(樣本數=1, 熱身數=0, 最短秒數=0.0001, 最大迭代=2),
            )
        finally:
            測試模組.tracemalloc = 原追蹤

        self.assertIsNone(結果.metadata["peak_memory_bytes"])
        self.assertIn("median", 統計)

    def test_compare可輸出表格_csv_與_markdown(self) -> None:
        基準資料 = {
            "version": "wyperf-1.0",
            "metadata": {"python_version": "3.12", "profile": "release"},
            "benchmarks": [
                {
                    "metadata": {"name": "lexer"},
                    "runs": [
                        {"values": [1.0, 1.1, 0.9], "warmups": [], "metadata": {}}
                    ],
                },
                {
                    "metadata": {"name": "parser"},
                    "runs": [
                        {"values": [2.0, 2.1, 1.9], "warmups": [], "metadata": {}}
                    ],
                },
            ],
        }
        新資料 = {
            "version": "wyperf-1.0",
            "metadata": {"python_version": "3.12", "profile": "release.v2"},
            "benchmarks": [
                {
                    "metadata": {"name": "lexer"},
                    "runs": [
                        {"values": [0.8, 0.85, 0.82], "warmups": [], "metadata": {}}
                    ],
                },
                {
                    "metadata": {"name": "parser"},
                    "runs": [
                        {"values": [3.0, 3.1, 2.9], "warmups": [], "metadata": {}}
                    ],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as 目錄:
            目錄路徑 = Path(目錄)
            基準檔 = 目錄路徑 / "base.json"
            新檔 = 目錄路徑 / "new.json"
            csv檔 = 目錄路徑 / "out.csv"
            md檔 = 目錄路徑 / "out.md"
            基準檔.write_text(
                json.dumps(基準資料, ensure_ascii=False), encoding="utf-8"
            )
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
                        "--exclude",
                        "parser",
                        "--note",
                        "parser benchmark definition changed",
                        "--csv",
                        str(csv檔),
                        "--markdown",
                        str(md檔),
                    ]
                )
            self.assertEqual(退出碼, 0)
            輸出文 = 標準出.getvalue()
            self.assertIn("Benchmark", 輸出文)
            self.assertIn("lexer", 輸出文)
            self.assertTrue(csv檔.exists())
            csv文 = csv檔.read_text(encoding="utf-8")
            self.assertIn(
                "benchmark,baseline_mean_s,changed_mean_s,ratio,significance", csv文
            )
            self.assertTrue(md檔.exists())
            md文 = md檔.read_text(encoding="utf-8")
            self.assertIn("Wenyan Compiler Benchmark Compare", md文)
            self.assertIn("parser benchmark definition changed", md文)
            self.assertIn("excluded_benchmarks", md文)
            self.assertIn("`lexer`", md文)
            self.assertNotIn("`parser` |", md文)


if __name__ == "__main__":
    unittest.main()
