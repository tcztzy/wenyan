from importlib.metadata import version, PackageNotFoundError
import pathlib

import lark

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    # package is not installed
    pass

parser = lark.Lark.open(
    pathlib.Path(__file__).parent / "wenyan.lark", start="program", parser="lalr"
)
