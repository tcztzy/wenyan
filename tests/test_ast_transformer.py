import io
import unittest
from contextlib import redirect_stdout

import wenyan


class 語法樹轉譯測試(unittest.TestCase):
    def _執行(self, 源碼: str) -> str:
        模組樹 = wenyan.編譯為PythonAST(源碼, "<測試>")
        程式碼 = compile(模組樹, "<測試>", "exec")
        緩衝 = io.StringIO()
        with redirect_stdout(緩衝):
            exec(程式碼, {})
        return 緩衝.getvalue()

    def test_書之_hello_world(self):
        輸出 = self._執行("吾有一言。曰「「問天地好在。」」。書之。")
        self.assertEqual(輸出, "問天地好在。\n")

    def test_運算_命名_賦值(self):
        輸出 = self._執行("加一以二。名之曰「甲」。加「甲」以一。昔之「甲」者。今其是矣。夫「甲」。書之。")
        self.assertEqual(輸出, "4\n")

    def test_若_其_比較(self):
        輸出 = self._執行("加一以二。若其等於三者。吾有一言。曰「「是矣。」」。書之。若非。吾有一言。曰「「非也。」」。書之。云云。")
        self.assertEqual(輸出, "是矣。\n")

    def test_為是遍_循環(self):
        輸出 = self._執行(
            "吾有一數。曰一。名之曰「甲」。為是三遍。加「甲」以一。昔之「甲」者。今其是矣。云云。夫「甲」。書之。"
        )
        self.assertEqual(輸出, "4\n")

    def test_恆為是_乃止(self):
        輸出 = self._執行(
            "有數一。名之曰「戊」。恆為是。若「戊」等於三者乃止也。加一以「戊」。昔之「戊」者。今其是矣。云云。夫「戊」。書之。"
        )
        self.assertEqual(輸出, "3\n")


if __name__ == "__main__":
    unittest.main()
