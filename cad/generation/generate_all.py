#!/usr/bin/env python3
"""Run every baseline FreeCAD generator in one FreeCAD Python process."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATORS = [
    ROOT / "cad" / "freecad" / "tolerance_coupon" / "generate.py",
    ROOT / "cad" / "freecad" / "shredder_stage1" / "generate.py",
    ROOT / "cad" / "freecad" / "shredder_stage2" / "generate.py",
    ROOT / "cad" / "freecad" / "full_assembly" / "generate.py",
]


def main() -> None:
    for generator in GENERATORS:
        print(f"==> {generator.relative_to(ROOT)}", flush=True)
        # Stage generators intentionally keep local geometry.py files.  Clear
        # the short module name so a prior stage cannot leak through sys.modules.
        sys.modules.pop("geometry", None)
        runpy.run_path(str(generator), run_name="__main__")


if __name__ == "__main__":
    main()
