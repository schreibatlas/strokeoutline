#!/usr/bin/env python
"""Build strokeoutline documentation with Sphinx.

Run ``python docs/make.py [target]`` from the repository root or run
``python make.py [target]`` from ``docs/``.

Targets include ``clean``, ``html``, ``dirhtml``, ``latex``, ``text``,
``man``, ``changes``, ``linkcheck``, ``doctest``, ``all``, and ``help``.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
BUILD_DIR = DOCS_DIR / "_build"
VALID_TARGETS = {
    "html",
    "dirhtml",
    "latex",
    "text",
    "man",
    "changes",
    "linkcheck",
    "doctest",
    "all",
}


def run_sphinx(target: str) -> None:
    """Run a strict Sphinx build for one output format."""
    output = BUILD_DIR / target
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-W",
            "--keep-going",
            "-b",
            target,
            str(DOCS_DIR),
            str(output),
        ],
        check=True,
    )


def main() -> int:
    """Run the requested documentation target."""
    target = "html" if len(sys.argv) < 2 else sys.argv[1]

    if target == "clean":
        if BUILD_DIR.exists():
            print(f"Cleaning {BUILD_DIR}...")
            shutil.rmtree(BUILD_DIR)
        return 0

    if target == "help":
        print(__doc__)
        return 0

    if target not in VALID_TARGETS:
        print(f"Unknown target: {target}")
        print("Use 'help' target for help")
        return 1

    targets = ("html", "dirhtml", "latex") if target == "all" else (target,)
    for output_format in targets:
        print(f"Building {output_format} documentation...")
        run_sphinx(output_format)

    if target == "all":
        print(f"Build finished. Documentation outputs are in {BUILD_DIR}")
    else:
        print(f"Build finished. Documentation is in {BUILD_DIR / target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
