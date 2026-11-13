import subprocess
import sys
from pathlib import Path

import strokeoutline


def test_package_does_not_import_inkgrammar():
    root = Path(strokeoutline.__file__).resolve().parent
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import inkgrammar" not in text
        assert "from inkgrammar" not in text


def test_source_checkout_has_version_string():
    assert isinstance(strokeoutline.__version__, str)
    assert strokeoutline.__version__


def test_core_import_does_not_require_fonttools():
    code = """
import builtins
original_import = builtins.__import__
def import_without_fonttools(name, *args, **kwargs):
    if name == "fontTools" or name.startswith("fontTools."):
        raise ImportError("FontTools intentionally unavailable")
    return original_import(name, *args, **kwargs)
builtins.__import__ = import_without_fonttools
import strokeoutline
"""
    root = Path(strokeoutline.__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
