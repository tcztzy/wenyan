import unittest

import wenyan


class 詞法位置測試(unittest.TestCase):
    def test_位置切片對應原文(self):
        來源 = "吾有一數。曰二。名之曰「甲」。"
        符號列 = list(wenyan.詞法分析器(來源))
        原文片段列 = [來源[符.position] for 符 in 符號列]
        self.assertEqual(原文片段列, ["吾有", "一", "數", "曰", "二", "名之曰", "「甲」"])
        self.assertTrue(all(isinstance(符.position, slice) for 符 in 符號列))

    def test_言位置包含引號(self):
        來源 = "曰「「甲乙」」。"
        符號列 = list(wenyan.詞法分析器(來源))
        原文片段列 = [來源[符.position] for 符 in 符號列]
        self.assertEqual(原文片段列, ["曰", "「「甲乙」」"])


if __name__ == "__main__":
    unittest.main()
