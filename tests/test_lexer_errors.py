import unittest

import wenyan


class 詞法錯誤測試(unittest.TestCase):
    def test_名未尽含位置細節(self):
        來源 = "吾有一數名之曰「甲"
        with self.assertRaises(wenyan.文法之禍) as 例外上下文:
            list(wenyan.詞法分析器(來源))
        錯誤 = 例外上下文.exception
        self.assertEqual(錯誤.msg, "名未尽")
        self.assertEqual(錯誤.filename, "<言>")
        self.assertEqual(錯誤.lineno, 1)
        self.assertEqual(錯誤.offset, 8)
        self.assertEqual(錯誤.text, 來源)

    def test_非法數含位置細節(self):
        來源 = "負負。"
        檔名 = "example.wy"
        with self.assertRaises(wenyan.文法之禍) as 例外上下文:
            list(wenyan.詞法分析器(來源, 檔名))
        錯誤 = 例外上下文.exception
        self.assertEqual(錯誤.msg, "非法數")
        self.assertEqual(錯誤.filename, 檔名)
        self.assertEqual(錯誤.lineno, 1)
        self.assertEqual(錯誤.offset, 1)
        self.assertEqual(錯誤.text, 來源)


if __name__ == "__main__":
    unittest.main()
