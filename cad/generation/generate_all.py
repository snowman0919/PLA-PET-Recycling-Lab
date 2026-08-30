#!/usr/bin/env python3
"""FreeCAD entry point for virtual-physics-closure-v0.5.1 artifacts."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / "cad/freecad/compact/generate.py"), run_name="__main__")
runpy.run_path(str(ROOT / "cad/generation/generate_manufacturing.py"), run_name="__main__")
runpy.run_path(str(ROOT / "cad/generation/generate_interface_catalog.py"), run_name="__main__")
runpy.run_path(str(ROOT / "cad/generation/export_modelica_properties.py"), run_name="__main__")
