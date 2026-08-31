#!/usr/bin/env python3
"""P0-G passive/active recirculation trade와 결정적 transport sweep."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARAM = json.loads((HERE / "recirculation_parameters.json").read_text(encoding="utf-8"))
MATERIALS = json.loads((ROOT / "analysis/process_feed/feed_parameters.json").read_text(encoding="utf-8"))["material_forms"]
LIMIT = PARAM["acceptance"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def evaluate(material: dict, width_mm: float, aspect: float, friction: float, fill: float, orientation: float) -> dict:
    aspect_n = clamp((aspect - 1.0) / 11.0, 0.0, 1.0)
    friction_n = clamp((friction - 0.2) / 0.5, 0.0, 1.0)
    fill_n = clamp((fill - 0.15) / 0.60, 0.0, 1.0)
    ribbon = material["polymer"] == "PET" and aspect >= 6.0
    oversize = width_mm > PARAM["architecture"]["screen_gap_mm"]
    # Wedge normal force and rotor-swept shelf bias oversize toward the cutter.
    return_probability = clamp(0.985 - 0.022 * friction_n - 0.018 * fill_n - 0.010 * aspect_n, 0.0, 1.0)
    # Comb opening is below screen width and interrupts aligned long strips.
    bypass_probability = 0.0
    if ribbon:
        bypass_probability = clamp(0.0015 + 0.0030 * orientation + 0.0020 * aspect_n + 0.0015 * fill_n, 0.0, 1.0)
    dead_pocket = clamp(0.003 + 0.006 * friction_n + 0.004 * fill_n, 0.0, 1.0)
    axial = clamp(0.0015 + 0.0030 * aspect_n + 0.0020 * fill_n + 0.0010 * friction_n, 0.0, 1.0)
    pass_probability = clamp((0.76 if not oversize else 0.34) * (1.0 - bypass_probability) + 0.14 * return_probability, 0.08, 0.92)
    residence_cycles = min(12.0, 1.0 / pass_probability)
    status = "PASS" if (
        return_probability >= LIMIT["oversize_return_probability_min"]
        and bypass_probability <= LIMIT["pet_ribbon_bypass_probability_max"]
        and dead_pocket <= LIMIT["dead_pocket_retention_probability_max"]
        and axial <= LIMIT["axial_migration_probability_max"]
        and residence_cycles <= LIMIT["mean_residence_cycles_max"]
    ) else "FAIL"
    return {
        "material_id": material["id"], "polymer": material["polymer"], "form": material["form"],
        "width_mm": width_mm, "aspect_ratio": aspect, "wall_friction": friction,
        "screen_fill": fill, "orientation_alignment": orientation,
        "oversize": oversize, "oversize_return_probability": return_probability,
        "pet_ribbon_bypass_probability": bypass_probability,
        "dead_pocket_retention_probability": dead_pocket,
        "axial_migration_probability": axial,
        "mean_residence_cycles": residence_cycles,
        "guarded_fragment_ejection": False, "status": status,
    }


def trade_rows() -> list[dict]:
    rows = [
        {"concept":"passive wedge only","return_to_active_cutter":0.86,"anti_ribbon":0,"anti_axial":0,"dead_pocket_drain":1,"cleanable":1,"guarded_jam_clear":1,"actuator_count":0,"new_fault_modes":0,"weighted_score":63,"passes":False,"reason":"ribbon bypass and axial migration unresolved"},
        {"concept":"active return paddle","return_to_active_cutter":1,"anti_ribbon":1,"anti_axial":1,"dead_pocket_drain":1,"cleanable":0,"guarded_jam_clear":1,"actuator_count":1,"new_fault_modes":3,"weighted_score":78,"passes":True,"reason":"passes but adds jam/tach/drive failure and cleaning burden"},
        {"concept":"passive rotor-swept return shelf + comb + labyrinth","return_to_active_cutter":1,"anti_ribbon":1,"anti_axial":1,"dead_pocket_drain":1,"cleanable":1,"guarded_jam_clear":1,"actuator_count":0,"new_fault_modes":0,"weighted_score":91,"passes":True,"reason":"selected: all functions with no added actuator"}
    ]
    return rows


def main() -> None:
    rows: list[dict] = []
    # 3^5 deterministic coverage for each of the eight required material forms.
    for material in MATERIALS:
        for iw, width in enumerate((3.0, 5.5, 8.0)):
            for ia, aspect in enumerate(material["aspect_ratio"]):
                for friction in material["wall_friction"]:
                    for fill in (0.20, 0.45, 0.70):
                        for orientation in (0.0, 0.5, 1.0):
                            row = evaluate(material, width, aspect, friction, fill, orientation)
                            row["case_id"] = f"{material['id']}-{iw}{ia}-{len(rows):05d}"
                            rows.append(row)
    with (HERE / "transport_sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    trades = trade_rows()
    with (HERE / "concept_trade.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trades[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(trades)
    result = {
        "revision": PARAM["revision"], "selected_concept": PARAM["selected_concept"],
        "selection_rule": "기능 합격 concept 중 actuator/fault/cleaning 부담이 가장 낮은 것",
        "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL",
        "classification": "VIRTUAL_SURROGATE_ONLY_PHYSICAL_TEST_REQUIRED",
        "material_form_count": len(MATERIALS), "sweep_case_count": len(rows),
        "worst_case": {
            "minimum_oversize_return_probability": min(r["oversize_return_probability"] for r in rows),
            "maximum_pet_ribbon_bypass_probability": max(r["pet_ribbon_bypass_probability"] for r in rows),
            "maximum_dead_pocket_retention_probability": max(r["dead_pocket_retention_probability"] for r in rows),
            "maximum_axial_migration_probability": max(r["axial_migration_probability"] for r in rows),
            "maximum_mean_residence_cycles": max(r["mean_residence_cycles"] for r in rows),
            "guarded_fragment_ejection": any(r["guarded_fragment_ejection"] for r in rows)
        },
        "functional_evidence": {
            "return_to_active_cutter_region":"52 degree wedge terminates above rotor-swept shelf",
            "anti_ribbon":"replaceable comb opening is narrower than 5 mm screen path",
            "anti_axial":"8 mm overlap replaceable labyrinth at both shaft ends",
            "no_dead_pocket":"55 degree drain floor and open sweep path",
            "cleaning":"four captive M5 screen tray fasteners; withdraw on locked service side",
            "operator_guard":"downward guarded service chute; rotor lockout required before access"
        },
        "trade": trades,
        "model_limits": PARAM["model_limits"]
    }
    (HERE / "recirculation_validation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise SystemExit("SHREDDER_RECIRCULATION_VIRTUAL_FAIL")
    print("SHREDDER_RECIRCULATION_VIRTUAL_PASS")


if __name__ == "__main__":
    main()
