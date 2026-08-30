#!/usr/bin/env python3
"""Regenerate PPR-C09 from the shared v0.5 FreeCAD source."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from geometry import print_parts
from generate import export_print_part
spec=next(item for item in print_parts() if item["id"]=="PPR-C09")
export_print_part(spec)
print("PPR-C09_REGENERATED")
