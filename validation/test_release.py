#!/usr/bin/env python3
"""implementation-crosssolver-v0.6 mandatory digital release checks."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "implementation-crosssolver-v0.6"
RELEASE = "IMPLEMENTATION_BASELINE"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def test_revision_and_stale():
    params = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    require(params["revision"] == REV and params["release_class"] == RELEASE, "baseline revision/release mismatch")
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
        require(REV in (ROOT / rel).read_text(errors="ignore"), f"revision missing: {rel}")
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
    require(target <= 180000 and absolute <= 200000, "cash cap")
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
    require(engineering["revision"] == REV and engineering["release_class"] == RELEASE, "engineering revision")
    require(engineering["torque_hierarchy"]["strict_order_pass"], "torque hierarchy")
    require(engineering["power"]["status"] == "PASS", "phase power budget")
    require(all(row["peak_w"] <= 500 and row["remaining_w_to_psu"] >= 100 for row in engineering["power"]["states"]), "500 W / 100 W reserve criterion")
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
    require(compile_result["revision"] == REV and compile_result["status"] == "PASS", "Arduino Mega compile evidence")
    ino = (ROOT / "firmware/arduino_mega/arduino_mega.ino").read_text()
    for token in ("Max6675Backend", "EEPROM", "materialSession", "heaterController", "gaugeController", "LOCKOUT_CONFIRM_PIN"):
        require(token in ino, f"firmware implementation missing {token}")
    process_state = (ROOT / "firmware/arduino_mega/src/process_state.cpp").read_text()
    require(all(token in process_state for token in ("PURGE_REQUIRED", "SCREEN_CLEAN_REQUIRED", "HOPPER_CLEAN_REQUIRED", "TEMPERATURE_TRANSITION_REQUIRED", "FINAL_CONFIRM_REQUIRED")), "ordered material-session implementation")

    package = ROOT / "exports/fusion_validation"
    model_rows = list(csv.DictReader((package / "model_manifest.csv").open()))
    load_rows = list(csv.DictReader((package / "load_case_manifest.csv").open()))
    require(len(model_rows) == 9 and len(load_rows) == 10, "Fusion neutral package count")
    binding = json.loads((package / "run_binding.json").read_text())
    require(binding["revision"] == REV and binding["fusion_result_state"] == "PENDING_EXTERNAL_EXECUTION", "Fusion binding state")
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
    require(state["design_release_gate"] == "PASS" and state["main_promotion_allowed"], "design release gate")
    require(state["procurement_approval_gate"] == state["commissioning_gate"] == "USER_APPROVAL_REQUIRED", "approval gates")
    require(not state["full_cutter_order_release"] and not state["full_screw_barrel_order_release"], "full order unlocked")
    require(not state["donor_drive_verified"], "donor incorrectly verified")
    readiness = json.loads((ROOT / "validation/results/gate1_readiness.json").read_text())
    require(readiness["revision"] == REV and readiness["status"] == "PASS" and readiness["empirical_result"] == "OPTIONAL_NOT_RUN", "optional Gate-1 readiness")
    require(not any(readiness["procurement_locks"].values()), "procurement lock opened")
    require(readiness["main_promotion_allowed"], "optional Gate-1 incorrectly gates main")

    manifest = json.loads((ROOT / "artifacts/manifest.json").read_text())
    require(manifest["revision"] == REV and manifest["release_state"] == RELEASE, "artifact manifest")
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
            REV in text
            and "IMPLEMENTATION_BASELINE" in text
            and "VIRTUAL_PHYSICS_VALIDATED" in text
            and "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN" in text
            and "Gate-1" in text,
            f"PDF current-state mismatch {rel}",
        )


def main():
    test_revision_and_stale(); print("PASS CURRENT_REVISION_COHERENT")
    test_geometry_budget_and_prints(); print("PASS GEOMETRY_BUDGET_PRINT")
    test_manufacturing_and_physics(); print("PASS MANUFACTURING_COUPLED_PHYSICS")
    test_implementation_and_cross_solver(); print("PASS IMPLEMENTATION_CROSS_SOLVER_BOUNDARY")
    test_artifacts_and_locks(); print("PASS ARTIFACTS_PHYSICAL_LOCKS")
    print("IMPLEMENTATION_CROSSSOLVER_V06_RELEASE_OK")


if __name__ == "__main__":
    main()
