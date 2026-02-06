import io
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import wenyan


class 執行測試(unittest.TestCase):
    def _執行(self, 源碼: str, 文檔名: str = "<測試>") -> str:
        模組樹 = wenyan.編譯為PythonAST(源碼, 文檔名)
        程式碼 = compile(模組樹, 文檔名, "exec")
        緩衝 = io.StringIO()
        with redirect_stdout(緩衝):
            exec(程式碼, {"__name__": "__main__", "__file__": 文檔名})
        return 緩衝.getvalue()

    def _執行檔案(self, 路徑: Path) -> str:
        內容 = 路徑.read_text(encoding="utf-8")
        return self._執行(內容, str(路徑))

    def test_取以施(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
            \t加「甲」以「乙」。乃得矣。
            是謂「加」之術也。

            夫一。夫二。取二以施「加」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "3\n")

    def test_部分套用(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「相加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
            \t加「甲」以「乙」。乃得矣。
            是謂「相加」之術也。

            施「相加」於一。名之曰「加一」。施「加一」於二。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "3\n")

    def test_匯入與宏(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            (根 / "宏經.wy").write_text(
                textwrap.dedent(
                    """
                    或云「「書「甲」焉」」。
                    蓋謂「「吾有一言。曰「甲」。書之」」。
                    """
                ).strip(),
                encoding="utf-8",
            )
            主檔 = 根 / "主.wy"
            主檔.write_text(
                textwrap.dedent(
                    """
                    吾嘗觀「「宏經」」之書。

                    書「「嘿」」焉。
                    吾有一言。曰「「書「甲」焉」」。書之。
                    """
                ).strip(),
                encoding="utf-8",
            )
            輸出 = self._執行檔案(主檔)
            self.assertEqual(輸出, "嘿\n書「甲」焉\n")

    def test_試擲與捕(self) -> None:
        源碼 = textwrap.dedent(
            """
            姑妄行此。
            \t嗚呼。「「大禍」」之禍。
            如事不諧。
            \t豈「「小禍」」之禍歟。
            \t\t吾有一言。曰「「不中」」。書之。
            \t豈「「大禍」」之禍歟。名之曰「禍」。
            \t\t夫「禍」之「「名」」。書之。
            \t不知何禍歟。
            \t\t吾有一言。曰「「未知」」。書之。
            乃作罷。

            姑妄行此。
            \t嗚呼。「「空」」之禍。
            如事不諧乃作罷。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "大禍\n")

    def test_JSON與String(self) -> None:
        源碼 = textwrap.dedent(
            """
            施「JSON.stringify」於「「中」」。書之。
            施「String.fromCharCode」於六十五。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, '"中"\nA\n')

    def test_是也與作用域(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一數。曰一。名之曰「甲」。
            昔之「甲」者。今二是也。
            夫「甲」。書之。

            吾有一數。曰一。名之曰「乙」。
            吾有一術。名之曰「改」。欲行是術。乃行是術曰。
            \t昔之「乙」者。今三是矣。
            是謂「改」之術也。
            施「改」。噫。
            夫「乙」。書之。

            吾有一術。名之曰「外」。欲行是術。乃行是術曰。
            \t吾有一數。曰一。名之曰「丙」。
            \t吾有一術。名之曰「內」。欲行是術。乃行是術曰。
            \t\t昔之「丙」者。今四是矣。
            \t是謂「內」之術也。
            \t施「內」。
            \t乃得「丙」。
            是謂「外」之術也。
            施「外」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n3\n4\n")

    def test_Python表式名值(self) -> None:
        源碼 = textwrap.dedent(
            """
            施「(lambda x: x + 1)」於一。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n")


if __name__ == "__main__":
    unittest.main()
