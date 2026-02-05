import unittest

import wenyan


class LexerPositionTest(unittest.TestCase):
    def test_positions_slice_to_lexeme(self):
        source = "吾有一數。曰二。名之曰「甲」。"
        tokens = list(wenyan.詞法分析器(source))
        lexemes = [source[t.position] for t in tokens]
        self.assertEqual(lexemes, ["吾有", "一", "數", "曰", "二", "名之曰", "「甲」"])
        self.assertTrue(all(isinstance(t.position, slice) for t in tokens))

    def test_literal_positions_include_quotes(self):
        source = "曰「「甲乙」」。"
        tokens = list(wenyan.詞法分析器(source))
        lexemes = [source[t.position] for t in tokens]
        self.assertEqual(lexemes, ["曰", "「「甲乙」」"])


if __name__ == "__main__":
    unittest.main()
