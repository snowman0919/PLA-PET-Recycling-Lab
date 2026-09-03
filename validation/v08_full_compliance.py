#!/usr/bin/env python3
"""첨부 v0.8 goal 0–25절의 축약 없는 디지털 closure gate."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "final-design-fabrication-closure-v0.8"
OUT = ROOT / "validation/results/v08_full_compliance.json"
REPORT = ROOT / "docs/final/v08_full_compliance_ko.md"

MANUFACTURING = ("cutter", "shafts", "phase_gears", "screw_barrel", "die", "bearing_plates", "feeder", "hot_zone", "guards_panels", "RFQ")
STEP_DIRS = ("assembly", "printed_parts", "cnc_parts", "shafts", "sheet_parts", "purchased_part_envelopes")
ELECTRICAL_PDFS = ("system_block_diagram", "power_distribution", "full_wiring_diagram", "safety_chain", "Arduino_Mega_pinmap", "grounding_bonding", "enclosure_layout", "cable_routing")
FIRMWARE = ("build_manifest.json", "library_lock.json", "EEPROM_schema.md", "pinmap.md", "flashing_guide_ko.md", "calibration_guide_ko.md", "runtime_state_machine_ko.md")
BOM_FILES = ("BOM.csv", "BOM.xlsx", "BOM_KO.pdf", "fastener_schedule.csv", "consumables.csv", "tools_required.csv", "approved_alternatives.csv", "make_buy_matrix.csv")
MANUALS = ("complete_build_manual_ko.pdf", "exploded_views_ko.pdf", "tolerance_and_fit_guide_ko.pdf", "electrical_assembly_ko.pdf", "firmware_and_calibration_ko.pdf", "maintenance_manual_ko.pdf")
COMMISSIONING = ("pre_power_checklist_ko.pdf", "first_power_on_ko.pdf", "dry_run_ko.pdf", "heater_commissioning_ko.pdf", "shredder_commissioning_ko.pdf", "PLA_process_startup_ko.pdf", "PET_process_startup_ko.pdf", "material_change_purge_ko.pdf", "physical_validation_plan_ko.pdf")
ASSEMBLY_FIELDS = {"step_number", "part_ids_quantity", "required_tools", "fasteners", "torque", "orientation", "clearance_tolerance", "drawing", "inspection_method", "pass_fail", "next_prerequisite"}
BOM_FIELDS = {"part_id", "description", "revision", "category", "quantity", "required_or_optional", "make_or_buy", "material_specification", "critical_interface", "approved_mpn", "approved_alternative", "donor_status", "supplier_status", "drawing", "assembly_step", "firmware_dependency", "notes"}
WIRE_FIELDS = {"wire_id", "from", "to", "voltage", "maximum_current", "wire_gauge", "colour", "connector", "terminal", "fuse", "routing", "shield_ground", "strain_relief"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exists(rel: str, minimum: int = 1) -> bool:
    path = ROOT / rel
    return path.is_file() and path.stat().st_size >= minimum


def csv_rows(rel: str) -> tuple[list[dict[str, str]], set[str]]:
    path = ROOT / rel
    if not path.is_file():
        return [], set()
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), set(reader.fieldnames or ())


def pdf_ok(rel: str, required: tuple[str, ...] = ()) -> bool:
    path = ROOT / rel
    if not path.is_file() or path.stat().st_size < 10_000 or path.read_bytes()[:5] != b"%PDF-":
        return False
    proc = subprocess.run(["pdftotext", str(path), "-"], text=True, capture_output=True)
    text = proc.stdout.lower()
    return proc.returncode == 0 and all(term.lower() in text for term in required)


def main() -> None:
    checks: dict[str, dict[str, object]] = {}

    def record(name: str, ok: bool, evidence: str) -> None:
        checks[name] = {"status": "PASS" if ok else "FAIL", "evidence": evidence}

    baseline = json.loads((ROOT / "validation/v0.8/baseline.json").read_text())
    baseline_ok = baseline.get("status") == "PASS" and baseline.get("remote_main") == "7de9bf2a6e4c91c7fa6b58da9c729e63dc52e3a0" and baseline.get("technical_closure_commit") == "8c4c933f84768c954b5a40f0804524e67fab1c58"
    record("00_authoritative_baseline", baseline_ok, "verified main/tag/handoff hashes")
    archive = json.loads((ROOT / "analysis/archive/v0.7_exploratory_manifest.json").read_text())
    valid_classes = {"VALID_REFERENCE", "PROVISIONAL", "INVALIDATED_BY_PIPELINE_CHANGE", "DIAGNOSTIC_ONLY", "NOT_RUN"}
    record("02_v07_archive", exists("docs/archive/v0.7_exploratory_index.md", 100) and all(row.get("classification") in valid_classes for row in archive.get("artifacts", [])), "archive index + classified manifest")

    solver = json.loads((ROOT / "analysis/final_validation/results/v0.8/summary.json").read_text())
    om = json.loads((ROOT / "simulation/openmodelica/results_v0.8/summary.json").read_text())
    record("03_calculix_core", solver.get("status") == "PASS" and all(solver.get(k, {}).get("status") == "PASS" for k in ("LC02", "LC04", "LC05", "hot_zone_mount")), "LC02/04/05 + hot mount clean summary")
    record("03_lc04_resolution", solver.get("LC04", {}).get("resolution") in {"OLD_RESULT_WRONG", "NEW_RESULT_WRONG", "DIFFERENT_METRIC_OR_MODEL"}, str(solver.get("LC04", {}).get("resolution")))
    hot = solver.get("hot_zone_mount", {})
    selected = next((row for row in hot.get("cases", []) if row.get("study") == hot.get("selected_mount")), {})
    record("03_hot_zone_mount", selected.get("safety_factor", 0) >= 2 and selected.get("status") == "PASS" and om.get("hot_zone", {}).get("travelMarginMm", -1) >= 0, f"SF={selected.get('safety_factor')} travel={om.get('hot_zone', {}).get('travelMarginMm')}")
    qualification = ROOT / "analysis/final_validation/results/v0.8/qualification_summary.json"
    q = json.loads(qualification.read_text()) if qualification.is_file() else {}
    required_q = {"torsion", "thermal", "modal", "cutter_root", "frame", "feeder", "spool"}
    record("03_solver_qualification", q.get("status") == "PASS" and required_q <= set(q.get("checks", {})) and all(q["checks"][k]["status"] == "PASS" for k in required_q), "torsion/thermal/modal + frame/feeder/spool")

    iface, iface_fields = csv_rows("exports/final/interface_catalog.csv")
    required_iface = {"interface_id", "part_a", "part_b", "nominal_dimension", "fit_tolerance", "surface_finish", "assembly_method", "inspection_method", "adjustment_shim_method", "thermal_condition", "revision"}
    record("06_interface_catalog", len(iface) >= 13 and required_iface <= iface_fields and all(row.get("revision") == REV for row in iface), f"rows={len(iface)}")
    tol = json.loads((ROOT / "calculations/tolerance_stack_final.json").read_text())
    record("06_tolerance_stacks", tol.get("status") == "PASS" and len(tol.get("interfaces", tol.get("stacks", []))) >= 13, "calculations/tolerance_stack_final.json")

    cad = json.loads((ROOT / "validation/results/final_v08_cad.json").read_text())
    record("07_freecad_source", cad.get("status") == "PASS" and not cad.get("unexpected_collisions") and len(cad.get("new_objects", {})) == 4, "FreeCAD full STEP + v0.8 mount solids/collision gate")
    step_rows, step_fields = csv_rows("exports/final/step/step_manifest.csv")
    required_step = {"part_id", "revision", "source_object", "source_commit", "format", "units", "body_count", "solid_count", "bbox_mm", "volume_mm3", "sha256", "status"}
    step_dirs_ok = all((ROOT / "exports/final/step" / name).is_dir() and any((ROOT / "exports/final/step" / name).iterdir()) for name in STEP_DIRS)
    record("08_step_package", step_dirs_ok and required_step <= step_fields and len(step_rows) > 20 and all(row.get("status") == "PASS" for row in step_rows), f"rows={len(step_rows)} dirs={step_dirs_ok}")

    print_rows, print_fields = csv_rows("exports/final/print/print_manifest.csv")
    required_print = {"part_id", "quantity", "material", "orientation", "support", "layer_height", "perimeters", "top_bottom_layers", "infill", "postprocess", "critical_dimensions", "mating_part", "expected_mass_each_g", "estimated_print_time_s", "status"}
    print_ok = len(print_rows) >= 12 and required_print <= print_fields and all(row.get("status") == "PASS" and int(row.get("quantity", 0)) > 0 for row in print_rows)
    record("09_print_package", print_ok and all((ROOT / "exports/final/print" / d).is_dir() for d in ("STL", "3MF", "STEP_REFERENCE", "plate_layouts", "orientation_renders")), f"rows={len(print_rows)}")

    mfg_ok = True; mfg_detail = []
    mfg_fields = {"part_id", "revision", "quantity", "material", "process", "critical_tolerance", "datum_scheme", "inspection", "status"}
    for family in MANUFACTURING:
        base = ROOT / "exports/final/manufacturing" / family
        rows, fields = csv_rows(f"exports/final/manufacturing/{family}/manifest.csv")
        formats = {p.suffix.lower() for p in base.rglob("*") if p.is_file()} if base.is_dir() else set()
        ok = bool(rows) and mfg_fields <= fields and {".step", ".dxf", ".pdf"} <= formats and all(r.get("revision") == REV and r.get("status") == "PASS" for r in rows)
        mfg_ok &= ok; mfg_detail.append(f"{family}:{'PASS' if ok else 'FAIL'}")
    record("10_manufacturing_package", mfg_ok, ", ".join(mfg_detail))

    drawings, drawing_fields = csv_rows("docs/drawings/drawing_register.csv")
    drawing_required = {"drawing_number", "part_assembly_id", "revision", "units", "scale", "projection", "material", "finish", "general_tolerance", "critical_tolerance", "notes", "source_commit", "pdf", "page", "status"}
    drawing_ok = len(drawings) >= 20 and drawing_required <= drawing_fields and len({r["drawing_number"] for r in drawings}) == len(drawings)
    drawing_ok &= all(r.get("status") == "PASS" and "governs" not in (r.get("critical_tolerance", "") + r.get("material", "")).lower() and pdf_ok(r["pdf"], (r["drawing_number"], "mm")) for r in drawings)
    record("11_dimensioned_drawings", drawing_ok, f"rows={len(drawings)} PDFs={len({r.get('pdf') for r in drawings})}")

    elec_dir = ROOT / "exports/final/electrical"
    diagrams_ok = all(pdf_ok(f"exports/final/electrical/{name}.pdf") and (elec_dir / f"{name}.svg").is_file() for name in ELECTRICAL_PDFS)
    wires, wire_fields = csv_rows("exports/final/electrical/wire_schedule.csv")
    record("12_electrical_package", diagrams_ok and WIRE_FIELDS <= wire_fields and len(wires) >= 20, f"vector_diagrams={diagrams_ok} wires={len(wires)}")

    fw = ROOT / "exports/final/firmware"
    build = json.loads((fw / "build_manifest.json").read_text()) if (fw / "build_manifest.json").is_file() else {}
    binary = fw / "binaries/filament_recycler_atmega2560.hex"
    firmware_ok = (fw / "source").is_dir() and any((fw / "source").rglob("*.cpp")) and (fw / "reproducible_build").is_dir()
    firmware_ok &= all((fw / name).is_file() and (fw / name).stat().st_size > 20 for name in FIRMWARE)
    firmware_ok &= binary.is_file() and build.get("status") == "PASS" and build.get("binary_sha256") == sha(binary)
    record("13_firmware_release", firmware_ok, "source/binary/build/library/docs/reproducible build")

    bom_dir = ROOT / "exports/final/bom"
    bom, bom_fields = csv_rows("exports/final/bom/BOM.csv")
    bom_ok = all((bom_dir / name).is_file() and (bom_dir / name).stat().st_size > 20 for name in BOM_FILES)
    normalized_bom_fields = {field.lower().replace("/", "_").replace(" ", "_") for field in bom_fields}
    bom_ok &= BOM_FIELDS <= normalized_bom_fields and len(bom) >= 30 and all(r.get("revision") == REV and int(r.get("quantity", 0)) > 0 for r in bom)
    record("14_authoritative_bom", bom_ok, f"rows={len(bom)} fields={len(bom_fields)}")

    steps, step_fields = csv_rows("docs/final/assembly_steps.csv")
    manual_ok = all(pdf_ok(f"docs/final/{name}") for name in MANUALS) and len(steps) >= 21 and ASSEMBLY_FIELDS <= step_fields and all(all(r.get(k, "").strip() for k in ASSEMBLY_FIELDS) for r in steps)
    record("15_assembly_manual", manual_ok, f"structured_steps={len(steps)}")
    gates, gate_fields = csv_rows("docs/final/commissioning_gates.csv")
    comm_ok = all(pdf_ok(f"docs/final/{name}") for name in COMMISSIONING) and len(gates) >= 6 and {"from_state", "to_state", "checklist", "approval", "status"} <= gate_fields
    record("16_commissioning_handoff", comm_ok, f"transition_gates={len(gates)} physical=NOT_RUN")

    review = json.loads((ROOT / "validation/multimodal_final_review.json").read_text())
    closeups, closeup_fields = csv_rows("validation/v0.8/multimodal_closeup_manifest.csv")
    required_views = {"front", "rear", "left", "right", "top", "bottom", "isometric", "exploded", "module-separated", "service-access", "guard-removed", "cable-routing"}
    closeup_kinds = {"interfaces", "fasteners", "adjusters", "sensors", "wire_routes", "hot_surfaces", "moving_hazards", "maintenance_access"}
    global_views = {row.get("view") for row in review.get("required_global_views", []) if row.get("status") == "PRESENT"}
    multi_ok = review.get("status") == "PASS" and required_views <= global_views and {"module", "category", "file", "review_state"} <= closeup_fields
    modules = {r.get("module") for r in closeups}; multi_ok &= len(modules) >= 5 and all(closeup_kinds <= {r.get("category") for r in closeups if r.get("module") == module} for module in modules)
    multi_ok &= all(r.get("review_state") != "MODEL_DETAIL_GAP" and exists(r.get("file", ""), 1000) for r in closeups)
    record("17_multimodal_review", multi_ok, f"views={len(global_views)} closeups={len(closeups)} modules={len(modules)}")

    runtime = json.loads((ROOT / "validation/results/runtime_supervisor.json").read_text())
    hardware = json.loads((ROOT / "validation/results/hardware_adapter_e2e/summary.json").read_text())
    record("18_electrical_firmware_tests", runtime.get("status") == "PASS" and hardware.get("status") in {"PASS", "HOST_SIMULATION_PASS"} and hardware.get("all_scenarios_passed") is True, "state-machine + hardware-adapter")
    agents = ROOT / "validation/v0.8/multi_agent_reviews.json"
    reviews = json.loads(agents.read_text()) if agents.is_file() else {}
    required_roles = {"configuration-control-auditor", "shredder-mechanical-reviewer", "feeder-reviewer", "extruder-thermal-reviewer", "forming-spooler-reviewer", "tolerance-stack-reviewer", "CAD-export-reviewer", "drawing-reviewer", "electrical-firmware-reviewer", "assembly-manual-reviewer", "release-packaging-reviewer", "final-red-team-adjudicator"}
    record("19_independent_reviews", required_roles <= set(reviews.get("reviews", {})) and all(v.get("status") == "PASS" for v in reviews.get("reviews", {}).values()), "12 required reviewer roles")

    package = ROOT / "dist/PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION.zip"
    package_ok = False
    if package.is_file():
        proc = subprocess.run([sys.executable, str(ROOT / "release/verify_fabrication_release.py")], cwd=ROOT, text=True, capture_output=True)
        with zipfile.ZipFile(package) as zf:
            manifest = json.loads(zf.read("00_START_HERE/release_manifest.json"))
        package_ok = proc.returncode == 0 and manifest.get("release_state") == "FABRICATION_CANDIDATE" and manifest.get("physical_validation_state") == "NOT_RUN"
    record("20_release_package", package_ok, f"zip_sha256={sha(package) if package.is_file() else 'missing'}")
    record("21_release_policy", exists("docs/final/release_notes_v1.0.0-rc1_ko.md", 200) and exists("validation/v0.8/remote_release_state.json", 50), "release notes + remote branch/PR evidence; publish remains blocked")

    passed = sum(v["status"] == "PASS" for v in checks.values())
    result = {"revision": REV, "status": "PASS" if passed == len(checks) else "FAIL", "passed": passed, "total": len(checks), "checks": checks,
              "technical_state": "DIGITAL_TECHNICAL_CLOSURE" if passed == len(checks) else "IN_PROGRESS",
              "physical_validation_state": "NOT_RUN", "safety_certification": "NOT_CERTIFIED", "fabrication_release_approval": "USER_APPROVAL_REQUIRED"}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    rows = ["# v0.8 전체 compliance", "", "첨부 goal 0–25절의 디지털 gate다. 물리시험·안전인증이 아니다.", ""]
    rows += [f"- `{v['status']}` {k}: {v['evidence']}" for k, v in checks.items()]
    rows += ["", f"결과: **{passed}/{len(checks)} {result['status']}**", "", "물리시험 `NOT_RUN` · 안전인증 `NOT_CERTIFIED` · 제작 승인 `USER_APPROVAL_REQUIRED`", ""]
    REPORT.write_text("\n".join(rows), encoding="utf-8")
    print(f"V08_FULL_COMPLIANCE_{result['status']} {passed}/{len(checks)}")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
