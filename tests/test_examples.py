import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_NAMES = (
    "01_basic_centerline.py",
    "02_variable_width.py",
    "03_svg_adapter.py",
    "04_closed_centerline.py",
    "05_planarcurve_interop.py",
)


@pytest.mark.parametrize("example_name", EXAMPLE_NAMES)
def test_example_runs(example_name):
    env = os.environ.copy()
    pythonpath = [str(ROOT), env.get("PYTHONPATH", "")]
    env["PYTHONPATH"] = os.pathsep.join(part for part in pythonpath if part)

    completed = subprocess.run(
        [sys.executable, str(ROOT / "examples" / example_name)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert completed.stdout.strip()
