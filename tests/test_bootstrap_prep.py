from pathlib import Path
import unittest

import wenyan


class 自舉準備測試(unittest.TestCase):
    def _載入自舉作用域(self) -> dict[str, object]:
        路徑 = Path(__file__).resolve().parents[1] / "wenyan.wy"
        內容 = 路徑.read_text(encoding="utf-8")

        模組樹 = wenyan.編譯為PythonAST(內容, str(路徑))
        程式碼 = compile(模組樹, str(路徑), "exec")

        作用域: dict[str, object] = {"__name__": "__main__", "__file__": str(路徑)}
        exec(程式碼, 作用域, 作用域)
        return 作用域

    def test_自舉骨架可編譯且可執行(self) -> None:
        作用域 = self._載入自舉作用域()
        主術 = 作用域.get("主術")
        self.assertTrue(callable(主術))
        self.assertEqual(主術(), 0)

    def test_自舉詞法骨架可分詞(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        self.assertTrue(callable(分詞))

        記號列 = 分詞("吾有一數。曰一。名之曰「甲」。施「主術」。書之。")
        self.assertIsInstance(記號列, list)
        self.assertGreaterEqual(len(記號列), 8)

        類列 = [記["類"] for 記 in 記號列]
        文列 = [記["文"] for 記 in 記號列]

        self.assertEqual(類列[0], "關鍵")
        self.assertEqual(文列[0], "吾有")
        self.assertIn("名之曰", 文列)
        self.assertIn("甲", 文列)
        self.assertIn("施", 文列)
        self.assertEqual(文列[-1], "書之")


if __name__ == "__main__":
    unittest.main()
