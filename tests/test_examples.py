import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATHS = tuple(sorted((ROOT / "examples").glob("*.py")))


@pytest.mark.parametrize("example_path", EXAMPLE_PATHS, ids=lambda path: path.name)
def test_example_runs_in_isolated_directory(example_path, tmp_path):
    env = os.environ.copy()
    pythonpath = [str(ROOT), env.get("PYTHONPATH", "")]
    env["PYTHONPATH"] = os.pathsep.join(part for part in pythonpath if part)

    completed = subprocess.run(
        [sys.executable, str(example_path)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert completed.stdout.strip()
    assert completed.stderr == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("example_path", EXAMPLE_PATHS, ids=lambda path: path.name)
def test_importing_example_has_no_output_or_files(example_path, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(example_path), run_name="example_import")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert list(tmp_path.iterdir()) == []
