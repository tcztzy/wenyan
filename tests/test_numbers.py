import unittest

from wenyan import 漢字數字, 詞法分析器, 文法之禍


class HanziNumberTest(unittest.TestCase):
    def test_basic_digits(self):
        self.assertEqual(漢字數字("零"), "0")
        self.assertEqual(漢字數字("〇"), "0")
        self.assertEqual(漢字數字("一二三"), "123")

    def test_units(self):
        self.assertEqual(漢字數字("十"), "10")
        self.assertEqual(漢字數字("十二"), "12")
        self.assertEqual(漢字數字("二十"), "20")
        self.assertEqual(漢字數字("二十一"), "21")
        self.assertEqual(漢字數字("一百零二"), "102")
        self.assertEqual(漢字數字("三千零五"), "3005")

    def test_large_units(self):
        self.assertEqual(漢字數字("一萬零三"), "10003")
        self.assertEqual(漢字數字("一億二千三百四十五萬六千七百八十九"), "123456789")

    def test_decimal_dot(self):
        self.assertEqual(漢字數字("一·二三"), "1.23")
        self.assertEqual(漢字數字("零·三"), "0.3")

    def test_decimal_units(self):
        self.assertEqual(漢字數字("分"), "0.1")
        self.assertEqual(漢字數字("三分"), "0.3")
        self.assertEqual(漢字數字("負三分"), "-0.3")
        self.assertEqual(漢字數字("一又二分三釐"), "1.23")
        self.assertEqual(漢字數字("一又二"), "3")

    def test_invalid_numbers(self):
        非法數列表 = ["負負一", "一·二·三", "一又", "二釐分", "·三", "三·", "一又二又三"]
        for 非法數 in 非法數列表:
            with self.subTest(非法數=非法數):
                with self.assertRaises(文法之禍):
                    漢字數字(非法數)

    def test_large_integer_not_scientific(self):
        self.assertEqual(漢字數字("一垓"), "100000000000000000000")

    def test_large_negative_integer_not_scientific(self):
        self.assertEqual(漢字數字("負一垓"), "-100000000000000000000")


class LexerNumberTest(unittest.TestCase):
    def test_lexer_recognizes_numbers(self):
        來源 = "吾有一數。曰二十三。曰負三分。曰一又二分三釐。"
        符號列 = list(詞法分析器(來源))
        數值 = [符.value for 符 in 符號列 if 符.type == "數" and 符.value is not None]
        self.assertEqual(數值, ["1", "23", "-0.3", "1.23"])

    def test_numbers_not_in_identifier_or_literal(self):
        來源 = "曰「甲一」曰「「二三」」"
        符號列 = list(詞法分析器(來源))
        self.assertFalse(any(符.type == "數" for 符 in 符號列))
        名稱 = next(符.value for 符 in 符號列 if 符.type == "名")
        字面量 = next(符.value for 符 in 符號列 if 符.type == "言")
        self.assertEqual(名稱, "甲一")
        self.assertEqual(字面量, "二三")


if __name__ == "__main__":
    unittest.main()
