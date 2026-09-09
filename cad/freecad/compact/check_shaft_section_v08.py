#!/usr/bin/env python3
"""CUT-05 실제 키홈 단면의 중심축 굽힘 관성과 기존 beam 가정을 대조한다."""

import hashlib
import json
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from geometry import cutter_shaft


def section(shape, y):
    thickness = 1.0
    slab = shape.common(Part.makeBox(30, thickness, 30, App.Vector(-15, y, -15)))
    assert slab.isValid() and len(slab.Solids) == 1
    slab = slab.Solids[0]
    area = slab.Volume / thickness
    inertia = slab.MatrixOfInertia
    ix = inertia.A11 / thickness - area * thickness**2 / 12
    iz = inertia.A33 / thickness - area * thickness**2 / 12
    ixz = inertia.A13 / thickness
    weakest = (ix + iz) / 2 - math.hypot((ix - iz) / 2, ixz)
    return {"y_mm": y, "area_mm2": area, "centroid_z_mm": slab.CenterOfMass.z,
            "Ixx_mm4": ix, "Izz_mm4": iz, "Imin_mm4": weakest}


def main():
    shape = cutter_shaft()
    rows = [section(shape, y) for y in (10, 40, 60, 170, 200)]
    circle_i = math.pi * 25**4 / 64
    # Independent analytical control catches axis and thin-slab corrections.
    for row in (rows[1], rows[3]):
        assert math.isclose(row["Imin_mm4"], circle_i, rel_tol=1e-8)
        assert math.isclose(row["area_mm2"], math.pi * 12.5**2, rel_tol=1e-8)
    bound_i = math.pi * 22**4 / 64
    weakest = min(row["Imin_mm4"] for row in rows)
    assert weakest > bound_i
    result = {
        "status": "PASS", "scope": "CAD centroidal bending section properties only",
        "physical_validation_state": "NOT_RUN", "sections": rows,
        "screening_diameter_mm": 22.0, "screening_I_mm4": bound_i,
        "minimum_CAD_to_screening_I_ratio": weakest / bound_i,
        "limitations": ["Does not qualify torsion, key contact, local stress or bearing/frame compliance.",
                        "Loaded phase acceptance is evaluated separately with exact keyed torsion and bearing/gear terms."],
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__).resolve(), HERE / "geometry.py")},
    }
    out = ROOT / "analysis/final_validation/results/v0.8/shaft_section.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"V08_SHAFT_SECTION_PASS minimum_I_ratio={weakest / bound_i:.6f}")


if __name__ == "__main__":
    main()
