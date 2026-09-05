#!/usr/bin/env python3
"""v0.8 해석용 형상을 controlling FreeCAD Python에서 직접 내보낸다."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from geometry import bearing_side_plate  # noqa: E402
from generate import normalize_step  # noqa: E402
from manufacturing import extruder_barrel  # noqa: E402

OUT = ROOT / "analysis" / "final_validation" / "input"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(name: str, shape: Part.Shape) -> dict:
    if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise RuntimeError(f"{name}: invalid controlling solid")
    path = OUT / f"{name}.step"
    doc = App.newDocument(f"v08_{name}")
    obj = doc.addObject("PartDesign::Feature", name)
    obj.Shape = shape
    doc.recompute()
    Part.export([obj], str(path))
    normalize_step(path)
    App.closeDocument(doc.Name)

    check = App.newDocument(f"v08_reimport_{name}")
    imported = check.addObject("PartDesign::Feature", "Reimported")
    imported.Shape = Part.read(str(path))
    check.recompute()
    volume_error = abs(imported.Shape.Volume - shape.Volume) / shape.Volume
    if not imported.Shape.isValid() or len(imported.Shape.Solids) != 1 or volume_error > 1e-6:
        raise RuntimeError(f"{name}: STEP reimport mismatch")
    App.closeDocument(check.Name)
    box = shape.BoundBox
    return {
        "file": path.name,
        "sha256": sha256(path),
        "solid_count": 1,
        "volume_mm3": round(shape.Volume, 6),
        "bbox_mm": [round(box.XLength, 6), round(box.YLength, 6), round(box.ZLength, 6)],
        "step_reimport_volume_error_fraction": volume_error,
        "status": "PASS",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [export("bearing_plate", bearing_side_plate()), export("extruder_barrel", extruder_barrel())]
    (OUT / "geometry_manifest.json").write_text(json.dumps({
        "revision": "final-design-fabrication-closure-v0.8",
        "authority": "FreeCAD Python controlling geometry",
        "physical_validation_state": "NOT_RUN",
        "parts": rows,
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"V08_FREECAD_GEOMETRY_OK parts={len(rows)}")


if __name__ == "__main__":
    main()
