import io
from pathlib import Path
import unittest
from contextlib import redirect_stdout

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

    def test_自舉文法骨架可析最小句列(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("吾有一數。曰一。名之曰「甲」。書之。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["宣告句", "命名句", "書之句"])

        宣告句 = 句列[0]
        self.assertEqual(宣告句["量"], "一")
        self.assertEqual(宣告句["型"], "數")
        self.assertEqual(len(宣告句["初值列"]), 1)
        self.assertEqual(宣告句["初值列"][0]["類"], "數值")
        self.assertEqual(宣告句["初值列"][0]["文"], "一")

    def test_自舉文法骨架可析施句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("施「加」於一。於二。")
        句列 = 析句列(記號列)
        self.assertEqual(len(句列), 1)
        self.assertEqual(句列[0]["類"], "施句")
        self.assertEqual(句列[0]["術值"]["類"], "名值")
        self.assertEqual(句列[0]["術值"]["文"], "加")
        self.assertEqual([項["文"] for 項 in 句列[0]["參列"]], ["一", "二"])

    def test_自舉文法骨架可析夫與返回句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("夫「甲」。乃得其。乃得矣。乃歸空無。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["夫句", "返回句", "返回句", "返回句"])

        夫句 = 句列[0]
        self.assertEqual(夫句["值"]["類"], "名值")
        self.assertEqual(夫句["值"]["文"], "甲")

        乃得句 = 句列[1]
        self.assertEqual(乃得句["值"]["類"], "其值")
        self.assertEqual(乃得句["取棧"], False)
        self.assertEqual(乃得句["空無"], False)

        乃得矣句 = 句列[2]
        self.assertEqual(乃得矣句["取棧"], True)
        self.assertEqual(乃得矣句["空無"], False)

        歸空句 = 句列[3]
        self.assertEqual(歸空句["取棧"], False)
        self.assertEqual(歸空句["空無"], True)

    def test_自舉文法骨架可析之句與之長句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("夫「列」之一者。夫「列」之長者。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["之句", "之長句"])

        之句 = 句列[0]
        self.assertEqual(之句["容器"]["類"], "名值")
        self.assertEqual(之句["容器"]["文"], "列")
        self.assertEqual(之句["索引"]["類"], "數值")
        self.assertEqual(之句["索引"]["文"], "一")

        長句 = 句列[1]
        self.assertEqual(長句["容器"]["類"], "名值")
        self.assertEqual(長句["容器"]["文"], "列")

    def test_自舉文法骨架可析昔今句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("昔之「甲」者。今二是矣。昔之「乙」者。今不復存矣。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["昔今句", "昔今句"])

        設值句 = 句列[0]
        self.assertEqual(設值句["左名"], "甲")
        self.assertEqual(設值句["刪除"], False)
        self.assertEqual(設值句["左下標"], None)
        self.assertEqual(設值句["右值"]["類"], "數值")
        self.assertEqual(設值句["右值"]["文"], "二")
        self.assertEqual(設值句["右下標"], None)

        刪除句 = 句列[1]
        self.assertEqual(刪除句["左名"], "乙")
        self.assertEqual(刪除句["刪除"], True)
        self.assertEqual(刪除句["左下標"], None)
        self.assertEqual(刪除句["右下標"], None)

    def test_自舉文法骨架可析昔今句下標(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("昔之「甲」之一者。今「乙」之二是矣。昔之「丙」之三者。今不復存矣。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["昔今句", "昔今句"])

        設值句 = 句列[0]
        self.assertEqual(設值句["左名"], "甲")
        self.assertEqual(設值句["左下標"]["類"], "數值")
        self.assertEqual(設值句["左下標"]["文"], "一")
        self.assertEqual(設值句["右值"]["類"], "名值")
        self.assertEqual(設值句["右值"]["文"], "乙")
        self.assertEqual(設值句["右下標"]["類"], "數值")
        self.assertEqual(設值句["右下標"]["文"], "二")

        刪除句 = 句列[1]
        self.assertEqual(刪除句["左名"], "丙")
        self.assertEqual(刪除句["刪除"], True)
        self.assertEqual(刪除句["左下標"]["類"], "數值")
        self.assertEqual(刪除句["左下標"]["文"], "三")
        self.assertEqual(刪除句["右下標"], None)

    def test_自舉文法骨架可析昔今刪除是也(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("昔之「甲」之一者。今不復存矣是也。")
        句列 = 析句列(記號列)
        self.assertEqual(len(句列), 1)
        self.assertEqual(句列[0]["類"], "昔今句")
        self.assertEqual(句列[0]["刪除"], True)
        self.assertEqual(句列[0]["左名"], "甲")
        self.assertEqual(句列[0]["左下標"]["文"], "一")

    def test_自舉文法骨架可析若與恆為是(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("若一者。書之。若非。書之。云云。恆為是。乃止是遍。乃止。云云。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["若句", "恆為是句"])

        若句 = 句列[0]
        self.assertEqual(若句["比較"], "真")
        self.assertEqual(若句["左值"]["類"], "數值")
        self.assertEqual(若句["左值"]["文"], "一")
        self.assertEqual([句["類"] for 句 in 若句["然列"]], ["書之句"])
        self.assertEqual([句["類"] for 句 in 若句["否列"]], ["書之句"])

        恆句 = 句列[1]
        self.assertEqual([句["類"] for 句 in 恆句["體列"]], ["乃止是遍句", "乃止句"])

    def test_自舉文法骨架可析若其與或若(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("若其不然者。書之。或若一者。書之。若非。書之。云云。")
        句列 = 析句列(記號列)
        self.assertEqual(len(句列), 1)
        若句 = 句列[0]
        self.assertEqual(若句["類"], "若句")
        self.assertEqual(若句["比較"], "假")
        self.assertEqual([句["類"] for 句 in 若句["然列"]], ["書之句"])
        self.assertEqual(len(若句["否列"]), 1)
        self.assertEqual(若句["否列"][0]["類"], "若句")

    def test_自舉文法骨架可析若句至是謂(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞(
            "今有一術。名之曰「甲」。欲行是術。乃行是術曰。若一者。乃得一。是謂「甲」之術也。"
        )
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["術定義句"])
        術句 = 句列[0]
        self.assertEqual([句["類"] for 句 in 術句["體列"]], ["若句"])

    def test_自舉文法骨架可析為是遍與凡句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("為是一遍。乃止是遍。云云。凡「甲」中之「項」。乃止。云云。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["為是遍句", "凡句"])

        為句 = 句列[0]
        self.assertEqual(為句["次數"]["類"], "數值")
        self.assertEqual(為句["次數"]["文"], "一")
        self.assertEqual([句["類"] for 句 in 為句["體列"]], ["乃止是遍句"])

        凡句 = 句列[1]
        self.assertEqual(凡句["容器"]["類"], "名值")
        self.assertEqual(凡句["容器"]["文"], "甲")
        self.assertEqual(凡句["變名"], "項")
        self.assertEqual([句["類"] for 句 in 凡句["體列"]], ["乃止句"])

    def test_自舉文法骨架循環可遇乃得作終(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列一 = 分詞("恆為是。乃止。乃得一。")
        句列一 = 析句列(記號列一)
        self.assertEqual([句["類"] for 句 in 句列一], ["恆為是句", "返回句"])
        self.assertEqual([句["類"] for 句 in 句列一[0]["體列"]], ["乃止句"])

        記號列二 = 分詞("為是一遍。乃止是遍。乃得二。")
        句列二 = 析句列(記號列二)
        self.assertEqual([句["類"] for 句 in 句列二], ["為是遍句", "返回句"])
        self.assertEqual([句["類"] for 句 in 句列二[0]["體列"]], ["乃止是遍句"])

    def test_自舉文法骨架可析試句與擲句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列一 = 分詞("嗚呼。「「大禍」」之禍。曰「「訊」」。")
        句列一 = 析句列(記號列一)
        self.assertEqual([句["類"] for 句 in 句列一], ["擲句"])
        擲句 = 句列一[0]
        self.assertEqual(擲句["名"]["類"], "言值")
        self.assertEqual(擲句["名"]["文"], "大禍")
        self.assertEqual(擲句["訊"]["類"], "言值")
        self.assertEqual(擲句["訊"]["文"], "訊")

        記號列二 = 分詞(
            "姑妄行此。嗚呼。「「甲」」之禍。如事不諧。"
            "豈「「乙」」之禍歟。乃得一。"
            "不知何禍歟。名之曰「禍」。乃得二。"
            "乃作罷。"
        )
        句列二 = 析句列(記號列二)
        self.assertEqual([句["類"] for 句 in 句列二], ["試句"])
        試句 = 句列二[0]
        self.assertEqual([句["類"] for 句 in 試句["體列"]], ["擲句"])
        self.assertEqual(len(試句["捕捉列"]), 2)

        捕一 = 試句["捕捉列"][0]
        self.assertEqual(捕一["亦可"], False)
        self.assertEqual(捕一["錯名"]["類"], "言值")
        self.assertEqual(捕一["錯名"]["文"], "乙")
        self.assertIsNone(捕一["變數名"])
        self.assertEqual([句["類"] for 句 in 捕一["體列"]], ["返回句"])

        捕二 = 試句["捕捉列"][1]
        self.assertEqual(捕二["亦可"], True)
        self.assertIsNone(捕二["錯名"])
        self.assertEqual(捕二["變數名"], "禍")
        self.assertEqual([句["類"] for 句 in 捕二["體列"]], ["返回句"])

    def test_自舉最小執行器可行試擲與捕(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式一 = (
            "姑妄行此。"
            "嗚呼。「「大禍」」之禍。"
            "如事不諧。"
            "豈「「小禍」」之禍歟。乃得零。"
            "豈「「大禍」」之禍歟。名之曰「禍」。夫「禍」之「「名」」。乃得矣。"
            "不知何禍歟。乃得「「未知」」。"
            "乃作罷。"
        )
        self.assertEqual(解譯(程式一), "大禍")

        程式二 = (
            "姑妄行此。"
            "嗚呼。「「空」」之禍。"
            "如事不諧。"
            "豈「「非空」」之禍歟。乃得一。"
            "乃作罷。"
            "乃得二。"
        )
        self.assertEqual(解譯(程式二), 2)

        程式三 = (
            "姑妄行此。"
            "嗚呼。「「甲」」之禍。曰「「訊」」。"
            "如事不諧。"
            "不知何禍歟。名之曰「禍」。夫「禍」之「「訊」」。乃得矣。"
            "乃作罷。"
        )
        self.assertEqual(解譯(程式三), "訊")

    def test_自舉最小執行器可行若句(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        結果一 = 解譯(
            "若一者。吾有一數。曰三。名之曰「甲」。若非。吾有一數。曰四。名之曰「甲」。云云。乃得「甲」。"
        )
        self.assertEqual(結果一, 3)

        結果二 = 解譯(
            "若零者。吾有一數。曰三。名之曰「甲」。若非。吾有一數。曰四。名之曰「甲」。云云。乃得「甲」。"
        )
        self.assertEqual(結果二, 4)

        結果三 = 解譯("夫零。若其不然者。乃得一。若非。乃得二。云云。")
        self.assertEqual(結果三, 1)

        結果四 = 解譯(
            "吾有一數。曰二。名之曰「甲」。若「甲」等於一者。乃得一。或若「甲」等於二者。乃得二。若非。乃得三。云云。"
        )
        self.assertEqual(結果四, 2)

    def test_自舉最小執行器可行恆為是與乃止(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        結果 = 解譯("吾有一數。曰零。名之曰「甲」。恆為是。昔之「甲」者。今三是矣。乃止。云云。乃得「甲」。")
        self.assertEqual(結果, 3)

        結果二 = 解譯("恆為是。乃止。乃得一。")
        self.assertEqual(結果二, 1)

    def test_自舉最小執行器可行乃止是遍(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式 = (
            "吾有一數。曰一。名之曰「甲」。"
            "吾有一數。曰零。名之曰「乙」。"
            "恆為是。"
            "若「甲」小於二者。昔之「甲」者。今二是矣。乃止是遍。云云。"
            "昔之「乙」者。今九是矣。"
            "乃止。"
            "云云。"
            "乃得「乙」。"
        )
        結果 = 解譯(程式)
        self.assertEqual(結果, 9)

    def test_自舉最小執行器可行為是遍句(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式 = (
            "吾有一數。曰零。名之曰「和」。"
            "為是三遍。"
            "加「和」以一。"
            "昔之「和」者。今其是矣。"
            "云云。"
            "乃得「和」。"
        )
        self.assertEqual(解譯(程式), 3)

        結果二 = 解譯("為是一遍。乃止是遍。乃得二。")
        self.assertEqual(結果二, 2)

    def test_自舉最小執行器可行凡句(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式 = (
            "今有一術。名之曰「給列」。欲行是術。必先得其餘數。曰「餘」。乃行是術曰。"
            "乃得「餘」。"
            "是謂「給列」之術也。"
            "夫一。夫二。夫三。取其餘。以施「給列」。"
            "名之曰「列」。"
            "吾有一數。曰零。名之曰「和」。"
            "凡「列」中之「項」。"
            "加「和」以「項」。"
            "昔之「和」者。今其是矣。"
            "云云。"
            "乃得「和」。"
        )
        self.assertEqual(解譯(程式), 6)

    def test_自舉最小執行器可行之句與之長句(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式 = (
            "今有一術。名之曰「給列」。欲行是術。必先得其餘數。曰「餘」。乃行是術曰。"
            "乃得「餘」。"
            "是謂「給列」之術也。"
            "夫一。夫二。夫三。取其餘。以施「給列」。"
            "名之曰「列」。"
            "夫「列」之一。名之曰「首」。"
            "夫「列」之長。名之曰「長」。"
            "加「首」以「長」。"
            "乃得矣。"
        )
        self.assertEqual(解譯(程式), 4)

    def test_自舉文法骨架可析術定義句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get('分詞')
        析句列 = 作用域.get('析句列')
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞('今有一術。名之曰「恆三」。欲行是術。乃行是術曰。乃得三。是謂「恆三」之術也。')
        句列 = 析句列(記號列)
        self.assertEqual([句['類'] for 句 in 句列], ['術定義句'])

        術句 = 句列[0]
        self.assertEqual(術句['名'], '恆三')
        self.assertEqual(術句['參名列'], [])
        self.assertEqual([句['類'] for 句 in 術句['體列']], ['返回句'])

    def test_自舉文法骨架可析術參組其餘(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get('分詞')
        析句列 = 作用域.get('析句列')
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞(
            '今有一術。名之曰「收尾」。欲行是術。必先得一數。曰「首」。其餘數。曰「餘」。乃行是術曰。'
            '乃得「餘」。'
            '是謂「收尾」之術也。'
        )
        句列 = 析句列(記號列)
        術句 = 句列[0]
        self.assertEqual(術句['參名列'], ['首'])
        self.assertEqual(術句['其餘參名'], '餘')

    def test_自舉文法骨架術參組其餘須一名(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get('分詞')
        析句列 = 作用域.get('析句列')
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        with self.assertRaises(Exception) as 上下文:
            析句列(
                分詞(
                    '今有一術。名之曰「錯」。欲行是術。必先得其餘數。曰「甲」。曰「乙」。乃行是術曰。'
                    '乃得零。'
                    '是謂「錯」之術也。'
                )
            )
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, '名', None), '文法')
        self.assertEqual(getattr(禍, '訊', None), '其餘參數須一名')

    def test_自舉文法骨架術參組其餘須居末(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get('分詞')
        析句列 = 作用域.get('析句列')
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        with self.assertRaises(Exception) as 上下文:
            析句列(
                分詞(
                    '今有一術。名之曰「錯」。欲行是術。必先得其餘數。曰「餘」。一數。曰「甲」。乃行是術曰。'
                    '乃得零。'
                    '是謂「錯」之術也。'
                )
            )
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, '名', None), '文法')
        self.assertEqual(getattr(禍, '訊', None), '其餘參數須居末')

    def test_自舉最小執行器可行術定義零參(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        程式 = (
            '今有一術。名之曰「恆三」。欲行是術。乃行是術曰。'
            '乃得三。'
            '是謂「恆三」之術也。'
            '施「恆三」。'
            '乃得矣。'
        )
        結果 = 解譯(程式)
        self.assertEqual(結果, 3)

    def test_自舉最小執行器可行術定義與柯里化(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        程式一 = (
            '今有一術。名之曰「取乙」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。'
            '乃得「乙」。'
            '是謂「取乙」之術也。'
            '施「取乙」於五。於七。'
            '乃得矣。'
        )
        self.assertEqual(解譯(程式一), 7)

        程式二 = (
            '今有一術。名之曰「取乙」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。'
            '乃得「乙」。'
            '是謂「取乙」之術也。'
            '施「取乙」於一。'
            '名之曰「半」。'
            '施「半」於九。'
            '乃得矣。'
        )
        self.assertEqual(解譯(程式二), 9)

    def test_自舉文法骨架可析取與以施(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get('分詞')
        析句列 = 作用域.get('析句列')
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞('取二。以施「加」。')
        句列 = 析句列(記號列)
        self.assertEqual([句['類'] for 句 in 句列], ['取句', '以施句'])
        self.assertEqual(句列[0]['量'], '二')
        self.assertEqual(句列[1]['術值']['類'], '名值')
        self.assertEqual(句列[1]['術值']['文'], '加')

    def test_自舉文法骨架可析取其餘(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get('分詞')
        析句列 = 作用域.get('析句列')
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞('取其餘。以施「加」。')
        句列 = 析句列(記號列)
        self.assertEqual([句['類'] for 句 in 句列], ['取句', '以施句'])
        self.assertEqual(句列[0]['量'], '其餘')

    def test_自舉文法骨架可析算術與變句(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        記號列 = 分詞("加一以二。減三於十。乘二以三。除九以四所餘幾何。變陰。")
        句列 = 析句列(記號列)
        self.assertEqual([句["類"] for 句 in 句列], ["算術句", "算術句", "算術句", "算術句", "變句"])
        self.assertEqual(句列[0]["算"], "+")
        self.assertEqual(句列[1]["算"], "-")
        self.assertEqual(句列[1]["左值"]["文"], "十")
        self.assertEqual(句列[1]["右值"]["文"], "三")
        self.assertEqual(句列[2]["算"], "*")
        self.assertEqual(句列[3]["算"], "%")
        self.assertEqual(句列[4]["值"]["類"], "爻值")

    def test_自舉文法骨架算術句介詞非法(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        with self.assertRaises(Exception) as 上下文:
            析句列(分詞("加一之二。"))
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, "名", None), "文法")
        self.assertEqual(getattr(禍, "訊", None), "算術句介詞非法")

    def test_自舉最小執行器可行算術與變句(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        self.assertEqual(解譯("加一以二。乃得矣。"), 3)
        self.assertEqual(解譯("減三於十。乃得矣。"), 7)
        self.assertEqual(解譯("乘二以三。乃得矣。"), 6)
        self.assertEqual(解譯("除八以二。乃得矣。"), 4)
        self.assertEqual(解譯("除九以四所餘幾何。乃得矣。"), 1)
        self.assertIs(解譯("變陽。乃得矣。"), False)
        self.assertIs(解譯("變陰。乃得矣。"), True)

    def test_自舉最小執行器可行取與以施(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        程式 = (
            '今有一術。名之曰「取乙」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。'
            '乃得「乙」。'
            '是謂「取乙」之術也。'
            '夫五。'
            '夫七。'
            '取二。'
            '以施「取乙」。'
            '乃得矣。'
        )
        self.assertEqual(解譯(程式), 7)

    def test_自舉最小執行器可行取其餘與術參組其餘(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        程式 = (
            '今有一術。名之曰「收尾」。欲行是術。必先得一數。曰「首」。其餘數。曰「餘」。乃行是術曰。'
            '乃得「餘」。'
            '是謂「收尾」之術也。'
            '夫一。'
            '夫二。'
            '夫三。'
            '取其餘。'
            '以施「收尾」。'
            '乃得矣。'
        )
        self.assertEqual(解譯(程式), [2, 3])

    def test_自舉最小執行器變長術可部分套用(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        程式 = (
            '今有一術。名之曰「取餘」。欲行是術。必先得二數。曰「甲」曰「乙」。其餘數。曰「餘」。乃行是術曰。'
            '乃得「餘」。'
            '是謂「取餘」之術也。'
            '施「取餘」於一。'
            '名之曰「半」。'
            '施「半」於二。於三。於四。'
            '乃得矣。'
        )
        self.assertEqual(解譯(程式), [3, 4])

    def test_自舉最小執行器取後需以施(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        with self.assertRaises(Exception) as 上下文:
            解譯('夫一。取一。書之。')
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, '名', None), '文法')
        self.assertEqual(getattr(禍, '訊', None), '取後需以施')

    def test_自舉最小執行器取後未以施(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        with self.assertRaises(Exception) as 上下文:
            解譯('夫一。取一。')
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, '名', None), '文法')
        self.assertEqual(getattr(禍, '訊', None), '取後未以施')

    def test_自舉最小執行器以施需先取(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get('解譯')
        self.assertTrue(callable(解譯))

        with self.assertRaises(Exception) as 上下文:
            解譯('以施「甲」。')
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, '名', None), '文法')
        self.assertEqual(getattr(禍, '訊', None), '以施需先取')

    def test_自舉最小執行器可解譯並輸出(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        緩衝 = io.StringIO()
        with redirect_stdout(緩衝):
            結果 = 解譯("吾有一數。曰二。名之曰「甲」。夫「甲」。書之。")

        self.assertIsNone(結果)
        self.assertEqual(緩衝.getvalue(), "2\n")

    def test_自舉最小執行器可返回與昔今(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        結果一 = 解譯("吾有一數。曰一。名之曰「甲」。昔之「甲」者。今二是矣。乃得「甲」。")
        self.assertEqual(結果一, 2)

        結果二 = 解譯("夫三。乃得矣。")
        self.assertEqual(結果二, 3)

        結果三 = 解譯("吾有一數。曰一。名之曰「甲」。昔之「甲」者。今不復存矣。乃得「甲」。")
        self.assertIsNone(結果三)

    def test_自舉最小執行器可行昔今句下標(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式一 = (
            "今有一術。名之曰「給列」。欲行是術。必先得其餘數。曰「餘」。乃行是術曰。"
            "乃得「餘」。"
            "是謂「給列」之術也。"
            "夫零。夫零。取其餘。以施「給列」。"
            "名之曰「甲」。"
            "夫五。夫七。取其餘。以施「給列」。"
            "名之曰「乙」。"
            "昔之「甲」之二者。今「乙」之一是矣。"
            "夫「甲」之二。"
            "乃得矣。"
        )
        self.assertEqual(解譯(程式一), 5)

        程式二 = (
            "今有一術。名之曰「給列」。欲行是術。必先得其餘數。曰「餘」。乃行是術曰。"
            "乃得「餘」。"
            "是謂「給列」之術也。"
            "夫零。夫九。取其餘。以施「給列」。"
            "名之曰「甲」。"
            "昔之「甲」之二者。今不復存矣。"
            "夫「甲」之二。"
            "乃得矣。"
        )
        self.assertIsNone(解譯(程式二))

    def test_自舉最小執行器昔今刪除越界不擴列(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        程式 = (
            "今有一術。名之曰「給列」。欲行是術。必先得其餘數。曰「餘」。乃行是術曰。"
            "乃得「餘」。"
            "是謂「給列」之術也。"
            "夫一。夫二。取其餘。以施「給列」。"
            "名之曰「甲」。"
            "昔之「甲」之五者。今不復存矣。"
            "夫「甲」之長。"
            "乃得矣。"
        )
        self.assertEqual(解譯(程式), 2)

    def test_自舉最小執行器昔今句下標左值非法(self) -> None:
        作用域 = self._載入自舉作用域()
        解譯 = 作用域.get("解譯")
        self.assertTrue(callable(解譯))

        with self.assertRaises(Exception) as 上下文一:
            解譯("昔之「甲」之一者。今二是矣。")
        禍一 = 上下文一.exception
        self.assertEqual(getattr(禍一, "名", None), "文法")
        self.assertEqual(getattr(禍一, "訊", None), "昔今句左值非法")

        with self.assertRaises(Exception) as 上下文二:
            解譯("昔之「甲」之一者。今不復存矣。")
        禍二 = 上下文二.exception
        self.assertEqual(getattr(禍二, "名", None), "文法")
        self.assertEqual(getattr(禍二, "訊", None), "昔今句左值非法")

    def test_自舉文法骨架遇未支援句會報錯(self) -> None:
        作用域 = self._載入自舉作用域()
        分詞 = 作用域.get("分詞")
        析句列 = 作用域.get("析句列")
        self.assertTrue(callable(分詞))
        self.assertTrue(callable(析句列))

        with self.assertRaises(Exception) as 上下文:
            析句列(分詞("充「甲」以一。"))
        禍 = 上下文.exception
        self.assertEqual(getattr(禍, "名", None), "文法")
        self.assertEqual(getattr(禍, "訊", None), "暫不支援之句")

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
