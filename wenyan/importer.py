import importlib
import importlib.machinery
import importlib.util
import runpy
import sys
from types import CodeType

_WY_SUFFIXES = [".wy"]
_INSTALLED = False


def _compile_wenyan(source: str, filename: str, optimize: int = -1) -> CodeType:
    import wenyan
    from wenyan.cmdline import ToPyAST

    tree = wenyan.parser.parse(source)
    tree = ToPyAST().transform(tree)
    return compile(tree, filename, "exec", optimize=optimize)


class WenyanLoader(importlib.machinery.SourceFileLoader):
    def source_to_code(self, data, path, *, _optimize=-1):
        if isinstance(data, bytes):
            source = importlib.util.decode_source(data)
        else:
            source = data
        return _compile_wenyan(source, path, optimize=_optimize)


_runpy_get_code_from_file = runpy._get_code_from_file  # type: ignore


def _get_code_from_file(fname: str):
    if fname.endswith(".wy"):
        with open(fname, "rb") as handle:
            source = importlib.util.decode_source(handle.read())
        return _compile_wenyan(source, fname)
    return _runpy_get_code_from_file(fname)


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    runpy._get_code_from_file = _get_code_from_file  # type: ignore
    loader_details = [
        (
            importlib.machinery.ExtensionFileLoader,
            importlib.machinery.EXTENSION_SUFFIXES,
        ),
        (WenyanLoader, _WY_SUFFIXES),
        (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES),
        (
            importlib.machinery.SourcelessFileLoader,
            importlib.machinery.BYTECODE_SUFFIXES,
        ),
    ]
    sys.path_hooks.insert(0, importlib.machinery.FileFinder.path_hook(*loader_details))
    sys.path_importer_cache.clear()
    importlib.invalidate_caches()
    _INSTALLED = True


install()

__all__ = ["install", "WenyanLoader"]
