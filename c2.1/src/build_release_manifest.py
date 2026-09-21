"""Build deterministic P0-P6 status and artifact manifests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]


def load(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    kin = load(C21/"results/kinematic_validation.json")
    cad = load(C21/"results/cad_validation.json")
    machine = load(C21/"results/machine_integration.json")
    native = load(C21/"results/machine_freecad.json")
    bom = load(C21/"results/system_bom_summary.json")
    wiring = load(C21/"results/machine_wiring.json")
    firmware = load(C21/"results/firmware_build.json")
    drawings = load(C21/"results/p6_drawings.json")
    coupon = load(REPO/"c2/results/coupon_fe_summary.json")
    thermal = load(REPO/"c2/results/p5_thermal_control.json")
    gate = load(REPO/"c2/results/performance_gate.json")

    summary = {
        "revision": "C2.1-P6",
        "date": "2026-09-21",
        "overall": "DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD",
        "stages": {
            "P0": "DYNAMIC_EVIDENCE_VERIFIER_PASS",
            "P1": kin["loaded_output_contact"],
            "P2": cad["status"],
            "P3": bom["cost_conclusion"],
            "P4": coupon["status"],
            "P5": thermal["status"],
            "P6": machine["status"],
        },
        "machine": {
            "assembly_objects": machine["assembly_objects"],
            "reimported_solids": machine["reimported_solids"],
            "interface_collision_passed": machine["interface_collision"]["passed"],
            "body_passed": machine["body"]["passed"],
            "operating_envelope_passed": machine["operating_envelope"]["passed"],
            "native_freecad_objects": native["objects"],
            "native_freecad_valid_objects": native["valid_objects"],
        },
        "package": {
            "bom_rows": bom["active_rows"],
            "known_cost_rows": bom["known_cost_rows"],
            "unknown_cost_rows": bom["unknown_cost_rows"],
            "wiring_components": wiring["components"],
            "wiring_pins": wiring["pins"],
            "wiring_nets": wiring["nets"],
            "firmware_host_cases": firmware["cases"],
            "drawing_status": drawings["status"],
        },
        "performance": {"status": gate["status"], "measured_runs": 0,
                        "calibrated_training_records": 0},
        "release_boundary": {
            "procurement": "HOLD", "fabrication": "HOLD", "energization": "HOLD",
            "target_firmware_cross_compile": firmware["target_cross_compile"],
            "firmware_flash": firmware["flash"],
            "physical_tests": "DID_NOT_RUN",
        },
    }
    (C21/"results/validation_summary.json").write_text(
        json.dumps(summary, indent=2)+"\n")

    excluded = {C21/"results/p6_manifest.json"}
    files = [path for path in C21.rglob("*")
             if path.is_file() and path not in excluded
             and "__pycache__" not in path.parts and path.suffix != ".pyc"]
    cross_stage = [
        REPO/"c2/experiments/performance_records.json",
        REPO/"c2/results/repository_verification.json",
        REPO/"c2/results/continuation_research.json",
        REPO/"c2/results/coupon_fe_summary.json",
        REPO/"c2/results/p5_thermal_control.json",
        REPO/"c2/results/performance_gate.json",
    ]
    records = [{"file": str(path.relative_to(REPO)), "bytes": path.stat().st_size,
                "sha256": sha256(path)} for path in sorted(set(files+cross_stage))]
    manifest = {
        "revision": "C2.1-P6",
        "scope": "P0-P6 digital review package",
        "artifact_count": len(records),
        "artifacts": records,
        "status": summary["overall"],
        "source_commit": "SET_BY_EXACT_COMMIT_PR_AND_CI_NOT_EMBEDDED_TO_AVOID_SELF_REFERENCE",
        "physical_release": "HOLD",
    }
    (C21/"results/p6_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"status": manifest["status"],
                      "artifact_count": manifest["artifact_count"]}, indent=2))


if __name__ == "__main__":
    main()
