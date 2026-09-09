#!/usr/bin/env python3
"""v0.8 overlay solid validity, collision, mount-clearance gate (FreeCAD)."""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
sys.path.insert(0, str(ROOT / "cad/freecad/final_v08"))

from generate import PARAMS, final_objects  # noqa: E402

OUT = ROOT / "validation/results/final_v08_cad.json"
NEW = {
    "ExtruderSupportRailRear", "ExtruderRearFixedDatum",
    "ExtruderFrontSlidingGuide", "ExtruderFixedCollar",
    "ExtruderRearRetainer", "ExtruderRearRetainerSpacer318", "ExtruderRearRetainerSpacer376",
}
ALLOWED = {
    ("ExtruderFrontSlidingGuide", "HotMountBoltFrontFront"),
    ("ExtruderFrontSlidingGuide", "HotMountBoltFrontRear"),
    ("ExtruderRearFixedDatum", "HotMountBoltRearFront"),
    ("ExtruderRearFixedDatum", "HotMountBoltRearRear"),
    ("ExtruderSupportRailRear", "HotMountBoltFrontRear"),
    ("ExtruderSupportRailRear", "HotMountBoltRearRear"),
    ("ExtruderRearFixedDatum", "RearRetainerM4_318"),
    ("ExtruderRearFixedDatum", "RearRetainerM4_376"),
    ("ExtruderRearRetainer", "RearRetainerM4_318"),
    ("ExtruderRearRetainer", "RearRetainerM4_376"),
    ("ExtruderRearRetainerSpacer318", "RearRetainerM4_318"),
    ("ExtruderRearRetainerSpacer376", "RearRetainerM4_376"),
}


def release_status(geometry_ok: bool, retention: str) -> str:
    if not geometry_ok:
        return "FAIL"
    return "PASS" if retention == "PASS" else "HOLD"


def current_retention_qualification() -> tuple[str, dict]:
    path = ROOT / "analysis/final_validation/results/v0.8/axial_retainer_qualification.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    current = all((ROOT / source).is_file() and hashlib.sha256((ROOT / source).read_bytes()).hexdigest() == digest
                  for source, digest in data["source_sha256"].items())
    passed = current and all(data.get(key) == "PASS" for key in ("status", "numeric_screen", "geometry_check"))
    return ("PASS" if passed else "HOLD"), data


def main() -> None:
    retention, retention_evidence = current_retention_qualification()
    objects = final_objects()
    by_name = {item["name"]: item for item in objects}
    validity = {
        name: {"valid": by_name[name]["shape"].isValid(), "solids": len(by_name[name]["shape"].Solids), "volume_mm3": by_name[name]["shape"].Volume}
        for name in sorted(NEW)
    }
    collisions = []
    for new_name in sorted(NEW):
        for item in objects:
            if item["name"] == new_name or item["name"] in NEW and item["name"] < new_name:
                continue
            volume = by_name[new_name]["shape"].common(item["shape"]).Volume
            if volume > 0.01 and (new_name, item["name"]) not in ALLOWED:
                collisions.append({"a": new_name, "b": item["name"], "common_volume_mm3": round(volume, 6)})
    mount = PARAMS["hot_zone_mount"]
    barrel = by_name["Barrel"]["shape"]
    collar = by_name["ExtruderFixedCollar"]["shape"]
    datum = by_name["ExtruderRearFixedDatum"]["shape"]
    barrel_collar_gap = barrel.distToShape(collar)[0]
    collar_datum_gap = collar.distToShape(datum)[0]
    # Contact is necessary for the claimed collar load path, not sufficient
    # evidence of axial retention, friction capacity or joint strength.
    load_path_contact = barrel_collar_gap <= 1e-6 and collar_datum_gap <= 1e-6
    thrust_axes = [face.Surface.Center for face in by_name["ThrustPlate"]["shape"].Faces
                   if hasattr(face.Surface, "Radius") and abs(face.Surface.Radius-14.15) < 1e-6]
    thrust_aligned = (bool(thrust_axes)
                      and by_name["ThrustPlate"]["shape"].BoundBox.XMin == PARAMS["extruder_thrust_stack"]["plate_global_x_mm"]
                      and all(abs(p.y-347) < 1e-6 and abs(p.z-382) < 1e-6 for p in thrust_axes))
    result = {
        "revision": PARAMS["revision"], "new_objects": validity, "unexpected_collisions": collisions,
        "thermal_expansion": {
            "predicted_pet_growth_mm": mount["predicted_pet_growth_mm"],
            "available_axial_travel_mm": mount["cold_axial_travel_mm"],
            "margin_mm": round(mount["cold_axial_travel_mm"] - mount["predicted_pet_growth_mm"], 4),
        },
        "physical_validation_state": "NOT_RUN",
        "thrust_seat_axis_alignment": {"status": "PASS" if thrust_aligned else "FAIL",
                                      "target_yz_mm": [347,382],
                                      "seat_axes_yz_mm": [[p.y,p.z] for p in thrust_axes]},
        "rear_axial_load_path": {
            "barrel_to_collar_minimum_distance_mm": barrel_collar_gap,
            "collar_to_datum_minimum_distance_mm": collar_datum_gap,
            "necessary_contact_check": "PASS" if load_path_contact else "FAIL",
            "axial_retention_qualification": retention,
            "qualification_evidence": "analysis/final_validation/results/v0.8/axial_retainer_qualification.json",
            "bolt_proof_safety_factor": retention_evidence["m4_class88_proof_safety_factor"],
            "thread_pullout_safety_factor": retention_evidence["thread_pullout_safety_factor"],
            "limitation": "Scoped digital geometry/strength screen only; material certificate, torque/preload and thermal-cycle physical validation remain NOT_RUN.",
        },
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
            "validation/final_v08_cad.py", "cad/freecad/final_v08/generate.py",
            "cad/freecad/compact/geometry.py", "cad/freecad/compact/manufacturing.py",
            "cad/parameters/final_v08.json",
            "analysis/final_validation/results/v0.8/axial_retainer_qualification.json")},
    }
    geometry_ok = thrust_aligned and load_path_contact and not collisions and all(row["valid"] and row["solids"] == 1 for row in validity.values()) and result["thermal_expansion"]["margin_mm"] >= 0
    result["geometry_screening_status"] = "PASS" if geometry_ok else "FAIL"
    result["status"] = release_status(geometry_ok, result["rear_axial_load_path"]["axial_retention_qualification"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["status"] != "PASS":
        raise SystemExit(f"V08_FINAL_CAD_FAIL collisions={len(collisions)} load_path_contact={load_path_contact}")
    print(f"V08_FINAL_CAD_OK objects={len(objects)} margin_mm={result['thermal_expansion']['margin_mm']}")


if __name__ == "__main__":
    main()
