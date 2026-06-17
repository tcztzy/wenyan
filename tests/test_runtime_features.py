import builtins
import io
import os
import subprocess
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
        有原狀態 = hasattr(builtins, "__wenyan_llvm_state__")
        原狀態 = getattr(builtins, "__wenyan_llvm_state__", None)
        sys.modules["llvmlite"] = 假套件
        sys.modules["llvmlite.binding"] = 假綁定
        if 有原狀態:
            delattr(builtins, "__wenyan_llvm_state__")
        域: dict[str, Any] = {"__wenyan_jit_backend__": "llvm"}
        try:
            exec(wenyan.內建序言源碼, 域, 域)
            llvm, ctypes = 域["__文言LLVM後端"]()
        finally:
            if 有原狀態:
                builtins.__wenyan_llvm_state__ = 原狀態
            elif hasattr(builtins, "__wenyan_llvm_state__"):
                delattr(builtins, "__wenyan_llvm_state__")
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

    def test_LLVM_JIT支援乘除取餘(self) -> None:
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「乘」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                乘「甲」以「乙」。乃得矣。
            是謂「乘」之術也。

            吾有一術。名之曰「除」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                除「甲」以「乙」。乃得矣。
            是謂「除」之術也。

            吾有一術。名之曰「取餘」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                除「甲」以「乙」所餘幾何。乃得矣。
            是謂「取餘」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm乘除餘>")
        程式碼 = compile(模組樹, "<jitllvm乘除餘>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm乘除餘>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        乘 = cast(Callable[..., Any], 作用域["乘"])
        除 = cast(Callable[..., Any], 作用域["除"])
        取餘 = cast(Callable[..., Any], 作用域["取餘"])

        self.assertEqual(乘(3, 4), 12)
        self.assertEqual(乘(-2, 5), -10)
        self.assertEqual(除(10, 2), 5)
        self.assertEqual(除(9, 3), 3)
        self.assertEqual(取餘(10, 3), 1)
        self.assertEqual(取餘(7, 3), 1)

        乘中介碼 = cast(str | None, getattr(乘, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(乘中介碼)
        assert 乘中介碼 is not None
        self.assertIn("mul i64", 乘中介碼)

        除中介碼 = cast(str | None, getattr(除, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(除中介碼)
        assert 除中介碼 is not None
        self.assertIn("sdiv i64", 除中介碼)

        餘中介碼 = cast(str | None, getattr(取餘, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(餘中介碼)
        assert 餘中介碼 is not None
        self.assertIn("srem i64", 餘中介碼)

    def test_LLVM_JIT支援多語句函數體(self) -> None:
        """加甲以乙。乘其以甲。—多句算術鏈經由棧傳遞值。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「算」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乘其以「甲」。乃得矣。
            是謂「算」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm多句>")
        程式碼 = compile(模組樹, "<jitllvm多句>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm多句>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        算 = cast(Callable[..., Any], 作用域["算"])
        self.assertEqual(算(2, 3), (2 + 3) * 2)
        self.assertEqual(算(5, 7), (5 + 7) * 5)

        中介碼 = cast(str | None, getattr(算, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("add i64", 中介碼)
        self.assertIn("mul i64", 中介碼)
        self.assertIn("%r0", 中介碼)
        self.assertIn("%r1", 中介碼)

    def test_LLVM_JIT支援三句算術鏈(self) -> None:
        """加甲以乙。乘其以甲。減其以乙。—三句鏈使用加減乘。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「鏈算」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                加「甲」以「乙」。乘其以「甲」。減其以「乙」。乃得矣。
            是謂「鏈算」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm三句>")
        程式碼 = compile(模組樹, "<jitllvm三句>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm三句>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        鏈算 = cast(Callable[..., Any], 作用域["鏈算"])
        self.assertEqual(鏈算(2, 3), (2 + 3) * 2 - 3)
        self.assertEqual(鏈算(5, 2), (5 + 2) * 5 - 2)

        中介碼 = cast(str | None, getattr(鏈算, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("add i64", 中介碼)
        self.assertIn("mul i64", 中介碼)
        self.assertIn("sub i64", 中介碼)
        self.assertIn("%r0", 中介碼)
        self.assertIn("%r1", 中介碼)
        self.assertIn("%r2", 中介碼)

    def test_LLVM_JIT支援夫句與算術鏈(self) -> None:
        """夫甲。加其以乙。—夫句推值後接算術。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「夫加」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                夫「甲」。加其以「乙」。乃得矣。
            是謂「夫加」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm夫加>")
        程式碼 = compile(模組樹, "<jitllvm夫加>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm夫加>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        夫加 = cast(Callable[..., Any], 作用域["夫加"])
        self.assertEqual(夫加(5, 3), 8)
        self.assertEqual(夫加(10, 7), 17)

        中介碼 = cast(str | None, getattr(夫加, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("add i64", 中介碼)

    def test_LLVM_JIT夫句與減法鏈(self) -> None:
        """夫三。減甲以其。—夫句接算術使用其為右值。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「減反」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                夫三。減「甲」以其。乃得矣。
            是謂「減反」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm減反>")
        程式碼 = compile(模組樹, "<jitllvm減反>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm減反>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        減反 = cast(Callable[..., Any], 作用域["減反"])
        self.assertEqual(減反(1), 1 - 3)
        self.assertEqual(減反(7), 7 - 3)

        中介碼 = cast(str | None, getattr(減反, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("sub i64", 中介碼)

    def test_LLVM_JIT超界整數回退Python路徑(self) -> None:
        """大於 2^30 的參數應回退到 Python 計算。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「加倍」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                乘「甲」以二。乃得矣。
            是謂「加倍」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm超界>")
        程式碼 = compile(模組樹, "<jitllvm超界>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm超界>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        加倍 = cast(Callable[..., Any], 作用域["加倍"])
        大數 = 1 << 70
        self.assertEqual(加倍(大數), 大數 * 2)
        self.assertEqual(加倍(3), 6)

    def test_LLVM_JIT已編譯快路仍守衛超界整數(self) -> None:
        """已編譯 LLVM 術再次遇超界 int 時仍須回退 Python。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「加倍」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                乘「甲」以二。乃得矣。
            是謂「加倍」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm超界已編譯>")
        程式碼 = compile(模組樹, "<jitllvm超界已編譯>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm超界已編譯>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        加倍 = cast(Callable[..., Any], 作用域["加倍"])
        self.assertEqual(加倍(3), 6)
        大數 = 1 << 70
        self.assertEqual(加倍(大數), 大數 * 2)

    def test_LLVM_JIT引擎跨作用域回收不崩潰(self) -> None:
        """V30：舊 exec 作用域回收不得釋放 LLVM 本機碼而崩潰。"""
        腳本 = r"""
import gc
import wenyan

def 執行(文檔名, 源碼, 呼叫列):
    模組樹 = wenyan.編譯為PythonAST(源碼, 文檔名)
    程式碼 = compile(模組樹, 文檔名, "exec")
    作用域 = {
        "__name__": "__main__",
        "__file__": 文檔名,
        "__wenyan_jit_enabled__": True,
        "__wenyan_jit_backend__": "llvm",
        "__wenyan_jit_threshold__": 1,
    }
    exec(程式碼, 作用域)
    for 名, 參, 期 in 呼叫列:
        得 = 作用域[名](*參)
        if 得 != 期:
            raise SystemExit(f"{名}{參}: {得!r} != {期!r}")

案例列 = [
    (
        "<jitllvm回收減反>",
        "吾有一術。名之曰「減反」。欲行是術。必先得一數。曰「甲」。乃行是術曰。夫三。減「甲」以其。乃得矣。是謂「減反」之術也。",
        [("減反", (1,), -2), ("減反", (7,), 4)],
    ),
    (
        "<jitllvm回收鏈算>",
        "吾有一術。名之曰「鏈算」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。加「甲」以「乙」。乘其以「甲」。減其以「乙」。乃得矣。是謂「鏈算」之術也。",
        [("鏈算", (2, 3), 7), ("鏈算", (5, 2), 33)],
    ),
    (
        "<jitllvm回收乘除>",
        "吾有一術。名之曰「乘」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。乘「甲」以「乙」。乃得矣。是謂「乘」之術也。吾有一術。名之曰「除」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。除「甲」以「乙」。乃得矣。是謂「除」之術也。吾有一術。名之曰「取餘」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。除「甲」以「乙」所餘幾何。乃得矣。是謂「取餘」之術也。",
        [
            ("乘", (3, 4), 12),
            ("乘", (-2, 5), -10),
            ("除", (10, 2), 5),
            ("除", (9, 3), 3),
            ("取餘", (10, 3), 1),
            ("取餘", (7, 3), 1),
        ],
    ),
    (
        "<jitllvm回收多句>",
        "吾有一術。名之曰「算」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。加「甲」以「乙」。乘其以「甲」。乃得矣。是謂「算」之術也。",
        [("算", (2, 3), 10), ("算", (5, 7), 60)],
    ),
]

for 文檔名, 源碼, 呼叫列 in 案例列:
    執行(文檔名, 源碼, 呼叫列)
    gc.collect()
"""
        進程 = subprocess.run(
            [sys.executable, "-c", 腳本],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        self.assertEqual(進程.returncode, 0, 進程.stdout + 進程.stderr)

    def test_LLVM_JIT直接返回參數(self) -> None:
        """乃得甲。—直接返回參數。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「返甲」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                乃得「甲」。
            是謂「返甲」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm返參>")
        程式碼 = compile(模組樹, "<jitllvm返參>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm返參>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        返甲 = cast(Callable[..., Any], 作用域["返甲"])
        self.assertEqual(返甲(42), 42)
        self.assertEqual(返甲(-5), -5)

    def test_LLVM_JIT不支援非數參數靜默回退(self) -> None:
        """擁有非數型別參數的術不產生 LLVM 中介碼。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「言返」。欲行是術。必先得一言。曰「甲」。乃行是術曰。
                乃得「甲」。
            是謂「言返」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm非數>")
        程式碼 = compile(模組樹, "<jitllvm非數>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm非數>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        言返 = cast(Callable[..., Any], 作用域["言返"])
        self.assertEqual(言返("hello"), "hello")
        中介碼 = cast(str | None, getattr(言返, "__文言JITLLVM中介碼__"))
        self.assertIsNone(中介碼, "非數參數不產生 LLVM 中介碼")

    def test_LLVM_JIT不支援其餘參數靜默回退(self) -> None:
        """擁有其餘參數的術不產生 LLVM 中介碼。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「取首」。欲行是術。必先得一數。曰「甲」。其餘數。曰「餘」。乃行是術曰。
                乃得「甲」。
            是謂「取首」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm其餘>")
        程式碼 = compile(模組樹, "<jitllvm其餘>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm其餘>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        取首 = cast(Callable[..., Any], 作用域["取首"])
        self.assertEqual(取首(1, 2, 3), 1)
        中介碼 = cast(str | None, getattr(取首, "__文言JITLLVM中介碼__"))
        self.assertIsNone(中介碼, "其餘參數不產生 LLVM 中介碼")

    def test_LLVM_JIT支援變句(self) -> None:
        """變甲。—一元邏輯非運算。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「變術」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                變「甲」。乃得矣。
            是謂「變術」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm變>")
        程式碼 = compile(模組樹, "<jitllvm變>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm變>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        變術 = cast(Callable[..., Any], 作用域["變術"])
        self.assertEqual(變術(0), True)
        self.assertEqual(變術(5), False)
        self.assertEqual(變術(-1), False)

        中介碼 = cast(str | None, getattr(變術, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp eq", 中介碼)
        self.assertIn("zext i1", 中介碼)

    def test_LLVM_JIT支援邏輯或(self) -> None:
        """夫甲。乙。中有陽乎。—邏輯或。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「或術」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                夫「甲」。「乙」。中有陽乎。乃得矣。
            是謂「或術」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm或>")
        程式碼 = compile(模組樹, "<jitllvm或>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm或>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        或術 = cast(Callable[..., Any], 作用域["或術"])
        self.assertEqual(或術(0, 0), 0)
        self.assertEqual(或術(0, 3), 3)
        self.assertEqual(或術(5, 0), 5)
        self.assertEqual(或術(5, 3), 5)

        中介碼 = cast(str | None, getattr(或術, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp ne i64", 中介碼)
        self.assertIn("select i1", 中介碼)

    def test_LLVM_JIT支援邏輯且(self) -> None:
        """夫甲。乙。中無陰乎。—邏輯且。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「且術」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                夫「甲」。「乙」。中無陰乎。乃得矣。
            是謂「且術」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm且>")
        程式碼 = compile(模組樹, "<jitllvm且>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm且>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        且術 = cast(Callable[..., Any], 作用域["且術"])
        self.assertEqual(且術(0, 0), 0)
        self.assertEqual(且術(0, 3), 0)
        self.assertEqual(且術(5, 0), 0)
        self.assertEqual(且術(5, 3), 3)

        中介碼 = cast(str | None, getattr(且術, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp ne i64", 中介碼)
        self.assertIn("select i1", 中介碼)

    def test_LLVM_JIT支援變句與算術鏈(self) -> None:
        """夫甲。變其。加其以乙。—變句與算術鏈組合。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「變鏈」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                夫「甲」。變其。加其以「乙」。乃得矣。
            是謂「變鏈」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm變鏈>")
        程式碼 = compile(模組樹, "<jitllvm變鏈>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm變鏈>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        變鏈 = cast(Callable[..., Any], 作用域["變鏈"])
        self.assertEqual(變鏈(0, 3), 1 + 3)
        self.assertEqual(變鏈(5, 2), 0 + 2)

        中介碼 = cast(str | None, getattr(變鏈, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp eq", 中介碼)
        self.assertIn("add i64", 中介碼)
        self.assertIn("%r0", 中介碼)
        self.assertIn("%r1", 中介碼)
        self.assertIn("%r2", 中介碼)

    def test_LLVM_JIT支援若句基本分支(self) -> None:
        """若甲大於乙者。乃得甲。若非。乃得乙。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「取大」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                若「甲」大於「乙」者。
                    乃得「甲」。
                若非。
                    乃得「乙」。
                云云。
            是謂「取大」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm若>")
        程式碼 = compile(模組樹, "<jitllvm若>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm若>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        取大 = cast(Callable[..., Any], 作用域["取大"])
        self.assertEqual(取大(5, 3), 5)
        self.assertEqual(取大(3, 5), 5)

        中介碼 = cast(str | None, getattr(取大, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp sgt", 中介碼)
        self.assertIn("then0_0", 中介碼)
        self.assertIn("else0_1", 中介碼)

    def test_LLVM_JIT支援若句或若分支(self) -> None:
        """若甲大於乙者。乃得甲。或若乙大於丙者。乃得乙。若非。乃得丙。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「三取大」。欲行是術。必先得三數。曰「甲」曰「乙」曰「丙」。乃行是術曰。
                若「甲」大於「乙」者。
                    乃得「甲」。
                或若「乙」大於「丙」者。
                    乃得「乙」。
                若非。
                    乃得「丙」。
                云云。
            是謂「三取大」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm或若>")
        程式碼 = compile(模組樹, "<jitllvm或若>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm或若>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        三取大 = cast(Callable[..., Any], 作用域["三取大"])
        self.assertEqual(三取大(5, 3, 1), 5)
        self.assertEqual(三取大(3, 5, 1), 5)
        self.assertEqual(三取大(1, 3, 5), 5)

        中介碼 = cast(str | None, getattr(三取大, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp sgt", 中介碼)
        self.assertIn("cond0_1", 中介碼)
        self.assertIn("else0_2", 中介碼)

    def test_LLVM_JIT支援爻值與若句(self) -> None:
        """若甲者。夫陽。若非。夫陰。—使用爻值。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「爻判」。欲行是術。必先得一數。曰「甲」。乃行是術曰。
                若「甲」者。
                    夫陽。乃得矣。
                若非。
                    夫陰。乃得矣。
                云云。
            是謂「爻判」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm爻若>")
        程式碼 = compile(模組樹, "<jitllvm爻若>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm爻若>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        爻判 = cast(Callable[..., Any], 作用域["爻判"])
        self.assertEqual(爻判(0), False)
        self.assertEqual(爻判(5), True)

        中介碼 = cast(str | None, getattr(爻判, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp ne", 中介碼)
        self.assertIn("then0_0", 中介碼)
        self.assertIn("else0_1", 中介碼)

    def test_LLVM_JIT支援爻值直接返回(self) -> None:
        """夫陽。乃得矣。—直接返回陽（1）。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「返陽」。欲行是術。乃行是術曰。
                夫陽。乃得矣。
            是謂「返陽」之術也。

            吾有一術。名之曰「返陰」。欲行是術。乃行是術曰。
                夫陰。乃得矣。
            是謂「返陰」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm爻值>")
        程式碼 = compile(模組樹, "<jitllvm爻值>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm爻值>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        返陽 = cast(Callable[..., Any], 作用域["返陽"])
        返陰 = cast(Callable[..., Any], 作用域["返陰"])
        self.assertEqual(返陽(), True)
        self.assertEqual(返陰(), False)

        陽碼 = cast(str | None, getattr(返陽, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(陽碼)
        assert 陽碼 is not None
        self.assertIn("ret i64 1", 陽碼)

        陰碼 = cast(str | None, getattr(返陰, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(陰碼)
        assert 陰碼 is not None
        self.assertIn("ret i64 0", 陰碼)

    def test_LLVM_JIT支援巢狀若句(self) -> None:
        """外層若甲大於乙者。內層若甲大於丙者。—巢狀分支。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「巢若」。欲行是術。必先得三數。曰「甲」曰「乙」曰「丙」。乃行是術曰。
                若「甲」大於「乙」者。
                    若「甲」大於「丙」者。
                        乃得「甲」。
                    若非。
                        乃得「丙」。
                    云云。
                若非。
                    乃得「乙」。
                云云。
            是謂「巢若」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm巢若>")
        程式碼 = compile(模組樹, "<jitllvm巢若>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm巢若>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        巢若 = cast(Callable[..., Any], 作用域["巢若"])
        self.assertEqual(巢若(5, 3, 2), 5)
        self.assertEqual(巢若(5, 3, 7), 7)
        self.assertEqual(巢若(3, 5, 2), 5)

        中介碼 = cast(str | None, getattr(巢若, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("icmp sgt", 中介碼)
        self.assertIn("then0_0", 中介碼)
        self.assertIn("then1_0", 中介碼)
        self.assertIn("else1_1", 中介碼)

    def test_LLVM_JIT支援巢狀若句含或若(self) -> None:
        """外層若。內層若含或若。—深層巢狀。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「深巢」。欲行是術。必先得三數。曰「甲」曰「乙」曰「丙」。乃行是術曰。
                若「甲」大於「乙」者。
                    若「甲」大於「丙」者。
                        乃得「甲」。
                    或若「乙」大於「丙」者。
                        乃得「乙」。
                    若非。
                        乃得「丙」。
                    云云。
                若非。
                    乃得零。
                云云。
            是謂「深巢」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm深巢>")
        程式碼 = compile(模組樹, "<jitllvm深巢>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm深巢>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        深巢 = cast(Callable[..., Any], 作用域["深巢"])
        self.assertEqual(深巢(5, 3, 2), 5)
        self.assertEqual(深巢(5, 2, 7), 7)
        self.assertEqual(深巢(2, 5, 1), 0)
        self.assertEqual(深巢(1, 2, 3), 0)

        中介碼 = cast(str | None, getattr(深巢, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("then0_0", 中介碼)
        self.assertIn("then0_1", 中介碼)
        self.assertIn("then1_0", 中介碼)

    def test_LLVM_JIT支援循環若句返回(self) -> None:
        """恆為是。若甲大於乙者。乃得甲。若非。乃得乙。"""
        源碼 = textwrap.dedent(
            """
            吾有一術。名之曰「找大」。欲行是術。必先得二數。曰「甲」曰「乙」。乃行是術曰。
                恆為是。
                    若「甲」大於「乙」者。
                        乃得「甲」。
                    若非。
                        乃得「乙」。
                    云云。
                也。
            是謂「找大」之術也。
            """
        ).strip()
        模組樹 = wenyan.編譯為PythonAST(源碼, "<jitllvm循環>")
        程式碼 = compile(模組樹, "<jitllvm循環>", "exec")
        作用域 = {
            "__name__": "__main__",
            "__file__": "<jitllvm循環>",
            "__wenyan_jit_enabled__": True,
            "__wenyan_jit_backend__": "llvm",
            "__wenyan_jit_threshold__": 1,
        }
        exec(程式碼, 作用域)

        找大 = cast(Callable[..., Any], 作用域["找大"])
        self.assertEqual(找大(5, 3), 5)
        self.assertEqual(找大(3, 5), 5)

        中介碼 = cast(str | None, getattr(找大, "__文言JITLLVM中介碼__"))
        self.assertIsNotNone(中介碼)
        assert 中介碼 is not None
        self.assertIn("loop0", 中介碼)
        self.assertIn("icmp sgt", 中介碼)

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
