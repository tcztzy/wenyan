import sys
import unittest
from pathlib import Path

from wenyan import 主術


class ExamplesTest(unittest.TestCase):
    def test_examples(self):
        example_paths = sorted(Path("examples").glob("*.wy"))
        self.assertTrue(example_paths, "No example files found")
        original_argv = list(sys.argv)
        try:
            for path in example_paths:
                with self.subTest(example=str(path)):
                    sys.argv = ["wenyan", str(path)]
                    主術()
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
