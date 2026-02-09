from pathlib import Path
import unittest

import wenyan


class 自舉準備測試(unittest.TestCase):
    def test_自舉骨架可編譯且可執行(self) -> None:
        路徑 = Path(__file__).resolve().parents[1] / "wenyan.wy"
        內容 = 路徑.read_text(encoding="utf-8")

        模組樹 = wenyan.編譯為PythonAST(內容, str(路徑))
        程式碼 = compile(模組樹, str(路徑), "exec")

        作用域: dict[str, object] = {"__name__": "__main__", "__file__": str(路徑)}
        exec(程式碼, 作用域, 作用域)

        主術 = 作用域.get("主術")
        self.assertTrue(callable(主術))
        self.assertEqual(主術(), 0)


if __name__ == "__main__":
    unittest.main()
