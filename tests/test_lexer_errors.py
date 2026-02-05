import unittest

import wenyan


class LexerErrorTest(unittest.TestCase):
    def test_unterminated_identifier_has_details(self):
        source = "吾有一數名之曰「甲"
        with self.assertRaises(wenyan.文法之禍) as ctx:
            list(wenyan.詞法分析器(source))
        err = ctx.exception
        self.assertEqual(err.msg, "名未尽")
        self.assertEqual(err.filename, "<言>")
        self.assertEqual(err.lineno, 1)
        self.assertEqual(err.offset, 8)
        self.assertEqual(err.text, source)

    def test_invalid_number_has_details(self):
        source = "負負。"
        filename = "example.wy"
        with self.assertRaises(wenyan.文法之禍) as ctx:
            list(wenyan.詞法分析器(source, filename))
        err = ctx.exception
        self.assertEqual(err.msg, "非法數")
        self.assertEqual(err.filename, filename)
        self.assertEqual(err.lineno, 1)
        self.assertEqual(err.offset, 1)
        self.assertEqual(err.text, source)


if __name__ == "__main__":
    unittest.main()
