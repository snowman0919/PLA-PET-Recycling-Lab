#!/usr/bin/env python3
"""Verify released left/right cutter-shaft and phase-gear clocking in FreeCAD."""
import hashlib
import json
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
from geometry import cutter_shaft, hook_disc  # noqa: E402
from manufacturing import solid_phase_gear  # noqa: E402


def rotated(shape, angle):
    result = shape.copy()
    result.rotate(App.Vector(), App.Vector(0, 1, 0), angle)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = []
    for side, shaft_phase, tooth_phase in (("L", 0.0, 0.0), ("R", 180 / 7, 180 / 16)):
        shaft = cutter_shaft(key_phase_deg=shaft_phase, shaft_id="153" if side=="R" else "105")
        cutter_key = rotated(Part.makeBox(6, 6, 3.4, App.Vector(-3, 100 if side=="R" else 70, 9.1)), shaft_phase)
        gear_key = rotated(Part.makeBox(8, 6, 3.9, App.Vector(-4, 220 if side=="R" else 205, 8.6)), shaft_phase)
        disc = rotated(hook_disc(), shaft_phase)
        disc_key = rotated(Part.makeBox(6, 6, 5.8, App.Vector(-3, 0, 9.1)), shaft_phase)
        local_key_angle = shaft_phase - tooth_phase
        gear = rotated(solid_phase_gear(local_key_angle), tooth_phase)
        gear_key_local = rotated(Part.makeBox(8, 18, 5.8, App.Vector(-4, 0, 9.6)), shaft_phase)
        assert all(shape.isValid() and len(shape.Solids) == 1 for shape in (shaft, disc, gear))
        assert max(shaft.common(key).Volume for key in (cutter_key, gear_key)) < 1e-6
        assert disc.common(disc_key).Volume < 1e-6 and gear.common(gear_key_local).Volume < 1e-6
        rows.append({"side": side, "shaft_key_datum_deg": shaft_phase,
                     "installed_tooth_phase_deg": tooth_phase,
                     "gear_local_keyway_deg": local_key_angle,
                     "clocking_residual_deg": abs(shaft_phase - tooth_phase - local_key_angle),
                     "status": "PASS"})
    assert math.isclose(rows[1]["gear_local_keyway_deg"], 14.464285714285715)
    output = {"status": "PASS", "physical_validation_state": "NOT_RUN", "rows": rows,
              "scope": "Nominal released solids and key void alignment; manufacturing clock inspection and physical fit remain NOT_RUN.",
              "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in (
                  Path(__file__).resolve(), ROOT / "cad/freecad/compact/geometry.py",
                  ROOT / "cad/freecad/compact/manufacturing.py")}}
    path = ROOT / "analysis/final_validation/results/v0.8/phase_clocking_release.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print("PHASE_CLOCKING_RELEASE_PASS sides=2 physical=NOT_RUN")


if __name__ == "__main__":
    main()
