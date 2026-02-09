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

    def test_關鍵詞採最長匹配(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        self.assertTrue(callable(分詞))

        記號列 = 分詞("乃得矣。乃止是遍。")
        文列 = [記["文"] for 記 in 記號列]
        類列 = [記["類"] for 記 in 記號列]

        self.assertEqual(文列, ["乃得矣", "乃止是遍"])
        self.assertEqual(類列, ["關鍵", "關鍵"])

    def test_分詞可區分言與名(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        self.assertTrue(callable(分詞))

        記號列 = 分詞("曰「「甲」」。名之曰「乙」。曰『丙』。")
        類列 = [記["類"] for 記 in 記號列]
        文列 = [記["文"] for 記 in 記號列]

        self.assertEqual(類列, ["關鍵", "言", "關鍵", "名", "關鍵", "言"])
        self.assertEqual(文列, ["曰", "甲", "名之曰", "乙", "曰", "丙"])

    def test_分詞言未盡拋文法之禍(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        self.assertTrue(callable(分詞))

        with self.assertRaises(Exception) as 上下文:
            分詞("曰「「甲」")
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, "名", None), "文法")
        self.assertEqual(getattr(禍, "訊", None), "言未尽")

    def test_分詞名未盡拋文法之禍(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        self.assertTrue(callable(分詞))

        with self.assertRaises(Exception) as 上下文:
            分詞("名之曰「甲")
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, "名", None), "文法")
        self.assertEqual(getattr(禍, "訊", None), "名未尽")

    def test_自舉檔不依賴宿主表達式(self) -> None:
        路徑 = Path(__file__).resolve().parents[1] / "wenyan.wy"
        內容 = 路徑.read_text(encoding="utf-8")
        禁詞列 = [
            "String.fromCharCode",
            ".startswith",
            "str.isspace",
            "(lambda",
            "__import__",
        ]
        for 禁詞 in 禁詞列:
            self.assertNotIn(禁詞, 內容)


if __name__ == "__main__":
    unittest.main()
