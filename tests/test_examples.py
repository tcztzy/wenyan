import sys
from pathlib import Path

from wenyan.cmdline import wenyan_main


def run_example(path):
    def run():
        sys.argv = ["wenyan", str(path)]
        wenyan_main()

    return run


for path in Path("examples").glob("*.wy"):
    globals()[f"test_{path.stem.replace("+", "_plus")}"] = run_example(path)
