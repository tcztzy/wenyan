import importlib.util
import tempfile
import unittest
from pathlib import Path

根目錄 = Path(__file__).resolve().parents[1]


def _載入模組():
    規格 = importlib.util.spec_from_file_location(
        "simplify_history", 根目錄 / "scripts" / "simplify_history.py"
    )
    assert 規格 is not None
    assert 規格.loader is not None
    模組 = importlib.util.module_from_spec(規格)
    規格.loader.exec_module(模組)
    return 模組


簡化歷程工具 = _載入模組()


class 簡化歷程工具測試(unittest.TestCase):
    def test_追加當前記錄會遞增輪次(self):
        with tempfile.TemporaryDirectory() as 暫目錄:
            根 = Path(暫目錄)
            CSV路徑 = 根 / "history.csv"
            源碼路徑 = 根 / "demo.py"
            源碼路徑.write_text("甲 = 1\nif 甲:\n    乙 = 2\n", encoding="utf-8")

            首筆 = 簡化歷程工具.追加當前記錄(
                CSV路徑,
                源碼路徑,
                說明="起點",
                Parser速度變化=1.01,
                CompileAST速度變化=0.99,
                幾何均值速度變化=1.00,
            )
            次筆 = 簡化歷程工具.追加當前記錄(CSV路徑, 源碼路徑)

            記錄列 = 簡化歷程工具.讀取歷程(CSV路徑)
            self.assertEqual("0", 首筆["輪次"])
            self.assertEqual("1", 次筆["輪次"])
            self.assertEqual(2, len(記錄列))
            self.assertEqual("起點", 記錄列[0]["說明"])
            self.assertEqual("第01輪", 記錄列[1]["標籤"])
            self.assertEqual("1.010000", 記錄列[0]["Parser速度變化"])
            self.assertEqual("0.990000", 記錄列[0]["CompileAST速度變化"])
            self.assertEqual("1.000000", 記錄列[0]["幾何均值速度變化"])

    def test_寫出折線圖會生成_svg(self):
        with tempfile.TemporaryDirectory() as 暫目錄:
            根 = Path(暫目錄)
            CSV路徑 = 根 / "history.csv"
            SVG路徑 = 根 / "history.svg"
            簡化歷程工具.寫入歷程(
                CSV路徑,
                [
                    {
                        "輪次": "0",
                        "標籤": "起點",
                        "行數": "100",
                        "位元組": "1000",
                        "詞元": "300",
                        "AST節點": "200",
                        "AST分支": "10",
                        "AST最大深度": "5",
                        "Parser速度變化": "1.000000",
                        "CompileAST速度變化": "1.000000",
                        "幾何均值速度變化": "1.000000",
                        "說明": "",
                    },
                    {
                        "輪次": "1",
                        "標籤": "第01輪",
                        "行數": "90",
                        "位元組": "900",
                        "詞元": "270",
                        "AST節點": "180",
                        "AST分支": "9",
                        "AST最大深度": "4",
                        "Parser速度變化": "1.080000",
                        "CompileAST速度變化": "1.030000",
                        "幾何均值速度變化": "1.050000",
                        "說明": "",
                    },
                ],
            )

            簡化歷程工具.寫出折線圖(CSV路徑, SVG路徑, "測試圖")

            內容 = SVG路徑.read_text(encoding="utf-8")
            self.assertIn("<svg", 內容)
            self.assertIn("測試圖", 內容)
            self.assertIn("行數", 內容)
            self.assertIn("位元組", 內容)
            self.assertIn("速度變化", 內容)
            self.assertIn("Parser速度變化", 內容)


if __name__ == "__main__":
    unittest.main()
