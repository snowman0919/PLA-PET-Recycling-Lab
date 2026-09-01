#!/usr/bin/env python3
"""P0-G/H generated evidence의 고신호 계약 검증."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # Regenerate from production surrogate sources first so stale JSON cannot
    # make this gate pass after a model mutation.
    subprocess.run(["python3", "analysis/process_feed/run_feed_surrogate.py"],
                   cwd=ROOT, check=True)
    subprocess.run(["python3", "analysis/shredder_recirculation/run_recirculation_surrogate.py"],
                   cwd=ROOT, check=True)
    feed = json.loads((ROOT / "analysis/process_feed/feed_validation.json").read_text())
    recirc = json.loads((ROOT / "analysis/shredder_recirculation/recirculation_validation.json").read_text())
    cad = json.loads((ROOT / "exports/process_v0621/manifest.json").read_text())
    collision = json.loads((ROOT / "exports/process_v0621/collision_and_clearance.json").read_text())
    fusion = json.loads((ROOT / "exports/process_v0621/fusion_change_classification.json").read_text())
    require(feed["status"] == "PASS" and feed["material_form_count"] == 8, "feed envelope")
    require(90 <= feed["delivered_feed_range_g_h"][0] <= feed["delivered_feed_range_g_h"][1] <= 110, "feed rate")
    require(feed["worst_starvation_s"] <= 2 and feed["worst_bridge_clear_cycles"] <= 3, "starvation/bridge")
    require(feed["worst_torque_nm"] < 2.2 and feed["worst_current_a"] < 4.2, "torque/current")
    require(feed["uncontrolled_overfeed_samples"] == 0, "overfeed")
    require(all(c["safe"] and c["response"] in {"DERATE_75_G_H", "CONTROLLED_PAUSE", "DERATE_THEN_PAUSE"} for c in feed["degraded_cases"]), "degraded response")
    require(recirc["status"] == "PASS" and recirc["selected_concept"] == "PASSIVE_ROTOR_SWEPT_RETURN", "recirculation selection")
    require(recirc["worst_case"]["maximum_pet_ribbon_bypass_probability"] <= 0.01, "ribbon bypass")
    require(not recirc["worst_case"]["guarded_fragment_ejection"], "guard containment")
    require(cad["all_valid_solids"] and cad["all_bboxes_within_210_mm"] and len(cad["parts"]) == 10, "CAD solids")
    require(collision["pass"] and collision["physical_validation"] == "NOT_RUN", "collision/claim scope")
    for part in cad["parts"]:
        step = ROOT / part["step"]
        require(step.is_file() and hashlib.sha256(step.read_bytes()).hexdigest() == part["step_sha256"], f"STEP hash {part['part_id']}")
        if part["printable"]:
            stl = ROOT / part["stl"]
            require(stl.is_file() and hashlib.sha256(stl.read_bytes()).hexdigest() == part["stl_sha256"], f"STL hash {part['part_id']}")
    require(any(c["decision"] == "NEW_CASE_REQUIRED" for c in fusion["classification"]), "Fusion delta honesty")
    require(fusion["new_case"]["status"] == "PENDING_EXTERNAL_FUSION_EXECUTION", "Fusion execution claim")
    print("PROCESS_MECHANICAL_LANE_PASS")


if __name__ == "__main__":
    main()
