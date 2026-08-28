#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from generate import export_tolerance_coupon
export_tolerance_coupon()
print("PPR-TC01_REGENERATED")
