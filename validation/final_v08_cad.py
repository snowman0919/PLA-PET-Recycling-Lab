#!/usr/bin/env python3
"""v0.8 overlay solid validity, collision, mount-clearance gate (FreeCAD)."""

from __future__ import annotations

import json
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
}
ALLOWED = {
    ("ExtruderFrontSlidingGuide", "HotMountBoltFrontFront"),
    ("ExtruderFrontSlidingGuide", "HotMountBoltFrontRear"),
    ("ExtruderRearFixedDatum", "HotMountBoltRearFront"),
    ("ExtruderRearFixedDatum", "HotMountBoltRearRear"),
    ("ExtruderSupportRailRear", "HotMountBoltFrontRear"),
    ("ExtruderSupportRailRear", "HotMountBoltRearRear"),
}


def main() -> None:
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
    result = {
        "revision": PARAMS["revision"], "new_objects": validity, "unexpected_collisions": collisions,
        "thermal_expansion": {
            "predicted_pet_growth_mm": mount["predicted_pet_growth_mm"],
            "available_axial_travel_mm": mount["cold_axial_travel_mm"],
            "margin_mm": round(mount["cold_axial_travel_mm"] - mount["predicted_pet_growth_mm"], 4),
        },
        "physical_validation_state": "NOT_RUN",
    }
    result["status"] = "PASS" if not collisions and all(row["valid"] and row["solids"] == 1 for row in validity.values()) and result["thermal_expansion"]["margin_mm"] >= 0 else "FAIL"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["status"] != "PASS":
        raise SystemExit(f"V08_FINAL_CAD_FAIL collisions={len(collisions)}")
    print(f"V08_FINAL_CAD_OK objects={len(objects)} margin_mm={result['thermal_expansion']['margin_mm']}")


if __name__ == "__main__":
    main()
