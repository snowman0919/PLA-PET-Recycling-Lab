#!/usr/bin/env python3
"""solid-manifold-openmodelica-v0.4 decision-relevant release checks."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "solid-manifold-openmodelica-v0.4"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def test_revision_and_stale():
    params = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    require(params["revision"] == REV, "baseline revision mismatch")
    require(params["release_class"] == "DIGITAL_FABRICATION_BASELINE", "digital release class mismatch")
    require(params["physical_validation"] == "PHYSICAL_VALIDATION_PENDING", "physical state mismatch")
    current = (
        "README.md", "requirements/system_requirements.md", "requirements/architecture_contract.md",
        "requirements/responsibility_matrix.md", "bom/bom.csv", "bom/cash_budget.csv", "bom/verified_budget.csv",
        "docs/build_manual_ko.typ", "docs/design_report_ko.typ", "docs/digital_release_report_ko.typ",
        "validation/release_checklist.md", "artifacts/manifest.json",
    )
    for rel in current:
        require(REV in (ROOT / rel).read_text(errors="ignore"), f"revision missing: {rel}")
    stale = ["2250 x 500 x 1100", "2510 x 600 x 1350", "two-tower", "Tower A", "Tower B", "6-color classifier", "3-stage release", "external 700 mm rail", "0.1.0-preflight", "0.2.0-undergraduate-mvp"]
    hits = []
    for rel in current:
        text = (ROOT / rel).read_text(errors="ignore")
        for token in stale:
            if token in text:
                hits.append(f"{rel}:{token}")
    require(not hits, "stale architecture: " + ", ".join(hits))


def test_envelope_and_topology():
    params = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    meta = json.loads((ROOT / "cad/generation/assembly_metadata.json").read_text())
    bb = meta["bounding_box_mm"]
    require(all(a <= b for a, b in zip(bb, params["limits"]["hard_envelope_mm"])), f"hard envelope {bb}")
    require(all(a <= b for a, b in zip(bb, params["limits"]["target_envelope_mm"])), f"target envelope {bb}")
    require(bb == [470.0, 700.0, 930.0], f"unexpected design envelope {bb}")
    topology = json.loads((ROOT / "validation/results/solid_topology.json").read_text())
    require(topology["status"] == "PASS" and topology["active_count"] >= 100, "solid topology gate")
    require(topology["review_keepout_count"] == 4, "review keep-out quarantine")
    mesh = json.loads((ROOT / "validation/results/mesh_manifold.json").read_text())
    require(mesh["status"] == "PASS" and len(mesh["meshes"]) == 12, "mesh manifold gate")
    require(mesh["tolerance_coupon"]["status"] == "PASS", "tolerance coupon mesh gate")
    active_token = f"{topology['active_count']}"
    for rel in ("README.md", "docs/digital_release_report_ko.typ", "docs/validation_report_ko.md"):
        require(active_token in (ROOT / rel).read_text(), f"stale active-object count in {rel}")
    for part in mesh["meshes"]:
        require(part["zero_area_triangles"] == 0 and part["nonmanifold_edges"] == 0 and part["connected_components"] == 1, f"bad mesh {part['file']}")


def test_budget():
    rows = list(csv.DictReader((ROOT / "bom/cash_budget.csv").open()))
    target = sum(int(row["planned_cash_krw"]) for row in rows if row["category"] not in {"TOTAL", "CONTINGENCY"})
    reserve = sum(int(row["planned_cash_krw"]) for row in rows if row["category"] == "CONTINGENCY")
    declared_target = int(next(row for row in rows if row["item_id"] == "TARGET_TOTAL")["planned_cash_krw"])
    declared_absolute = int(next(row for row in rows if row["item_id"] == "ABSOLUTE_TOTAL_WITH_RESERVE")["planned_cash_krw"])
    require(target == declared_target and target <= 180000, f"target budget {target}")
    require(target + reserve == declared_absolute and declared_absolute <= 200000, f"absolute budget {declared_absolute}")
    print_allow=int(next(row for row in rows if row["item_id"]=="PRINT-ALLOW")["planned_cash_krw"])
    print_cost=list(csv.DictReader((ROOT/"bom/printed_material_cost.csv").open()))
    require(print_allow==int(next(row for row in print_cost if row["part_id"]=="TOTAL_PLANNING")["estimated_cost_krw"]),"print budget stale from slicer")
    cnc = list(csv.DictReader((ROOT / "bom/cnc_quote_package.csv").open()))
    require(len({row["family_id"] for row in cnc}) <= 8, "unique CNC family cap")
    reuse = list(csv.DictReader((ROOT / "bom/reuse_inventory.csv").open()))
    require(all(row["claimed_zero_cash"] == "false" for row in reuse), "unverified reuse claimed zero cash")
    require((ROOT / "bom/value_engineering_v0.4.md").exists(), "v0.4 VE record missing")
    verified = list(csv.DictReader((ROOT / "bom/verified_budget.csv").open()))
    verified_state = {row["field_or_item"]: row for row in verified if row["budget_state"] == "VERIFIED_PROCUREMENT_BUDGET"}
    require(verified_state["verified_quoted_or_receipted_subtotal"]["status"] == "NOT_ESTABLISHED", "unverified procurement budget incorrectly passed")
    require(verified_state["remaining_margin"]["amount_krw"] == "", "fabricated verified margin")
    budget_tokens = (f"{declared_target:,}", f"{declared_absolute:,}", f"{200000-declared_absolute:,}")
    for rel in (
        "README.md", "requirements/assumptions.md", "bom/value_engineering_v0.4.md",
        "docs/build_manual_ko.typ", "docs/design_report_ko.typ", "docs/digital_release_report_ko.typ",
        "docs/validation_report_ko.md", "validation/completion_audit_v0.4.md",
        "validation/release_checklist.md", "calculations/economics/break_even.md",
    ):
        text = (ROOT / rel).read_text()
        require(all(token in text for token in budget_tokens), f"stale conditional budget in {rel}")


def test_print_package():
    manifest = list(csv.DictReader((ROOT / "exports/print/print_manifest.csv").open()))
    slicing = json.loads((ROOT / "validation/results/slicer_results.json").read_text())
    require(len(manifest) == 12 and slicing["status"] == "PASS", "print/slicer family gate")
    require(abs(slicing["total_mass_g"] - sum(float(row["slicer_mass_total_g"]) for row in manifest)) < 0.02, "manifest/slicer mass mismatch")
    require(slicing["planning_mass_g"] <= 1500, "print planning target")
    require(all("support_volume_cm3" in item and item["support_volume_cm3"] >= 0 for item in slicing["parts"]), "support volume not recorded")
    by_id={item["part_id"]:item for item in slicing["parts"]}
    for row in manifest:
        require(max(float(row[key]) for key in ("x_mm", "y_mm", "z_mm")) <= 210, f"print oversize {row['part_id']}")
        require(row["slicer_status"] == "PASS", f"unsliced {row['part_id']}")
        require(by_id[row["part_id"]]["support_generation_enabled"]==(row["support"].strip().lower()!="no"),f"declared slicer support mismatch {row['part_id']}")
        folder = ROOT / "exports/print" / row["part_id"]
        for key in ("revision", "support_contact", "support_removal", "fastener", "insert_or_nut", "tightening_torque", "edge_distance", "interfaces", "freecad_source", "dimension_sheet"):
            require(row[key].strip(), f"print metadata missing {row['part_id']}:{key}")
        for ext in ("FCStd", "step", "stl", "3mf"):
            require((folder / f"{row['part_id']}.{ext}").stat().st_size > 100, f"missing {row['part_id']}.{ext}")
        require((folder / row["freecad_source"]).stat().st_size > 100, f"missing source {row['part_id']}")
        require((folder / row["dimension_sheet"]).stat().st_size > 100, f"missing dimension sheet {row['part_id']}")
    for item in slicing["parts"]:
        preview=ROOT/item["preview"]
        require(preview.suffix==".svg" and preview.stat().st_size>500 and item["preview_segment_count"]>=3, f"missing first-layer preview {item['part_id']}")
    plates = sorted((ROOT / "exports/print/plate_layouts").glob("plate-*.3mf"))
    require(len(plates) == 12 and all(zipfile.is_zipfile(path) for path in plates), "actual slicer plates")
    require(all("PPR-C" in path.name for path in plates), "stale non-slicer plate present")
    coupon = ROOT / "exports/print/coupons/PPR-TC01"
    for ext in ("FCStd", "step", "stl", "3mf", "py"):
        require((coupon / f"PPR-TC01.{ext}").stat().st_size > 100, f"tolerance coupon missing {ext}")
    require(slicing["tolerance_coupon"]["status"] == "PASS" and not slicing["tolerance_coupon"]["included_in_machine_mass"], "coupon slicing/accounting")
    coupon_preview=ROOT/slicing["tolerance_coupon"]["preview"]
    require(coupon_preview.suffix==".svg" and coupon_preview.stat().st_size>500 and slicing["tolerance_coupon"]["preview_segment_count"]>=3, "coupon first-layer preview")
    slicing_tokens = (
        f"{slicing['total_mass_g']:.2f}",
        f"{slicing['planning_mass_g']:,.2f}",
        f"{slicing['total_time_s']/3600:.1f}",
    )
    for rel in (
        "README.md", "docs/build_manual_ko.typ", "docs/design_report_ko.typ",
        "docs/digital_release_report_ko.typ", "docs/validation_report_ko.md",
    ):
        require(all(token in (ROOT / rel).read_text() for token in slicing_tokens), f"stale slicer result in {rel}")


def test_engineering_modelica_structural_firmware():
    engineering = json.loads((ROOT / "simulation/engineering_summary.json").read_text())
    require(engineering["revision"] == REV and engineering["release_class"] == "DIGITAL_FABRICATION_BASELINE", "engineering revision")
    profiles = engineering["throughput"]["profile_points"]
    require(profiles["PLA"]["rpm"] == 18 and profiles["PET"]["rpm"] == 20, "screw RPM mismatch")
    require(profiles["PLA"]["throughput_nominal_gph"] < 200 and profiles["PET"]["throughput_nominal_gph"] < 200, "200 g/h incorrectly claimed")
    require(engineering["torque_hierarchy"]["strict_order_pass"], "torque hierarchy")
    require(not engineering["drive_calibration"]["hardcoded_universal_current_limit"], "universal current limit reintroduced")
    require(engineering["pet_predry"] == "UNQUALIFIED_EXTERNAL_PROCESS", "PET predry incorrectly qualified")
    clearance=engineering["throughput"]["clearance_sensitivity"]
    require(len(clearance)==6 and {row["radial_clearance_mm"] for row in clearance}=={0.14,0.15,0.16},"flight-tip clearance sweep missing")
    for material in ("PLA","PET"):
        rows=sorted((row for row in clearance if row["material"]==material),key=lambda row:row["radial_clearance_mm"])
        require(rows[0]["predicted_throughput_gph"]>rows[1]["predicted_throughput_gph"]>rows[2]["predicted_throughput_gph"],f"flight-tip leakage direction {material}")

    modelica = json.loads((ROOT / "simulation/openmodelica/results/summary.json").read_text())
    require(modelica["status"] == "PASS" and len(modelica["scenarios"]) == 18, "OpenModelica scenarios")
    require(len(modelica["sensitivity_sweeps"]) == 6 and all(row["status"] == "PASS" for row in modelica["sensitivity_sweeps"]), "OpenModelica sensitivity sweeps")
    modelica_sources = "\n".join(path.read_text() for path in (ROOT / "simulation/openmodelica/PLA_PET_Recycler").rglob("*.mo"))
    for library in ("Modelica.Mechanics.Rotational", "Modelica.Mechanics.Translational", "Modelica.Mechanics.MultiBody"):
        require(library in modelica_sources, f"MSL mechanics library missing {library}")
    envelope = json.loads((ROOT / "simulation/openmodelica/results/dynamic_load_envelope.json").read_text())
    analysis_copy = json.loads((ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json").read_text())
    require(envelope == analysis_copy and envelope["loads"]["peak_cutter_torque_nm"] <= 22, "load-envelope trace")
    loads = envelope["loads"]
    full_system = envelope["full_system"]
    dynamic_tokens = (
        f"{loads['peak_cutter_torque_nm']:.0f}",
        f"{loads['peak_bearing_load_n']/1000:.3f}",
        f"{loads['peak_chain_force_n']/1000:.3f}",
        f"{full_system['peak_anchor_tension_n']/1000:.3f}",
    )
    for rel in ("README.md", "docs/digital_release_report_ko.typ", "docs/validation_report_ko.md"):
        require(all(token in (ROOT / rel).read_text() for token in dynamic_tokens), f"stale dynamic load in {rel}")
    structural = json.loads((ROOT / "analysis/structural/results/structural_screening.json").read_text())
    require(structural["status"] == "PASS" and len(structural["checks"]) == 9, "structural screening")
    require(all(item["status"] == "PASS" for item in structural["calculix"].values()), "CalculiX gate")
    plate=structural["calculix"]["bearing_plate"]; shaft=structural["calculix"]["cutter_shaft"]
    expected_tokens=(f"{plate['max_von_mises_mpa']:.2f}",f"{plate['max_displacement_mm']:.4f}",f"{shaft['max_von_mises_mpa']:.2f}",f"{shaft['max_displacement_mm']:.4f}")
    for rel in ("README.md","docs/digital_release_report_ko.typ"):
        text=(ROOT/rel).read_text()
        require(all(token in text for token in expected_tokens),f"stale CalculiX result in {rel}")

    baseline_hash = hashlib.sha256((ROOT / "cad/parameters/baseline.json").read_bytes()).hexdigest()
    header = (ROOT / "firmware/arduino_mega/src/generated_profiles.h").read_text()
    require(baseline_hash in header and "false}" in header, "firmware config hash/calibration lock")
    require("18.0f" in header and "20.0f" in header, "firmware screw profile")


def test_artifacts_and_release_locks():
    required = [
        "renders/assembly/compact_full_assembly_isometric.png", "renders/review/compact_exploded.png",
        "renders/review/compact_section.png", "renders/review/shredder_fastener_tool_access.png",
        "renders/review/print_orientation.png", "renders/review/support_contact.png",
        "renders/modules/CUT-01_cycloidal_hook_profile.png", "renders/modules/shredder_drive_guard_removed.png",
        "docs/build_manual_ko.pdf", "docs/design_report_ko.pdf", "docs/digital_release_report_ko.pdf",
        "exports/jigs/gate1/gate1_assembly.step", "exports/jigs/gate1/gate1_assembly_ko.pdf",
        "exports/cnc/extruder/rfq_drawing_ko.pdf", "exports/cnc/extruder/inspection_report_template.csv",
        "cad/review_keepouts/review_keepouts.FCStd", "simulation/openmodelica/reports/mechanical_validation_ko.md",
    ]
    for rel in required:
        path = ROOT / rel
        require(path.exists() and path.stat().st_size > 100, f"artifact missing {rel}")
    for rel in ("docs/build_manual_ko.pdf", "docs/design_report_ko.pdf", "docs/digital_release_report_ko.pdf"):
        text = subprocess.run(["pdftotext", str(ROOT / rel), "-"], text=True, capture_output=True, check=True).stdout
        require(REV in text and "PHYSICAL" in text, f"PDF current-state mismatch {rel}")
    state = json.loads((ROOT / "validation/physical_gate_status.json").read_text())
    require(state["gate1_result"] == "NOT_RUN" and state["physical_state"] == "PHYSICAL_NOT_RUN", "physical state")
    require(not state["full_cutter_order_release"] and not state["full_screw_barrel_order_release"], "full order unlocked")
    require(not state["main_promotion_allowed"] and not state["donor_drive_verified"], "main/donor incorrectly released")
    lock_sources = (
        "README.md", "requirements/architecture_contract.md", "docs/build_manual_ko.typ",
        "docs/design_report_ko.typ", "docs/digital_release_report_ko.typ",
        "validation/completion_audit_v0.4.md", "validation/release_checklist.md",
        "exports/jigs/gate1/gate1_release_record_ko.md",
    )
    for rel in lock_sources:
        text = (ROOT / rel).read_text()
        require("Gate-1" in text and ("main" in text or "MAIN" in text), f"Gate-1/main lock missing from {rel}")
    manifest = json.loads((ROOT / "artifacts/manifest.json").read_text())
    require(manifest["revision"] == REV and manifest["release_state"] == "DIGITAL_FABRICATION_BASELINE", "artifact manifest state")
    reproducibility = json.loads((ROOT / "validation/results/artifact_reproducibility.json").read_text())
    require(reproducibility["gate"] == "CLEAN_CLONE_REPRODUCIBILITY" and reproducibility["status"] == "PASS", "artifact reproducibility gate")
    require(not reproducibility["mismatches"], "artifact reproducibility mismatch list")
    require(reproducibility["checked_count"] == manifest["artifact_count"], "artifact reproducibility count")
    require(all(item.get("hash_mode") and item.get("normalized_bytes", 0) > 0 and len(item.get("sha256", "")) == 64 for item in manifest["artifacts"]), "artifact normalized hash schema")
    manifested={item["path"] for item in manifest["artifacts"]}
    canonical=(
        "README.md","cad/README.md","cad/parameters/baseline.json","calculations/run_engineering.py",
        "calculations/flight_tip_clearance_sensitivity.csv","firmware/arduino_mega/src/process_state.cpp",
        "firmware/arduino_mega/src/shredder_control.cpp","electronics/safety_power_topology.md",
        "docs/build_manual_ko.typ","docs/build_manual_ko.pdf","requirements/architecture_contract.md",
        "validation/completion_audit_v0.4.md","validation/results/clean_clone_validation.json",
        "validation/artifact_reproducibility.py","validation/results/artifact_reproducibility.json",
        "artifacts/build_manifest.py","artifacts/manifest_lib.py",
        "exports/print/slicing_previews/plate-01-PPR-C01-first-layer.svg",
    )
    require(all(rel in manifested for rel in canonical),"artifact manifest omits canonical source or evidence")
    for result in ("print_interfaces.json", "full_motion.json", "cutter_phase_sweep.json"):
        data=json.loads((ROOT / "validation/results" / result).read_text())
        require(data["status"] == "PASS", f"independent gate failed {result}")
    phase=json.loads((ROOT / "validation/results/cutter_phase_sweep.json").read_text())
    require(phase["configurations_checked"] == 1080 and phase["minimum_solid_clearance_mm"] >= 0.5, "phase sweep coverage")


def main():
    test_revision_and_stale(); print("PASS REVISION_STALE")
    test_envelope_and_topology(); print("PASS ENVELOPE_SOLID_MESH")
    test_budget(); print("PASS TARGET_ABSOLUTE_BUDGET")
    test_print_package(); print("PASS ACTUAL_SLICER_PACKAGE")
    test_engineering_modelica_structural_firmware(); print("PASS DIGITAL_MECHANICS_SYNC")
    test_artifacts_and_release_locks(); print("PASS ARTIFACTS_PHYSICAL_LOCKS")
    print("SOLID_MANIFOLD_OPENMODELICA_RELEASE_VALIDATION_OK")


if __name__ == "__main__":
    main()
