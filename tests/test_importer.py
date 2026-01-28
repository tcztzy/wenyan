import importlib
import sys


def test_import_wy_module(tmp_path):
    source = (
        "\u543e\u6709\u4e00\u6578\u66f0\u4e09\u540d\u4e4b\u66f0\u300c\u7532\u300d\u3002"
    )
    module_path = tmp_path / "demo.wy"
    module_path.write_text(source, encoding="utf-8")

    sys.path.insert(0, str(tmp_path))
    try:
        import wenyan

        assert wenyan.__name__ == "wenyan"
        importlib.invalidate_caches()
        module = importlib.import_module("demo")
        assert getattr(module, "\u7532") == 3
    finally:
        sys.path.pop(0)
        sys.modules.pop("demo", None)
