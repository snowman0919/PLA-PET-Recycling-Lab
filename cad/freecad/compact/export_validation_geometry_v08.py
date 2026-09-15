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

from geometry import assembly_objects, bearing_side_plate  # noqa: E402
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
    # Read real final-machine stations, not the old jig's 60/200 mm supports.
    sys.path[:0] = [str(ROOT), str(ROOT/"cad/freecad/drive_v08")]
    from cad.freecad.final_v08.generate import final_objects
    from cad.freecad.drive_v08.assembly import integrated_objects
    integrated, _ = integrated_objects(final_objects())
    objects = {item["name"]: item["shape"] for item in integrated}
    stations = {}
    for shaft_id in (105, 153):
        shaft = objects[f"Shaft{shaft_id}"].BoundBox
        stations[str(shaft_id)] = {
            "shaft_y_min_mm": shaft.YMin, "shaft_y_max_mm": shaft.YMax,
            "bearing_y_mm": [objects[f"Bearing{shaft_id}_{y}"].BoundBox.Center.y for y in (315, 455)],
            "gear_y_mm": objects[f"PhaseGear{shaft_id}"].BoundBox.Center.y,
            "cutter_y_mm": [objects[f"Hook{shaft_id}_{i}"].BoundBox.Center.y for i in range(6)],
        }
        if shaft_id == 153:
            stations[str(shaft_id)]["chain_sprocket_y_mm"] = objects["GGM_SH_30T"].BoundBox.Center.y
    (OUT / "geometry_manifest.json").write_text(json.dumps({
        "revision": "final-design-fabrication-closure-v0.8",
        "authority": "FreeCAD Python controlling geometry",
        "physical_validation_state": "NOT_RUN",
        "parts": rows,
        "shredder_stations": stations,
        "hot_zone_stations": {
            "barrel_rear_y_mm": objects["Barrel"].BoundBox.YMax,
            "barrel_die_y_mm": objects["Barrel"].BoundBox.YMin,
            "rear_datum_y_mm": objects["ExtruderRearFixedDatum"].BoundBox.Center.y,
            "front_guide_y_mm": objects["ExtruderFrontSlidingGuide"].BoundBox.Center.y,
            "authority": "GGM integrated final native CAD"
        },
        "geometry_source_sha256": sha256(HERE / "geometry.py"),
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"V08_FREECAD_GEOMETRY_OK parts={len(rows)}")


if __name__ == "__main__":
    main()
