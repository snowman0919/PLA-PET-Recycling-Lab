#!/usr/bin/env python3
"""v0.6.1 safety-orchestration closure의 구현·release 증거를 검증한다."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "safety-orchestration-closure-v0.6.1"
IMPLEMENTATION_STATE = "IMPLEMENTATION_BASELINE"
RELEASE_STATE = "SAFETY_ORCHESTRATION_BASELINE"
SAFETY_REV = REV
ACTUATION_REV = "parallel-actuation-hardening-v0.6.2"
CLOSURE_REV = "technical-blocker-closure-v0.6.2.1"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def test_revision_and_stale():
    params = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    require(params["revision"] == REV and params["release_class"] == IMPLEMENTATION_STATE, "baseline revision/release mismatch")
    require(params["geometry_validation"] == params["fabrication_validation"] == params["virtual_physics_validation"] == "PASS", "validation dimension mismatch")
    require(params["virtual_physics_state"] == "VIRTUAL_PHYSICS_VALIDATED" and params["empirical_state"] == "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN", "release-state mismatch")
    current = (
        "README.md", "requirements/system_requirements.md", "requirements/architecture_contract.md",
        "requirements/responsibility_matrix.md", "requirements/assumptions.md", "bom/bom.csv",
        "bom/cash_budget.csv", "bom/verified_budget.csv", "docs/build_manual_ko.typ",
        "docs/design_report_ko.typ", "docs/digital_release_report_ko.typ",
        "docs/validation_report_ko.md", "validation/release_checklist.md", "artifacts/manifest.json",
    )
    for rel in current:
        text = (ROOT / rel).read_text(errors="ignore")
        require(any(revision in text for revision in (REV, ACTUATION_REV, CLOSURE_REV)),
                f"recognized revision missing: {rel}")
    stale = ["2250 x 500 x 1100", "2510 x 600 x 1350", "two-tower", "Tower A", "Tower B", "6-color classifier", "3-stage release", "external 700 mm rail", "0.1.0-preflight", "0.2.0-undergraduate-mvp"]
    hits = [f"{rel}:{token}" for rel in current for token in stale if token in (ROOT / rel).read_text(errors="ignore")]
    require(not hits, "stale architecture: " + ", ".join(hits))


def test_geometry_budget_and_prints():
    params = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    meta = json.loads((ROOT / "cad/generation/assembly_metadata.json").read_text())
    bb = meta["bounding_box_mm"]
    require(bb == [470.0, 700.0, 930.0], f"unexpected design envelope {bb}")
    require(all(a <= b for a, b in zip(bb, params["limits"]["hard_envelope_mm"])), "hard envelope")
    require(all(a <= b for a, b in zip(bb, params["limits"]["target_envelope_mm"])), "target envelope")
    for name in ("solid_topology", "mesh_manifold", "print_interfaces", "full_motion", "cutter_phase_sweep"):
        require(json.loads((ROOT / "validation/results" / f"{name}.json").read_text())["status"] == "PASS", f"{name} gate")
    collision = json.loads((ROOT / "validation/results/assembly_pairwise_collisions.json").read_text())
    require(collision["status"] == "PASS" and collision["unexpected_count"] == 0, "pairwise collision gate")

    rows = list(csv.DictReader((ROOT / "bom/cash_budget.csv").open()))
    target = int(next(row for row in rows if row["item_id"] == "TARGET_TOTAL")["planned_cash_krw"])
    absolute = int(next(row for row in rows if row["item_id"] == "ABSOLUTE_TOTAL_WITH_RESERVE")["planned_cash_krw"])
    require(target >= 0 and absolute >= target, "invalid informational budget totals")
    policy = json.loads((ROOT / "bom/budget_policy.json").read_text())
    require(policy["price_status"] == "INFORMATIONAL", "price status must be informational")
    require(policy["price_release_blocking"] is False, "price must not block technical release")
    require(policy["procurement_approval_gate"] == "USER_APPROVAL_REQUIRED", "procurement approval gate")
    verified = list(csv.DictReader((ROOT / "bom/verified_budget.csv").open()))
    require(any(r["budget_state"] == "VERIFIED_PROCUREMENT_BUDGET" and r["status"] == "NOT_ESTABLISHED" for r in verified), "unverified budget claimed")

    slicing = json.loads((ROOT / "validation/results/slicer_results.json").read_text())
    require(slicing["status"] == "PASS" and slicing["planning_mass_g"] <= 1500, "print mass target")
    print_rows = list(csv.DictReader((ROOT / "exports/print/print_manifest.csv").open()))
    require(len(print_rows) == 12, "print manifest part count")
    require(all(max(float(p["x_mm"]), float(p["y_mm"]), float(p["z_mm"])) <= 210 for p in print_rows), "print envelope/families")


def test_manufacturing_and_physics():
    for rel in (
        "exports/jigs/gate1/gate1_assembly.FCStd", "exports/jigs/gate1/gate1_assembly.step",
        "exports/jigs/gate1/gate1_assembly.stl", "exports/jigs/gate1/bom.csv",
        "exports/jigs/gate1/gate1_assembly_ko.pdf", "exports/cnc/extruder/rfq_drawing_ko.pdf",
        "exports/cnc/extruder/manufacturing_audit_ko.md", "exports/cnc/extruder/rfq_manifest.csv",
        "exports/drive_interface/interface_contract_ko.md", "exports/thermal/manifest.csv",
    ):
        require((ROOT / rel).exists() and (ROOT / rel).stat().st_size > 100, f"manufacturing artifact missing {rel}")
    require(len(list(csv.DictReader((ROOT / "exports/fabrication/interface_catalog.csv").open()))) == 32, "interface catalog row count")

    engineering = json.loads((ROOT / "simulation/engineering_summary.json").read_text())
    require(engineering["revision"] == REV and engineering["release_class"] == IMPLEMENTATION_STATE, "engineering revision")
    require(engineering["torque_hierarchy"]["strict_order_pass"], "torque hierarchy")
    require(engineering["power"]["status"] == "PASS", "phase power budget")
    require(all(
        row["computed_peak_w"] <= 500 and row["remaining_w_to_psu"] >= 100
        for row in engineering["power"]["states"]
    ), "500 W / 100 W reserve criterion")
    require(engineering["thermocouple_bore"]["selected_status"] == "PASS", "thermocouple bore local screen")
    require(engineering["frame_sensitivity"]["selected"] == "B_LOCAL_2040" and engineering["frame_sensitivity"]["options"][1]["status"] == "PASS", "frame reinforcement")
    require(engineering["cartridge_heater_fit"]["status"] == "PASS_DFM_SCREEN", "cartridge heater fit")
    require(engineering["throughput"]["profile_points"]["PLA"]["throughput_nominal_gph"] < 200, "PLA 200 g/h incorrectly claimed")
    require(engineering["throughput"]["profile_points"]["PET"]["throughput_nominal_gph"] < 200, "PET 200 g/h incorrectly claimed")

    modelica = json.loads((ROOT / "simulation/openmodelica/results/summary.json").read_text())
    require(modelica["revision"] == REV and modelica["status"] == "PASS" and modelica["scenario_count"] >= 74, "mandatory coupled scenarios")
    names = {row["scenario"] for row in modelica["scenarios"]}
    require({
        "ReverseClear", "RetryFailure", "MechanicalFuseTrip", "LeftShaftJam",
        "PhaseGearLoadReversal", "MultiHookProtectiveTrip", "MotorRatedLoadStrict",
        "GaugeFailureControlledPause", "FeederLossDuringExtrusion", "CoolingLossDuringExtrusion",
        "SpoolerPermissionLoss", "GaugeNoise", "GaugeBias", "PullerSlip", "PullerSaturation",
        "OvalityDisturbance", "ReliefOpeningPLA", "ReliefOpeningPET",
        "DynamicPowerShredding", "DynamicPowerPreheating", "DynamicPowerExtrusion", "DynamicPowerCooldown",
    } <= names, "v0.6 critical scenarios absent")
    require(all(row["status"] == "PASS" for row in modelica["scenarios"]), "scenario failure")
    bridge = json.loads((ROOT / "simulation/openmodelica/generated/cad_mass_properties.json").read_text())
    require(bridge["revision"] == REV, "CAD/Modelica bridge revision")
    require(bridge["baseline_sha256"] == hashlib.sha256((ROOT / "cad/parameters/baseline.json").read_bytes()).hexdigest(), "CAD/Modelica bridge hash")
    structural = json.loads((ROOT / "analysis/structural/results/structural_screening.json").read_text())
    require(structural["status"] == "PASS" and all(v["status"] == "PASS" for v in structural["calculix"].values()), "structural screening")
    require(structural["calculix"]["bearing_plate"]["medium_to_fine_displacement_delta_percent"] <= 5, "bearing plate mesh convergence")
    require(structural["calculix"]["cutter_shaft"]["medium_to_fine_displacement_delta_percent"] <= 5, "shaft mesh convergence")
    header = (ROOT / "firmware/arduino_mega/src/generated_profiles.h").read_text()
    require(bridge["baseline_sha256"] in header and "false}" in header, "firmware calibration lock/hash")


def test_implementation_and_cross_solver():
    compile_result = json.loads((ROOT / "validation/results/arduino_mega_compile.json").read_text())
    require(compile_result["revision"] == ACTUATION_REV and compile_result["status"] == "PASS", "Arduino Mega v0.6.2 compile evidence")
    ino = (ROOT / "firmware/arduino_mega/arduino_mega.ino").read_text()
    for token in ("MachineSupervisor", "Max6675Backend", "CoolingFeedbackBackend", "EEPROM", "materialSession", "supervisor.update", "LOCKOUT_CONFIRM_PIN"):
        require(token in ino, f"firmware implementation missing {token}")
    process_state = (ROOT / "firmware/arduino_mega/src/process_state.cpp").read_text()
    require(all(token in process_state for token in ("PURGE_PREHEAT_REQUIRED", "PURGE_READY_CONFIRM_REQUIRED", "PURGE_RUNNING", "SCREEN_CLEAN_REQUIRED", "HOPPER_CLEAN_REQUIRED", "TEMPERATURE_TRANSITION_REQUIRED", "FINAL_CONFIRM_REQUIRED")), "ordered material-session implementation")

    package = ROOT / "exports/fusion_validation"
    model_rows = list(csv.DictReader((package / "model_manifest.csv").open()))
    load_rows = list(csv.DictReader((package / "load_case_manifest.csv").open()))
    require(len(model_rows) == 9 and len(load_rows) == 10, "Fusion neutral package count")
    binding = json.loads((package / "run_binding.json").read_text())
    require(binding["revision"] == REV and binding["fusion_result_state"] == "PENDING_EXTERNAL_EXECUTION", "Fusion binding state")
    source_lock = json.loads((package / "engineering_source_lock.json").read_text())
    require(binding["source_git_sha"] == binding["engineering_source_sha"] == source_lock["engineering_source_sha"], "Fusion engineering source lock")
    require(binding["supersedes_archive_v0_6_sha"] == source_lock["archive_v0_6_sha"], "Fusion v0.6 supersession binding")
    reruns = list(csv.DictReader((package / "rerun_delta_report.csv").open()))
    require(len(reruns) == 10 and all(row["rerun_required"] == "true" and row["result_state"] == "PENDING_EXTERNAL_EXECUTION" for row in reruns), "Fusion LC01-LC10 rerun delta")
    require(binding["model_manifest_sha256"] == hashlib.sha256((package / "model_manifest.csv").read_bytes()).hexdigest(), "model manifest binding")
    require(binding["load_case_manifest_sha256"] == hashlib.sha256((package / "load_case_manifest.csv").read_bytes()).hexdigest(), "load manifest binding")
    for row in model_rows:
        step = package / "geometry" / row["file"]
        require(step.stat().st_size > 4000 and row["step_sha256"] == hashlib.sha256(step.read_bytes()).hexdigest(), f"STEP binding {row['file']}")
    fusion_results = json.loads((package / "results/fusion_result_manifest.json").read_text())
    require(fusion_results["status"] == "PENDING" and not fusion_results["runs"], "external Fusion result falsely claimed")
    correlation = list(csv.DictReader((ROOT / "analysis/cross_solver/correlation_matrix.csv").open()))
    require(correlation and all(row["status"] == "PENDING" for row in correlation), "cross-solver pending boundary")

    inventory = list(csv.DictReader((ROOT / "bom/inventory_evidence_v0.6.csv").open()))
    rfqs = list(csv.DictReader((ROOT / "bom/rfq_register_v0.6.csv").open()))
    require(inventory and all(row["verification_state"] == "USER_INSPECTION_REQUIRED" and not row["claimed_available_quantity"] for row in inventory), "physical inventory falsely established")
    require(rfqs and all(row["status"] == "RFP_READY_NOT_SENT" and not row["quoted_total_krw"] for row in rfqs), "RFQ falsely claimed")


def test_artifacts_and_locks():
    state = json.loads((ROOT / "validation/physical_gate_status.json").read_text())
    require(state["optional_gate1_result"] == "NOT_RUN" and state["empirical_state"] == "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN", "empirical state")
    require(state["design_release_gate"] == "PASS" and state["safety_orchestration_release_gate"] == "PASS" and state["main_promotion_allowed"], "safety orchestration release gate")
    require(state["procurement_approval_gate"] == state["commissioning_gate"] == "USER_APPROVAL_REQUIRED", "approval gates")
    require(not state["full_cutter_order_release"] and not state["full_screw_barrel_order_release"], "full order unlocked")
    require(not state["donor_drive_verified"], "donor incorrectly verified")
    readiness = json.loads((ROOT / "validation/results/gate1_readiness.json").read_text())
    require(readiness["revision"] == REV and readiness["status"] == "PASS" and readiness["empirical_result"] == "OPTIONAL_NOT_RUN", "optional Gate-1 readiness")
    require(not any(readiness["procurement_locks"].values()), "procurement lock opened")
    require(readiness["main_promotion_allowed"], "optional Gate-1 incorrectly gates main")

    manifest = json.loads((ROOT / "artifacts/manifest.json").read_text())
    require(manifest["revision"] == REV and manifest["release_state"] == RELEASE_STATE and
            manifest["implementation_state"] == IMPLEMENTATION_STATE, "artifact manifest")
    require(
        manifest["geometry_validation"] == manifest["fabrication_validation"] == manifest["virtual_physics_validation"] == "PASS"
        and manifest["virtual_physics_state"] == "VIRTUAL_PHYSICS_VALIDATED"
        and manifest["empirical_state"] == "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN",
        "artifact manifest release dimensions",
    )
    reproducibility = json.loads((ROOT / "validation/results/artifact_reproducibility.json").read_text())
    require(reproducibility["revision"] == REV and reproducibility["status"] == "PASS" and not reproducibility["mismatches"], "reproducibility")
    require(reproducibility["checked_count"] == manifest["artifact_count"], "manifest count")
    for rel in ("docs/build_manual_ko.pdf", "docs/design_report_ko.pdf", "docs/digital_release_report_ko.pdf"):
        text = subprocess.run(["pdftotext", str(ROOT / rel), "-"], text=True, capture_output=True, check=True).stdout
        require(
            CLOSURE_REV in text
            and "TECHNICAL_CLOSURE_BASELINE" in text
            and "IMPLEMENTATION_BASELINE" in text
            and "VIRTUAL_PHYSICS_VALIDATED" in text
            and "CROSS_SOLVER_VALIDATION_DEFERRED" in text
            and "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN" in text
            and "Gate-1" in text,
            f"PDF current-state mismatch {rel}",
        )


def test_safety_orchestration_closure():
    for name in ("orchestration_contract", "controller_contract", "red_team_orchestration"):
        result = json.loads((ROOT / "validation/results" / f"{name}.json").read_text())
        require(
            result.get("revision") == SAFETY_REV and result.get("status") == "PASS",
            f"v0.6.1 safety evidence missing/stale: {name}",
        )
    for name in ("runtime_supervisor", "arduino_mega_compile"):
        result = json.loads((ROOT / "validation/results" / f"{name}.json").read_text())
        require(
            result.get("revision") == ACTUATION_REV and result.get("status") == "PASS",
            f"v0.6.2 production actuation evidence missing/stale: {name}",
        )
    runtime = json.loads((ROOT / "validation/results/runtime_supervisor.json").read_text())
    require(runtime["scenario_count"] >= 43 and runtime["trace_count"] >= 100, "runtime coverage regression")
    require(runtime["invariant_failure_count"] == 0, "runtime invariant failure")
    require(runtime["bounded_sequence"] == {
        "fixed_seeds": 4, "maximum_events_per_seed": 64, "status": "PASS",
    }, "bounded sequence evidence drift")
    require(runtime["purge_revolution_evidence"] == "ACTUAL_SCREW_TACH_MEASURED_REVOLUTIONS", "actual purge tach evidence missing")
    require(runtime["purge_operator_sequence"] == "approvePurgeFeed_then_independent_waste_path_confirmation", "purge operator sequence evidence drift")
    red_team = json.loads((ROOT / "validation/results/red_team_orchestration.json").read_text())
    require(red_team["mutation_count"] >= 14, "mandatory red-team mutation count")
    require(all(value == "FAIL_DETECTED" for value in red_team["mutations"].values()), "red-team false PASS")


def main():
    test_revision_and_stale(); print("PASS CURRENT_REVISION_COHERENT")
    test_geometry_budget_and_prints(); print("PASS GEOMETRY_BUDGET_PRINT")
    test_manufacturing_and_physics(); print("PASS MANUFACTURING_COUPLED_PHYSICS")
    test_implementation_and_cross_solver(); print("PASS IMPLEMENTATION_CROSS_SOLVER_BOUNDARY")
    test_artifacts_and_locks(); print("PASS ARTIFACTS_PHYSICAL_LOCKS")
    test_safety_orchestration_closure(); print("PASS SAFETY_ORCHESTRATION_CLOSURE")
    print("SAFETY_ORCHESTRATION_V061_RELEASE_OK")


if __name__ == "__main__":
    main()
