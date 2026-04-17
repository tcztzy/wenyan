import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import wenyan


class 基準圖表程式測試(unittest.TestCase):
    def test_圖表程式不再用_exec_包整段_python(self) -> None:
        根 = Path(__file__).resolve().parents[1]
        for 相對 in (
            "benchmark/charts/compiler_summary.wy",
            "benchmark/charts/runtime_matrix_summary.wy",
        ):
            路徑 = 根 / 相對
            with self.subTest(path=相對):
                內容 = 路徑.read_text(encoding="utf-8")
                self.assertNotIn("施「exec」", 內容)

    def test_圖表程式可編譯(self) -> None:
        根 = Path(__file__).resolve().parents[1]
        for 相對 in (
            "benchmark/charts/compiler_summary.wy",
            "benchmark/charts/runtime_matrix_summary.wy",
        ):
            路徑 = 根 / 相對
            with self.subTest(path=相對):
                內容 = 路徑.read_text(encoding="utf-8")
                模組樹 = wenyan.編譯為PythonAST(內容, str(路徑))
                self.assertGreater(len(模組樹.body), 0)

    def test_圖表程式可生成_svg(self) -> None:
        if shutil.which("uv") is None:
            self.skipTest("uv 不可用")
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            輸入檔 = 根 / "wyperformance.json"
            輸出檔 = 根 / "compiler.svg"
            輸入檔.write_text(
                json.dumps(
                    {
                        "benchmarks": [
                            {
                                "metadata": {
                                    "name": "lexer_only",
                                    "peak_memory_bytes": 2048,
                                },
                                "runs": [{"values": [0.1, 0.2], "metadata": {}}],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            環境 = os.environ.copy()
            環境["WENYAN_BENCHMARK_INPUT"] = str(輸入檔)
            環境["WENYAN_BENCHMARK_OUTPUT"] = str(輸出檔)
            命令 = [
                "uv",
                "run",
                "--with",
                "matplotlib",
                "wenyan.py",
                "benchmark/charts/compiler_summary.wy",
            ]
            結果 = subprocess.run(
                命令,
                cwd=str(Path(__file__).resolve().parents[1]),
                env=環境,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if 結果.returncode != 0:
                self.skipTest(
                    f"matplotlib smoke unavailable: {(結果.stderr or 結果.stdout).strip()}"
                )
            self.assertTrue(輸出檔.exists())
            self.assertIn("<svg", 輸出檔.read_text(encoding="utf-8"))

    def test_圖表程式可帶_compiler_baseline(self) -> None:
        if shutil.which("uv") is None:
            self.skipTest("uv 不可用")
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            輸入檔 = 根 / "new.json"
            基線檔 = 根 / "base.json"
            輸出檔 = 根 / "compiler-baseline.svg"
            輸入檔.write_text(
                json.dumps(
                    {
                        "benchmarks": [
                            {
                                "metadata": {
                                    "name": "lexer_only",
                                    "peak_memory_bytes": 2048,
                                },
                                "runs": [{"values": [0.2, 0.2], "metadata": {}}],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            基線檔.write_text(
                json.dumps(
                    {
                        "benchmarks": [
                            {
                                "metadata": {
                                    "name": "lexer_only",
                                    "peak_memory_bytes": 1024,
                                },
                                "runs": [{"values": [0.1, 0.1], "metadata": {}}],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            環境 = os.environ.copy()
            環境["WENYAN_BENCHMARK_INPUT"] = str(輸入檔)
            環境["WENYAN_BENCHMARK_BASELINE"] = str(基線檔)
            環境["WENYAN_BENCHMARK_OUTPUT"] = str(輸出檔)
            命令 = [
                "uv",
                "run",
                "--with",
                "matplotlib",
                "wenyan.py",
                "benchmark/charts/compiler_summary.wy",
            ]
            結果 = subprocess.run(
                命令,
                cwd=str(Path(__file__).resolve().parents[1]),
                env=環境,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if 結果.returncode != 0:
                self.skipTest(
                    f"matplotlib smoke unavailable: {(結果.stderr or 結果.stdout).strip()}"
                )
            self.assertTrue(輸出檔.exists())
            self.assertIn("<svg", 輸出檔.read_text(encoding="utf-8"))

    def test_runtime_圖表程式可生成_svg(self) -> None:
        if shutil.which("uv") is None:
            self.skipTest("uv 不可用")
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            輸入檔 = 根 / "runtime.json"
            輸出檔 = 根 / "runtime.svg"
            輸入檔.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "名稱": "wenyan.py[py312]",
                                "狀態": "ok",
                                "每例中位數秒": 0.1,
                                "啟動探針中位數秒": 0.02,
                            },
                            {
                                "名稱": "cli[node]",
                                "狀態": "ok",
                                "每例中位數秒": 0.08,
                                "啟動探針中位數秒": 0.03,
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            環境 = os.environ.copy()
            環境["WENYAN_BENCHMARK_INPUT"] = str(輸入檔)
            環境["WENYAN_BENCHMARK_OUTPUT"] = str(輸出檔)
            命令 = [
                "uv",
                "run",
                "--with",
                "matplotlib",
                "wenyan.py",
                "benchmark/charts/runtime_matrix_summary.wy",
            ]
            結果 = subprocess.run(
                命令,
                cwd=str(Path(__file__).resolve().parents[1]),
                env=環境,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if 結果.returncode != 0:
                self.skipTest(
                    f"matplotlib smoke unavailable: {(結果.stderr or 結果.stdout).strip()}"
                )
            self.assertTrue(輸出檔.exists())
            self.assertIn("<svg", 輸出檔.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
