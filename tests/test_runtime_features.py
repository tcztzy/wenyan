import io
import os
import sys
import tempfile
import textwrap
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable, cast

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

    def test_取其餘與術參組其餘(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「收尾」。欲行是術。必先得一數。曰「首」。其餘數。曰「餘」。乃行是術曰。
            \t夫「首」。書之。
            \t夫「餘」之長。書之。
            \t夫「餘」之一。乃得矣。
            是謂「收尾」之術也。

            夫一。夫二。夫三。取其餘以施「收尾」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "1\n2\n2\n")

    def test_變長參數可部分套用(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「取餘長」。欲行是術。必先得二數。曰「甲」曰「乙」。其餘數。曰「餘」。乃行是術曰。
            \t夫「餘」之長。乃得矣。
            是謂「取餘長」之術也。

            施「取餘長」於一。名之曰「半」。
            施「半」於二。於三。於四。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n")

    def test_文言呼叫可傳尾參入變長術(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「取餘長」。欲行是術。必先得二數。曰「甲」曰「乙」。其餘數。曰「餘」。乃行是術曰。
            \t夫「餘」之長。乃得矣。
            是謂「取餘長」之術也。

            吾有一術。名之曰「返術」。欲行是術。乃行是術曰。
            \t乃得「取餘長」。
            是謂「返術」之術也。

            施「返術」於一。於二。於三。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "1\n")

    def test_術參組其餘須一名(self) -> None:
        源碼 = (
            "吾有一術。名之曰「錯」。欲行是術。必先得其餘數。曰「甲」。曰「乙」。乃行是術曰。"
            "乃得零。"
            "是謂「錯」之術也。"
        )
        with self.assertRaises(wenyan.文法之禍) as 上下文:
            self._執行(源碼)
        self.assertIn("其餘參數須一名", str(上下文.exception))

    def test_術參組其餘須居末(self) -> None:
        源碼 = (
            "吾有一術。名之曰「錯」。欲行是術。必先得其餘數。曰「餘」。一數。曰「甲」。乃行是術曰。"
            "乃得零。"
            "是謂「錯」之術也。"
        )
        with self.assertRaises(wenyan.文法之禍) as 上下文:
            self._執行(源碼)
        self.assertIn("其餘參數須居末", str(上下文.exception))

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

    def test_JIT熱術快路與部分套用(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「相加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乃得矣。
            是謂「相加」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jit>")
        程式碼 = compile(模組樹, "<jit>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jit>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_threshold__": 2,
        }
        exec(程式碼, 作用域)

        相加 = cast(Callable[..., Any], 作用域["相加"])
        self.assertEqual(相加(1, 2), 3)
        self.assertEqual(相加(3, 4), 7)
        self.assertEqual(相加(5, 6), 11)
        加一 = 相加(1)
        self.assertEqual(加一(2), 3)

        統計 = cast(dict[str, int], getattr(相加, "__文言JIT統計__"))
        self.assertEqual(統計["calls"], 5)
        self.assertEqual(統計["compiled"], 1)
        self.assertEqual(統計["hits"], 2)

    def test_JIT已知滿參術呼叫直呼本體(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「相加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乃得矣。
            是謂「相加」之術也。

            施「相加」於一。於二。書之。
            施「相加」於三。於四。書之。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jit直呼>", 啟用JIT直呼=True)
        程式碼 = compile(模組樹, "<jit直呼>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jit直呼>",
            "__wenyan_jit_enabled__": True,
        }
        緩衝 = io.StringIO()
        with redirect_stdout(緩衝):
            exec(程式碼, 作用域)

        相加 = 作用域["相加"]
        統計 = cast(dict[str, int], getattr(相加, "__文言JIT統計__"))
        self.assertEqual(緩衝.getvalue(), "3\n7\n")
        self.assertEqual(統計["calls"], 0)

    def test_LLVM_JIT產生整數算術中介碼並保留回退(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「相加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乃得矣。
            是謂「相加」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm>")
        程式碼 = compile(模組樹, "<jitllvm>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        相加 = cast(Callable[..., Any], 作用域["相加"])
        self.assertEqual(相加(1, 2), 3)
        self.assertEqual(相加(1 << 40, 1), (1 << 40) + 1)
        中介碼 = cast(str | None, getattr(相加, "__文言JITLLVM中介碼__"))
        統計 = cast(dict[str, int], getattr(相加, "__文言JIT統計__"))
        self.assertEqual(getattr(相加, "__文言JIT後端__"), "llvm")
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("define i64", 中介碼)
        self.assertIn("add i64", 中介碼)
        self.assertEqual(統計["compiled"], 1)

    def test_LLVM後端接受新版llvmlite自動初始化(self) -> None:
        假綁定 = cast(Any, types.ModuleType("llvmlite.binding"))
        呼叫列: list[str] = []

        def 初始化() -> None:
            呼叫列.append("initialize")
            raise RuntimeError("llvmlite.binding.initialize() is deprecated")

        def 初始化目標() -> None:
            呼叫列.append("target")

        def 初始化組譯器() -> None:
            呼叫列.append("asm")

        class 假目標機:
            pass

        class 假目標:
            def create_target_machine(self) -> 假目標機:
                呼叫列.append("machine")
                return 假目標機()

        class 假Target:
            @staticmethod
            def from_default_triple() -> 假目標:
                呼叫列.append("triple")
                return 假目標()

        假綁定.initialize = 初始化
        假綁定.initialize_native_target = 初始化目標
        假綁定.initialize_native_asmprinter = 初始化組譯器
        假綁定.Target = 假Target
        假套件 = types.ModuleType("llvmlite")
        原套件 = sys.modules.get("llvmlite")
        原綁定 = sys.modules.get("llvmlite.binding")
        sys.modules["llvmlite"] = 假套件
        sys.modules["llvmlite.binding"] = 假綁定
        域: dict[str, Any] = {"__wenyan_jit_backend__": "llvm"}
        try:
            exec(wenyan.內建序言源碼, 域, 域)
            llvm, ctypes = 域["__文言LLVM後端"]()
        finally:
            if 原套件 is None:
                sys.modules.pop("llvmlite", None)
            else:
                sys.modules["llvmlite"] = 原套件
            if 原綁定 is None:
                sys.modules.pop("llvmlite.binding", None)
            else:
                sys.modules["llvmlite.binding"] = 原綁定

        self.assertIs(llvm, 假綁定)
        self.assertIsNotNone(ctypes)
        self.assertEqual(呼叫列, ["initialize", "target", "asm", "triple", "machine"])

    def test_JIT直呼術遇重新賦值會失效(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「甲」。欲行是術。乃行是術曰。
                乃得一。
            是謂「甲」之術也。

            吾有一術。名之曰「乙」。欲行是術。乃行是術曰。
                乃得二。
            是謂「乙」之術也。

            昔之「甲」者。今「乙」是矣。
            施「甲」。書之。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jit失效>", 啟用JIT直呼=True)
        程式碼 = compile(模組樹, "<jit失效>", "exec")
        緩衝 = io.StringIO()
        with redirect_stdout(緩衝):
            exec(
                程式碼,
                {
                    "__name__": "__main__",
                    "__file__": "<jit失效>",
                    "__wenyan_jit_enabled__": True,
                },
            )
        self.assertEqual(緩衝.getvalue(), "2\n")

    def test_JIT直呼術回退分支保留語義(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「相加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乃得矣。
            是謂「相加」之術也。

            吾有一術。名之曰「收尾」。欲行是術。必先得二數。曰「甲」曰「乙」。其餘數。曰「餘」。乃行是術曰。
                夫「餘」之長。乃得矣。
            是謂「收尾」之術也。

            施「相加」於一。名之曰「加一」。施「加一」於二。書之。
            夫「相加」。施其於五。於六。書之。
            施「收尾」於一。名之曰「待收」。
            施「收尾」於一。於二。於三。書之。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jit回退>", 啟用JIT直呼=True)
        程式碼 = compile(模組樹, "<jit回退>", "exec")
        緩衝 = io.StringIO()
        with redirect_stdout(緩衝):
            exec(
                程式碼,
                {
                    "__name__": "__main__",
                    "__file__": "<jit回退>",
                    "__wenyan_jit_enabled__": True,
                },
            )
        self.assertEqual(緩衝.getvalue(), "3\n11\n1\n")

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

    def test_是也可終止內層若句(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「試」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
            \t有數零。名之曰「總」。
            \t若「甲」等於零者。乃得「總」。
            \t若非。
            \t\t若「甲」等於一者。昔之「甲」者。今二也。
            \t\t若非。昔之「甲」者。今三是也。
            \t\t加「總」以一。名之曰「乙」。
            \t\t昔之「總」者。今「乙」是也。
            \t\t乃得「總」。
            是謂「試」之術也。
            施「試」於一。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "1\n")

    def test_若其不然與或若(self) -> None:
        源碼 = textwrap.dedent(
            """
            夫零。
            若其不然者。夫一。書之。
            若非。夫二。書之。
            云云。

            吾有一數。曰二。名之曰「甲」。
            若「甲」等於一者。夫一。書之。
            或若「甲」等於二者。夫二。書之。
            若非。夫三。書之。
            云云。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "1\n2\n")

    def test_條件式後綴與邏輯優先序(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一列。名之曰「列」。
            充「列」以一以二。
            若「列」之長等於二中有陽乎零等於一中無陰乎零等於一者。
            \t夫「「長度與優先序」」。書之。
            若非。
            \t夫「「錯」」。書之。
            云云。

            若「列」之一等於一中無陰乎「列」之二等於二者。
            \t夫「「下標」」。書之。
            云云。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "長度與優先序\n下標\n")

    def test_循環可由乃得外收束(self) -> None:
        源碼 = textwrap.dedent(
            """
            今有一術。名之曰「甲」。欲行是術。乃行是術曰。
            	恆為是。
            		乃止。
            	乃得一。
            是謂「甲」之術也。

            今有一術。名之曰「乙」。欲行是術。乃行是術曰。
            	為是一遍。
            		乃止是遍。
            	乃得二。
            是謂「乙」之術也。

            施「甲」。書之。
            施「乙」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "1\n2\n")

    def test_昔今刪除無下標設空無(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一數。曰一。名之曰「甲」。
            昔之「甲」者。今不復存矣。
            夫「甲」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "None\n")

    def test_昔今刪除列元素會移除(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一列。名之曰「甲」。
            充「甲」以一以二以三。
            昔之「甲」之二者。今不復存矣。
            夫「甲」之長。書之。
            夫「甲」之二。書之。
            夫「甲」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n3\n[1, 3]\n")

    def test_昔今刪除列越界不擴列(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一列。名之曰「甲」。
            充「甲」以一以二。
            昔之「甲」之五者。今不復存矣。
            夫「甲」之長。書之。
            夫「甲」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n[1, 2]\n")

    def test_昔今刪除可用是也銜接若非(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一數。曰一。名之曰「甲」。
            若一者。
            	昔之「甲」者。今不復存矣是也。
            若非。
            	昔之「甲」者。今二是矣。
            云云。
            夫「甲」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "None\n")

    def test_是也可與云云終止並存(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一數。曰一。名之曰「甲」。
            若一者。
            	昔之「甲」者。今二是也。
            云云。
            夫「甲」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n")

    def test_其作下標只求值一次(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一列。名之曰「列」。
            充「列」以一以二。
            加一以一。
            夫「列」之其。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n")

    def test_曆法優先採用根庫實作(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾嘗觀「「曆法」」之書。方悟「言今之日時」之義。
            施「言今之日時」。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertTrue(輸出.startswith("西元"))

    def test_文言可匯入Python模組並方悟(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾嘗觀「「math」」之書。方悟「sin」之義。
            施「sin」於零。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "0.0\n")

    def test_文言匯入Python無方悟不污染名稱(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾嘗觀「「math」」之書。
            施「sin」於零。書之。
            """
        ).strip()
        with self.assertRaises(NameError):
            self._執行(源碼)

    def test_文言匯入先取_wy_後取Python(self) -> None:
        with tempfile.TemporaryDirectory() as 目錄:
            根 = Path(目錄)
            (根 / "math.wy").write_text(
                textwrap.dedent(
                    """
                    吾有一術。名之曰「sin」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                    \t乃得四十二。
                    是謂「sin」之術也。
                    """
                ).strip(),
                encoding="utf-8",
            )
            主檔 = 根 / "主.wy"
            源碼 = textwrap.dedent(
                """
                吾嘗觀「「math」」之書。方悟「sin」之義。
                施「sin」於零。書之。
                """
            ).strip()
            輸出 = self._執行(源碼, str(主檔))
            self.assertEqual(輸出, "42\n")

    def test_Python表式名值(self) -> None:
        源碼 = textwrap.dedent(
            """
            施「(lambda x: x + 1)」於一。書之。
            """
        ).strip()
        輸出 = self._執行(源碼)
        self.assertEqual(輸出, "2\n")

    def test_畫譜_turtle_兼容層(self) -> None:
        舊值 = os.environ.get("WENYAN_TURTLE_HEADLESS")
        os.environ["WENYAN_TURTLE_HEADLESS"] = "1"
        try:
            源碼 = textwrap.dedent(
                """
                吾嘗觀「「畫譜」」之書。方悟「備紙」「擇筆」「蘸色」「落筆」「運筆」「提筆」「設色」「裱畫」之義。
                施「備紙」於六十四。於六十四。名之曰「紙」。
                施「擇筆」於「紙」於二。
                施「蘸色」於「紙」於「「曙紅」」。
                施「落筆」於「紙」於一。於一。
                施「運筆」於「紙」於六十三。於一。
                施「運筆」於「紙」於六十三。於六十三。
                施「運筆」於「紙」於一。於六十三。
                施「設色」於「紙」。
                施「提筆」於「紙」。
                施「裱畫」於「紙」於「「out」」。
                """
            ).strip()
            輸出 = self._執行(源碼)
            self.assertEqual(輸出, "")
        finally:
            if 舊值 is None:
                os.environ.pop("WENYAN_TURTLE_HEADLESS", None)
            else:
                os.environ["WENYAN_TURTLE_HEADLESS"] = 舊值


if __name__ == "__main__":
    unittest.main()
