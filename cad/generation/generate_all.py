#!/usr/bin/env python3
"""FreeCAD entry point for compact v0.3 artifacts."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / "cad/freecad/compact/generate.py"), run_name="__main__")
runpy.run_path(str(ROOT / "cad/generation/generate_manufacturing.py"), run_name="__main__")
