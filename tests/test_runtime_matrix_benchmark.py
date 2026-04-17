import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


def _載入模組():
    腳本路徑 = (
        Path(__file__).resolve().parents[1] / "scripts" / "benchmark_runtime_matrix.py"
    )
    腳本目錄 = str(腳本路徑.parent)
    if 腳本目錄 not in sys.path:
        sys.path.insert(0, 腳本目錄)
    規格 = importlib.util.spec_from_file_location("benchmark_runtime_matrix", 腳本路徑)
    if 規格 is None or 規格.loader is None:
        raise RuntimeError("無法載入 benchmark_runtime_matrix.py")
    模組 = importlib.util.module_from_spec(規格)
    sys.modules[規格.name] = 模組
    規格.loader.exec_module(模組)
    return 模組


測試模組 = _載入模組()


class 運行矩陣腳本測試(unittest.TestCase):
    def test_解析參數含_profile_與_workloads(self) -> None:
        參數 = 測試模組.解析參數(["run", "--profile", "ci", "--workloads", "ci"])
        self.assertEqual(參數.profile, "ci")
        self.assertEqual(參數.workloads, "ci")

    def test_tox環境轉uv請求(self) -> None:
        self.assertEqual(測試模組.tox環境轉uv請求("py312"), "cpython3.12")
        self.assertEqual(測試模組.tox環境轉uv請求("py313t"), "cpython3.13t")
        self.assertEqual(測試模組.tox環境轉uv請求("pypy310"), "pypy3.10")

    def test_compare可輸出_md(self) -> None:
        基準資料 = {
            "meta": {"profile": "ci"},
            "results": [
                {"名稱": "wenyan.py[py312]", "狀態": "ok", "每例中位數秒": 0.2},
                {"名稱": "wywy[py312]", "狀態": "ok", "每例中位數秒": 0.5},
            ],
        }
        新資料 = {
            "meta": {"profile": "release"},
            "results": [
                {"名稱": "wenyan.py[py312]", "狀態": "ok", "每例中位數秒": 0.25},
                {"名稱": "wywy[py312]", "狀態": "ok", "每例中位數秒": 0.4},
            ],
        }
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            基準檔 = 根 / "base.json"
            新檔 = 根 / "new.json"
            md檔 = 根 / "compare.md"
            基準檔.write_text(
                json.dumps(基準資料, ensure_ascii=False), encoding="utf-8"
            )
            新檔.write_text(json.dumps(新資料, ensure_ascii=False), encoding="utf-8")
            緩衝 = io.StringIO()
            with redirect_stdout(緩衝):
                退出碼 = 測試模組.main(
                    [
                        "compare",
                        str(基準檔),
                        str(新檔),
                        "--output-md",
                        str(md檔),
                        "--note",
                        "workload set changed",
                    ]
                )
            self.assertEqual(退出碼, 0)
            輸出 = 緩衝.getvalue()
            self.assertIn("Wenyan Runtime Matrix Compare", 輸出)
            self.assertIn("wenyan.py[py312]", 輸出)
            self.assertTrue(md檔.exists())
            md文 = md檔.read_text(encoding="utf-8")
            self.assertIn("workload set changed", md文)
            self.assertIn("baseline_workloads", md文)
            self.assertIn("`wenyan.py[py312]`", md文)


if __name__ == "__main__":
    unittest.main()
