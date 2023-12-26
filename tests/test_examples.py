import sys
from pathlib import Path

from wenyan.cmdline import wenyan_main


def test_examples():
    for path in Path("examples").glob("*.wy"):
        sys.argv = ["wenyan", str(path)]
        wenyan_main()
