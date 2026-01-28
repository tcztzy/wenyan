import importlib
import pathlib
from importlib.metadata import PackageNotFoundError, version

import lark

try:
    __version__ = version(__package__)  # type: ignore
except PackageNotFoundError:
    # package is not installed
    __version__ = "__UNKNOWN__"
__logo__ = " ,_ ,_\n \\/ ==\n /\\ []\n"
parser = lark.Lark.open(
    str(pathlib.Path(__file__).parent / "wenyan.lark"),
    start="mod",
    parser="lalr",
    propagate_positions=True,
)
importlib.import_module("wenyan.importer")
