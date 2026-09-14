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
sys.path.insert(0, str(ROOT / "release"))
from firmware_evidence import firmware_evidence_current
from publication_policy import publication_policy_current
sys.path.insert(0, str(ROOT / "validation"))
from evidence_freshness import audit_evidence
REV = "final-design-fabrication-closure-v0.8"
OUT = ROOT / "validation/results/v08_full_compliance.json"
REPORT = ROOT / "docs/final/v08_full_compliance_ko.md"
CURRENT_REPORT = ROOT / "docs/final/v08_closure_report_ko.md"

MANUFACTURING = ("cutter", "shafts", "phase_gears", "screw_barrel", "die", "bearing_plates", "feeder", "hot_zone", "guards_panels", "drive_ggm", "RFQ")
STEP_DIRS = ("assembly", "printed_parts", "cnc_parts", "shafts", "sheet_parts", "purchased_part_envelopes")
ELECTRICAL_PDFS = ("system_block_diagram", "power_distribution", "full_wiring_diagram", "safety_chain", "Arduino_Mega_pinmap", "grounding_bonding", "enclosure_layout", "cable_routing")
FIRMWARE = ("build_manifest.json", "library_lock.json", "EEPROM_schema.md", "pinmap.md", "flashing_guide_ko.md", "calibration_guide_ko.md", "runtime_state_machine_ko.md")
BOM_FILES = ("BOM.csv", "BOM.xlsx", "BOM_KO.pdf", "fastener_schedule.csv", "consumables.csv", "tools_required.csv", "approved_alternatives.csv", "make_buy_matrix.csv")
PRINT_BINDINGS = (("stl_file", "sha256_stl"), ("three_mf_file", "sha256_3mf"),
                  ("step_reference_file", "sha256_step"), ("plate_layout_file", "sha256_plate"),
                  ("orientation_render", "sha256_orientation_render"))
MANUALS = ("complete_build_manual_ko.pdf", "exploded_views_ko.pdf", "tolerance_and_fit_guide_ko.pdf", "electrical_assembly_ko.pdf", "firmware_and_calibration_ko.pdf", "maintenance_manual_ko.pdf")
COMMISSIONING = ("pre_power_checklist_ko.pdf", "first_power_on_ko.pdf", "dry_run_ko.pdf", "heater_commissioning_ko.pdf", "shredder_commissioning_ko.pdf", "PLA_process_startup_ko.pdf", "PET_process_startup_ko.pdf", "material_change_purge_ko.pdf", "physical_validation_plan_ko.pdf")
ASSEMBLY_FIELDS = {"step_number", "part_ids_quantity", "required_tools", "fasteners", "torque", "orientation", "clearance_tolerance", "drawing", "inspection_method", "pass_fail", "next_prerequisite"}
BOM_FIELDS = {"part_id", "description", "revision", "category", "quantity", "required_or_optional", "make_or_buy", "material_specification", "critical_interface", "approved_mpn", "approved_alternative", "donor_status", "supplier_status", "drawing", "assembly_step", "firmware_dependency", "notes"}
WIRE_FIELDS = {"wire_id", "from", "to", "voltage", "maximum_current", "wire_gauge", "colour", "connector", "terminal", "fuse", "routing", "shield_ground", "strain_relief"}
SECTION_BINDINGS = {
    "00": ("00_authoritative_baseline",), "01": ("$scope_decision",), "02": ("02_v07_archive",),
    "03": ("03_calculix_core", "03_lc04_resolution", "03_hot_zone_mount", "03_solver_qualification"),
    "04": ("$architecture_freeze",),
    "05": ("05_v08_motion_dynamics", "05_loaded_phase_centre", "07_freecad_source", "10_manufacturing_package"),
    "06": ("06_interface_catalog", "06_tolerance_stacks"), "07": ("07_freecad_source",),
    "08": ("08_step_package",), "09": ("09_print_package",), "10": ("10_manufacturing_package",),
    "11": ("11_dimensioned_drawings",), "12": ("12_electrical_package",),
    "13": ("13_firmware_release",), "14": ("14_authoritative_bom",),
    "15": ("15_assembly_manual",), "16": ("16_commissioning_handoff",),
    "17": ("17_multimodal_review",),
    "18": ("03_calculix_core", "03_solver_qualification", "05_v08_motion_dynamics", "05_loaded_phase_centre",
           "06_tolerance_stacks", "07_freecad_source", "08_step_package", "09_print_package",
           "12_electrical_package", "13_firmware_release", "15_assembly_manual", "20_release_package"),
    "19": ("19_independent_reviews",), "20": ("20_release_package",), "21": ("21_release_policy",),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manufacturing_files_current(base: Path, row: dict,
                                bindings=(("step_file", "sha256_step"), ("dxf_file", "sha256_dxf"), ("drawing_pdf", "sha256_pdf"))) -> bool:
    for field, digest in bindings:
        name = row.get(field, "")
        path = (base / name).resolve()
        if not name or not path.is_relative_to(base.resolve()) or not path.is_file():
            return False
        if not path.stat().st_size or sha(path) != row.get(digest):
            return False
    return True


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


def audit_sections(checks: dict[str, dict[str, object]], extras: dict[str, bool]) -> dict[str, dict[str, object]]:
    states = {name: row.get("status") == "PASS" for name, row in checks.items()} | extras
    bindings = SECTION_BINDINGS | {
        "22": tuple(checks),
        "23": tuple(checks) + ("$final_states",),
        "24": tuple(checks) + ("$execution_complete",),
        "25": ("$final_report",),
    }
    result = {}
    for section in (f"{number:02d}" for number in range(26)):
        requirements = bindings.get(section, ())
        covered = bool(requirements) and all(name in states for name in requirements)
        result[section] = {"covered": covered, "status": "PASS" if covered and all(states[name] for name in requirements) else "FAIL",
                           "requirements": list(requirements)}
    return result


def main() -> None:
    technical_only = "--technical-only" in sys.argv[1:]
    checks: dict[str, dict[str, object]] = {}
    freshness_audits = {}

    def transitive_current(report: str, required=()) -> bool:
        audit = audit_evidence(ROOT, report, required)
        freshness_audits[report] = audit
        return audit["status"] == "CURRENT"

    def record(name: str, ok: bool, evidence: str) -> None:
        checks[name] = {"status": "PASS" if ok else "FAIL", "evidence": evidence}

    baseline = json.loads((ROOT / "validation/v0.8/baseline.json").read_text())
    baseline_ok = baseline.get("status") == "PASS" and baseline.get("remote_main") == "7de9bf2a6e4c91c7fa6b58da9c729e63dc52e3a0" and baseline.get("technical_closure_commit") == "8c4c933f84768c954b5a40f0804524e67fab1c58"
    record("00_authoritative_baseline", baseline_ok, "verified main/tag/handoff hashes")
    archive = json.loads((ROOT / "analysis/archive/v0.7_exploratory_manifest.json").read_text())
    valid_classes = {"VALID_REFERENCE", "PROVISIONAL", "INVALIDATED_BY_PIPELINE_CHANGE", "DIAGNOSTIC_ONLY", "NOT_RUN"}
    archive_entries = archive.get("entries", [])
    record("02_v07_archive", exists("docs/archive/v0.7_exploratory_index.md", 100) and bool(archive_entries) and all(row.get("classification") in valid_classes for row in archive_entries), "archive index + classified manifest")

    solver = json.loads((ROOT / "analysis/final_validation/results/v0.8/summary.json").read_text())
    om = json.loads((ROOT / "simulation/openmodelica/results_v0.8/summary.json").read_text())
    solver_current = solver.get("pipeline_source_sha256") == sha(ROOT / "analysis/final_validation/run_calculix_v08.py")
    solver_dependencies = solver.get("dependencies_sha256", {})
    solver_current &= bool(solver_dependencies) and all(exists(p) and sha(ROOT/p) == digest for p,digest in solver_dependencies.items())
    solver_current &= transitive_current("analysis/final_validation/results/v0.8/summary.json", ("analysis/final_validation/run_calculix_v08.py", "cad/freecad/compact/geometry.py"))
    record("03_calculix_core", solver_current and solver.get("status") == "PASS" and all(solver.get(k, {}).get("status") == "PASS" for k in ("LC02", "LC04", "LC05", "hot_zone_mount")), f"LC02/04/05 + hot mount; source_current={solver_current}")
    record("03_lc04_resolution", solver.get("LC04", {}).get("resolution") in {"OLD_RESULT_WRONG", "NEW_RESULT_WRONG", "DIFFERENT_METRIC_OR_MODEL"}, str(solver.get("LC04", {}).get("resolution")))
    hot = solver.get("hot_zone_mount", {})
    selected = next((row for row in hot.get("cases", []) if row.get("study") == hot.get("selected_mount")), {})
    hot_studies = {row.get("study"): row for row in hot.get("cases", [])}
    required_hot = {"A_FULLY_FIXED", "B_ONE_AXIAL_DATUM_SLIDING", "C_RADIAL_CONTROLLED_AXIAL_EXPANSION", "D_BOUNDED_FRAME_SPRING", "E_THERMAL_ONLY", "F_PRESSURE_ONLY", "G_PET_THERMAL_BLOCKED_DIE_PRESSURE"}
    hot_qualified = hot.get("qualification_checks", {})
    sensor_local_path = ROOT / "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json"
    sensor_local = json.loads(sensor_local_path.read_text()) if sensor_local_path.is_file() else {}
    sensor_local_sources = sensor_local.get("source_sha256", {})
    sensor_local_current = bool(sensor_local_sources) and all(exists(path) and sha(ROOT / path) == digest for path, digest in sensor_local_sources.items())
    sensor_local_current &= transitive_current("analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json")
    required_hot_checks = {"scm440_temperature_dependent_material_qualified", "sensor_bore_local_stress_qualified", "die_joint_qualified", "local_temperature_gradient_qualified"}
    record("03_hot_zone_mount", solver_current and sensor_local_current and hot.get("status") == "PASS" and required_hot_checks <= set(hot_qualified) and all(hot_qualified[name] is True for name in required_hot_checks) and selected.get("safety_factor", 0) >= 2 and required_hot <= set(hot_studies) and all(hot_studies[name].get("status") == "PASS" for name in required_hot - {"A_FULLY_FIXED"}) and om.get("hot_zone", {}).get("travelMarginMm", -1) >= 0, f"A–G={len(hot_studies)} qualified={hot_qualified} selected_SF={selected.get('safety_factor')} sensor_local_current={sensor_local_current} sensor_thermal_pressure_screen={sensor_local.get('status')}/{sensor_local.get('medium_to_fine_regional_stress_change')}")
    dynamics = om.get("spooler_traverse_dynamics", {})
    required_dynamics = {"SpoolerTraverseEmptyToFull", "SpoolerPETOneKg", "SpoolerFullRadiusPLA", "SpoolerFullRadiusPET"}
    om_hashes = om.get("source_sha256", {})
    om_current = bool(om_hashes) and all(exists(p) and sha(ROOT/p) == digest for p,digest in om_hashes.items())
    om_current &= transitive_current("simulation/openmodelica/results_v0.8/summary.json")
    jam_checks = om.get("jam", {}).get("checks", {})
    record("05_v08_motion_dynamics", om_current and om.get("status") == "PASS" and bool(jam_checks) and all(v is True for v in jam_checks.values()) and required_dynamics <= set(dynamics) and all(dynamics[name].get("status") == "PASS" and bool(dynamics[name].get("checks")) and all(v is True for v in dynamics[name]["checks"].values()) for name in required_dynamics), f"v0.8 parameter-bound mechanical/control surrogate; source_current={om_current}; not firmware/physical validation")
    phase = json.loads((ROOT / "validation/results/cutter_phase_sweep.json").read_text())
    loaded_path = ROOT / "analysis/final_validation/results/v0.8/loaded_phase.json"
    loaded = json.loads(loaded_path.read_text()) if loaded_path.is_file() else {}
    loaded_current = loaded.get("source_sha256") == sha(ROOT / "analysis/final_validation/run_phase_load_v08.py") and loaded.get("geometry_source_sha256") == sha(ROOT / "cad/freecad/compact/geometry.py")
    loaded_dependencies = loaded.get("dependencies_sha256", {})
    loaded_current &= bool(loaded_dependencies) and all(exists(p) and sha(ROOT/p) == digest for p,digest in loaded_dependencies.items())
    loaded_current &= transitive_current("analysis/final_validation/results/v0.8/loaded_phase.json")
    key_path = ROOT / "analysis/final_validation/results/v0.8/phase_clocking_release.json"
    key_check = json.loads(key_path.read_text()) if key_path.is_file() else {}
    key_sources = key_check.get("source_sha256", {})
    key_current = bool(key_sources) and all(exists(path) and sha(ROOT / path) == digest for path, digest in key_sources.items())
    key_current &= transitive_current("analysis/final_validation/results/v0.8/phase_clocking_release.json")
    key_clocking_ok = key_current and key_check.get("status") == "PASS"
    phase25_path = ROOT / "analysis/final_validation/results/v0.8/phase_path_25_qualification.json"
    phase25 = json.loads(phase25_path.read_text()) if phase25_path.is_file() else {}
    phase25_sources = phase25.get("source_sha256", {})
    phase25_current = bool(phase25_sources) and all(exists(path) and sha(ROOT / path) == digest for path, digest in phase25_sources.items())
    phase25_current &= transitive_current("analysis/final_validation/results/v0.8/phase_path_25_qualification.json")
    required_phase_checks = {"mesh_convergence", "positive_loaded_backlash", "backlash_below_one_degree", "frame_and_bearing_compliance_qualified", "torsional_phase_compliance_qualified"}
    phase_checks = loaded.get("checks", {})
    record("05_loaded_phase_centre", phase.get("revision") == REV and phase.get("status") == "PASS" and loaded_current and loaded.get("status") == "PASS" and key_clocking_ok and phase25_current and required_phase_checks <= set(phase_checks) and all(phase_checks[name] is True for name in required_phase_checks), f"source_current={loaded_current} loaded={loaded.get('status')} key_source_current={key_current} released_key_clocking={key_check.get('status')} candidate25_current={phase25_current} candidate25={phase25.get('status')}/{phase25.get('combined_worst_angle_deg')}deg checks={phase_checks}")
    qualification = ROOT / "analysis/final_validation/results/v0.8/qualification_summary.json"
    q = json.loads(qualification.read_text()) if qualification.is_file() else {}
    required_q = {"torsion", "thermal", "modal", "cutter_root", "frame", "feeder", "spool"}
    q_sources = q.get("source_sha256", {})
    q_required_sources = {"analysis/final_validation/run_qualification_v08.py", "analysis/load_cases/openmodelica_dynamic_envelope.json"}
    q_current = q_required_sources <= set(q_sources) and all(exists(p) and sha(ROOT/p) == digest for p,digest in q_sources.items())
    q_current &= transitive_current("analysis/final_validation/results/v0.8/qualification_summary.json")
    record("03_solver_qualification", q_current and q.get("status") == "PASS" and required_q <= set(q.get("checks", {})) and all(q["checks"][k]["status"] == "PASS" for k in required_q), f"torsion/thermal/modal + component screens; source_current={q_current}; not complete assembly qualification")

    iface, iface_fields = csv_rows("exports/final/interface_catalog.csv")
    required_iface = {"interface_id", "part_a", "part_b", "nominal_dimension", "fit_tolerance", "surface_finish", "assembly_method", "inspection_method", "adjustment_shim_method", "thermal_condition", "revision"}
    tol = json.loads((ROOT / "calculations/tolerance_stack_final.json").read_text())
    record("06_interface_catalog", tol.get("coverage", {}).get("status") == "PASS" and len(iface) >= 32 and required_iface <= iface_fields and all(row.get("revision") == REV and row.get("status") == "PASS" for row in iface), f"single controlling rows={len(iface)}; exhaustive_coverage={tol.get('coverage', {}).get('status')}")
    record("06_tolerance_stacks", tol.get("status") == "PASS" and len(tol.get("interfaces", tol.get("stacks", []))) >= 13, "calculations/tolerance_stack_final.json")

    cad = json.loads((ROOT / "validation/results/final_v08_cad.json").read_text())
    cad_sources = cad.get("source_sha256", {})
    cad_current = bool(cad_sources) and all(exists(p) and sha(ROOT / p) == digest for p, digest in cad_sources.items())
    cad_current &= transitive_current("validation/results/final_v08_cad.json")
    contact = cad.get("rear_axial_load_path", {}).get("necessary_contact_check")
    retainer_path = ROOT / "analysis/final_validation/results/v0.8/axial_retainer_qualification.json"
    retainer = json.loads(retainer_path.read_text()) if retainer_path.is_file() else {}
    retainer_sources = retainer.get("source_sha256", {})
    retainer_current = bool(retainer_sources) and all(exists(path) and sha(ROOT / path) == digest for path, digest in retainer_sources.items())
    retainer_current &= transitive_current("analysis/final_validation/results/v0.8/axial_retainer_qualification.json")
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        frame_spec = spec_from_file_location('ppr_frame_binding', ROOT/'validation/physical_v08/frame_release.py')
        frame_module = module_from_spec(frame_spec)
        frame_spec.loader.exec_module(frame_module)
        integrated_frame = frame_module.validate(ROOT)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        integrated_frame = {'status': 'FAIL', 'reason': str(error)}
    frame_current = (integrated_frame.get('status') == 'FRAME_CUTLIST_BINDING_PASS'
                     and integrated_frame.get('cut_authorization') is False)
    record("07_freecad_source", cad_current and retainer_current and frame_current and contact == "PASS" and cad.get("status") == "PASS" and not cad.get("unexpected_collisions") and len(cad.get("new_objects", {})) == 7, f"Integrated GGM frame={integrated_frame}; FreeCAD mount solids/collision/contact gate; source_current={cad_current}; axial_contact={contact}; candidate_current={retainer_current} candidate={retainer.get('status')}/{retainer.get('numeric_screen')}")
    step_rows, step_fields = csv_rows("exports/final/step/step_manifest.csv")
    required_step = {"part_id", "revision", "source_object", "source_commit", "file", "format", "units", "body_count", "solid_count", "bbox_mm", "volume_mm3", "sha256", "status"}
    step_dirs_ok = all((ROOT / "exports/final/step" / name).is_dir() and any((ROOT / "exports/final/step" / name).iterdir()) for name in STEP_DIRS)
    step_files_current = all(manufacturing_files_current(ROOT / "exports/final/step", row, (("file", "sha256"),)) for row in step_rows)
    record("08_step_package", step_dirs_ok and required_step <= step_fields and len(step_rows) > 20 and step_files_current and all(row.get("status") == "PASS" for row in step_rows), f"rows={len(step_rows)} dirs={step_dirs_ok} files_current={step_files_current}; file integrity only, not fabrication qualification")

    print_rows, print_fields = csv_rows("exports/final/print/print_manifest.csv")
    required_print = {"part_id", "quantity", "material", "orientation", "support", "layer_height", "perimeters", "top_bottom_layers", "infill", "postprocess", "critical_dimensions", "mating_part", "expected_mass_each_g", "estimated_print_time_s", "status"}
    print_ok = len(print_rows) >= 12 and required_print <= print_fields and all(row.get("status") == "PASS" and int(row.get("quantity", 0)) > 0 for row in print_rows)
    print_current = bool(print_rows) and all(manufacturing_files_current(ROOT / "exports/final/print", row, PRINT_BINDINGS) for row in print_rows)
    record("09_print_package", print_ok and print_current and all((ROOT / "exports/final/print" / d).is_dir() for d in ("STL", "3MF", "STEP_REFERENCE", "plate_layouts", "orientation_renders")), f"rows={len(print_rows)} files_current={print_current}; physical fit NOT_RUN")

    mfg_ok = True; mfg_detail = []
    mfg_fields = {"part_id", "revision", "quantity", "material", "process", "critical_tolerance", "datum_scheme", "inspection", "status"}
    for family in MANUFACTURING:
        base = ROOT / "exports/final/manufacturing" / family
        rows, fields = csv_rows(f"exports/final/manufacturing/{family}/manifest.csv")
        formats = {p.suffix.lower() for p in base.rglob("*") if p.is_file()} if base.is_dir() else set()
        ok = bool(rows) and mfg_fields <= fields and {".step", ".dxf", ".pdf"} <= formats and all(r.get("revision") == REV and r.get("status") == "PASS" for r in rows)
        ok &= all(manufacturing_files_current(base, row) for row in rows)
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
    firmware_ok = (fw / "source").is_dir() and any((fw / "source").rglob("*.cpp")) and (fw / "reproducible_build").is_dir()
    firmware_ok &= all((fw / name).is_file() and (fw / name).stat().st_size > 20 for name in FIRMWARE)
    firmware_ok &= firmware_evidence_current(ROOT)
    record("13_firmware_release", firmware_ok, "source/binary/build/library/docs/reproducible build")

    bom_dir = ROOT / "exports/final/bom"
    bom, bom_fields = csv_rows("exports/final/bom/BOM.csv")
    bom_ok = all((bom_dir / name).is_file() and (bom_dir / name).stat().st_size > 20 for name in BOM_FILES)
    normalized_bom_fields = {field.lower().replace("/", "_").replace(" ", "_") for field in bom_fields}
    bom_ok &= BOM_FIELDS <= normalized_bom_fields and len(bom) >= 30 and all(r.get("revision") == REV and int(r.get("quantity", 0)) > 0 for r in bom)
    bom_verify_path = bom_dir / "bom_verification.json"
    bom_verify = json.loads(bom_verify_path.read_text()) if bom_verify_path.is_file() else {}
    bom_ok &= bom_verify.get("digital_integrity_status") == "PASS"
    bom_ok &= bom_verify.get("fabrication_procurement_readiness") == "HOLD"
    record("14_authoritative_bom", bom_ok, f"rows={len(bom)} digital=PASS procurement=HOLD")

    steps, step_fields = csv_rows("docs/final/assembly_steps.csv")
    manual_ok = all(pdf_ok(f"docs/final/{name}") for name in MANUALS) and len(steps) >= 21 and ASSEMBLY_FIELDS <= step_fields and all(all(r.get(k, "").strip() for k in ASSEMBLY_FIELDS) for r in steps)
    held_steps = [r.get("step_number") for r in steps if any("HOLD" in (value or "") for value in r.values())]
    record("15_assembly_manual", manual_ok, f"structured_steps={len(steps)} artifact_fields_and_pdfs={manual_ok} execution_HOLD_steps={held_steps}; completeness is separate from physical approval")
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
    if package.is_file() and not technical_only:
        proc = subprocess.run([sys.executable, str(ROOT / "release/verify_fabrication_release.py")], cwd=ROOT, text=True, capture_output=True)
        with zipfile.ZipFile(package) as zf:
            manifest = json.loads(zf.read("00_START_HERE/release_manifest.json"))
        package_ok = proc.returncode == 0 and manifest.get("release_state") == "FABRICATION_CANDIDATE" and manifest.get("physical_validation_state") == "NOT_RUN"
    record("20_release_package", package_ok, "deterministic ZIP schema/hash/clean-extraction verification")
    remote_path = ROOT / "validation/v0.8/remote_release_state.json"
    remote = json.loads(remote_path.read_text()) if remote_path.is_file() else {}
    remote_ok = False
    branch = head = "UNKNOWN"
    pr = {}
    try:
        if technical_only:
            raise FileNotFoundError("distribution checks explicitly outside technical-only scope")
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() or remote.get("branch", "")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        pushed = subprocess.check_output(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=ROOT, text=True).split()[0]
        pr = json.loads(subprocess.check_output(
            ["gh", "pr", "view", str(remote.get("pr_number", "")), "--json", "state,headRefName,baseRefName,url"],
            cwd=ROOT, text=True,
        ))
        remote_ok = pushed == head and branch == REV and pr == {
            "baseRefName": "main", "headRefName": branch, "state": "OPEN", "url": remote.get("pr_url"),
        }
    except (FileNotFoundError, IndexError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    policy_ok = exists("docs/final/release_notes_v1.0.0-rc1_ko.md", 200) and remote_ok
    policy_ok &= publication_policy_current(ROOT) and remote.get("fabrication_release_approval") == "USER_APPROVAL_REQUIRED"
    record("21_release_policy", policy_ok, "origin HEAD + open main-target PR verified; user-authorized prerelease only; physical approvals remain blocked")
    if technical_only:
        for gate in ("20_release_package", "21_release_policy"):
            checks[gate] = {"status": "NOT_EVALUATED", "evidence": "Explicitly outside technical-only CI scope; required separately for release."}

    all_checks_ok = all(v["status"] == "PASS" for v in checks.values())
    parameters = json.loads((ROOT / "cad/parameters/final_v08.json").read_text())
    requirements_text = (ROOT / "requirements/system_requirements.md").read_text()
    scope_ok = all(parameters.get(name) == value for name, value in {
        "validation_basis": "OPENMODELICA_CALCULIX_CLOSED_FORM_CAD",
        "cross_solver_state": "NOT_COMPLETED_BY_SCOPE_DECISION",
        "fusion_state": "STOPPED_NOT_USED_FOR_FINAL_RELEASE",
        "inventor_state": "STOPPED_NOT_USED_FOR_FINAL_RELEASE",
        "physical_validation_state": "NOT_RUN",
    }.items())
    architecture_ok = parameters.get("architecture") == "compact_single_path" and all(
        token in requirements_text for token in ("SYS-PATH-01", "공용 16 mm×16 L/D single screw", "200 g/h는 stretch target"))
    full_assembly = next((row for row in step_rows if row.get("part_id") == "PPR-FULL-ASM"), {})
    print_mass = sum(float(row["slicer_mass_total_g"]) for row in print_rows)
    print_time = sum(int(row["estimated_print_time_s"]) for row in print_rows)
    bom_quantity = sum(int(row["quantity"]) for row in bom)
    manual_pdf_count = sum((ROOT / "docs/final" / name).is_file() for name in MANUALS + COMMISSIONING)
    failed = [name for name, row in checks.items() if row["status"] != "PASS"]
    tolerance_rows = tol.get("interfaces", tol.get("stacks", []))
    tolerance_numeric_fail = [row["interface_id"] for row in tolerance_rows if row.get("numeric_status") == "FAIL"]
    tolerance_not_evaluated = [row["interface_id"] for row in tolerance_rows if row.get("numeric_status") == "NOT_EVALUATED"]
    tolerance_assumption_bound = [row["interface_id"] for row in tolerance_rows if row.get("assessment_kind") == "ASSUMPTION_BOUND"]
    thrust_path = ROOT / "analysis/final_validation/results/v0.8/extruder_thrust_stack_candidate.json"
    thrust = json.loads(thrust_path.read_text()) if thrust_path.is_file() else {}
    current_zip = "NOT_CREATED"
    if package.is_file() and not technical_only:
        current_zip += f"; 기존 파일은 과거 산출물 SHA-256 {sha(package)}"
    CURRENT_REPORT.write_text(f"""# v0.8 현재 closure 보고서

report_state: `CURRENT` · 전체 gate: `{'PASS' if all_checks_ok else 'IN_PROGRESS'}` · 제작: `HOLD`

## source baseline and final commit

- 기준 main: `{baseline.get('remote_main')}`
- 현재 branch/HEAD: `{branch}` / `{head}`
- final commit: `{'HEAD' if not failed else 'NOT_ESTABLISHED—미해결 gate와 작업트리 변경 존재'}`

## design changes and reasons / architecture drift

- v0.8은 hot-zone 지지, 하중 위상, 공차·인터페이스 및 패키지 증거를 재검증하도록 재개됐다.
- architecture: `{parameters.get('architecture')}`; scope decision=`{parameters.get('cross_solver_state')}`.
- architecture drift: `{'NONE_DETECTED' if architecture_ok else 'FAIL'}`; 200 g/h는 release 기준이 아닌 stretch target이다.

## LC04 resolution / hot-zone mount resolution / final safety factors

- LC04 resolution: `{solver.get('LC04', {}).get('resolution')}`; fine displacement={solver.get('LC04', {}).get('meshes', [{}])[-1].get('result', {}).get('max_displacement_mm')} mm.
- hot-zone mount resolution: `{hot.get('status')}`; selected=`{hot.get('selected_mount')}`; selected safety factor={selected.get('safety_factor')}.
- qualification gaps: `{hot_qualified}`. 위 safety factor는 디지털 선형 모델이며 실제 재료·접촉·시험 인증이 아니다.
- sensor-bore conditional thermal-pressure screen: `{sensor_local.get('status')}`; fine peak={sensor_local.get('meshes', [{}])[-1].get('sensor_region_peak_stress_mpa')} MPa; conditional SF={sensor_local.get('conditional_sf_at_177p5_mpa')}; source_current={sensor_local_current}.

## final dimensions and mass / part count

- assembly envelope: `{full_assembly.get('bbox_mm', 'NOT_ESTABLISHED')}` mm; active CAD body count={full_assembly.get('body_count', 'NOT_ESTABLISHED')}.
- final machine mass: `NOT_ESTABLISHED`—donor 실물과 혼합 소재 질량이 확정되지 않았다.
- BOM line count={len(bom)}; scheduled quantity sum={bom_quantity} (질량이나 고유 부품 수가 아님).

## print mass and time / STEP STL 3MF count / drawing count

- print mass={print_mass:.2f} g; estimated print time={print_time} s ({print_time / 3600:.2f} h); physical print/fit=`NOT_RUN`.
- STEP count={len(step_rows)}; STL count={len(print_rows)}; 3MF count={len(print_rows)}; drawing count={len(drawings)}.

## BOM / firmware / manual PDF

- BOM: {len(bom)} lines, digital integrity PASS, procurement HOLD.
- firmware build hash: `{json.loads((fw / 'build_manifest.json').read_text()).get('binary_sha256')}`; physical I/O commissioning NOT_RUN.
- manual/PDF count={manual_pdf_count} (manual 6 + commissioning/validation 9).

## release ZIP hash / known limitations

- release ZIP hash: `{current_zip}`.
- known limitations: `{', '.join(failed) if failed else 'NONE'}`.
- cutter key clocking: current-source=`{key_current}`, released left/right check=`{key_check.get('status')}`; actual optical/CMM inspection remains NOT_RUN.
- 25 mm phase-path candidate: current-source=`{phase25_current}`, numeric angle=`{phase25.get('numeric_screen')}`, total=`{phase25.get('combined_worst_angle_deg')}` deg, solid18 mm/34 N·m gear elastic=`{phase25.get('calculix_gear_elastic_angle_deg')}` deg, conditional strength=`{phase25.get('gear_conditional_strength_screen')}`/SF `{phase25.get('gear_conditional_strength_sf')}`/stress convergence `{phase25.get('gear_peak_stress_relative_mesh_change')}`, state=`{phase25.get('status')}`; 이는 범위가 제한된 디지털 증거다. 활성 CAD 반영 여부는 현재 파라미터와 assembly manifest로 확인하며, 전체 release 적격성과 실물 fit은 별도 gate다.
- rear axial retainer candidate: current-source=`{retainer_current}`, numeric=`{retainer.get('numeric_screen')}`, bolt proof SF=`{retainer.get('m4_class88_proof_safety_factor')}`, thread pullout SF=`{retainer.get('thread_pullout_safety_factor')}`, minimum preload/load=`{retainer.get('minimum_preload_to_design_load_ratio')}`, state=`{retainer.get('status')}`; 이 값만으로 최종 체결부 적격성을 승인하지 않는다. 활성 CAD 반영 여부와 고온 재료·예압/접촉 가정, 실물 마찰·열이완은 각각의 gate에서 구분한다.
- extruder thrust stack: NSK 51102 dynamic SF=`{thrust.get('bearing_dynamic_rating_sf')}`, static SF=`{thrust.get('bearing_static_rating_sf')}`, Ruland MCLX-12-12-F torque SF=`{thrust.get('coupling_torque_sf')}`, state=`{thrust.get('status')}`. Ø15 h6 seat·Ø23 받침·Ø28.30–28.35 pocket·금속 shim 계약으로 IF-020은 디지털 PASS이며 수령/endplay/추력 proof는 NOT_RUN이다. IF-008은 GMP60 수령 한계가 포함된 디지털 기준 변형만 PASS이고 구매·수령·Gate-1은 HOLD다.
- tolerance blockers: numeric FAIL={tolerance_numeric_fail}; NOT_EVALUATED={tolerance_not_evaluated}; assumption-bound={tolerance_assumption_bound}. PASS 수치라도 blockers가 있으면 release PASS가 아니다.
- physical validation prerequisites: donor 라벨·정격·치수 확인, lockout, PE/퓨즈/interlock 검사, 단계별 사용자 승인과 실제 시험.
- user decisions still required: Tempco 승인도면·견적 검토, donor 선정, JLCCNC를 제외한 SCM440/QT/질화 전문 공급업체 선정, 구매·가공·통전·시운전 승인.

## 사용자 지정 조달 경로 조사 (2026-09-08)

- JLCCNC의2026-09-08 서면 회신은 비목록 SCM440 조달, Q&T, 가스질화와 그 최종
  물성·경도·층깊이 보증을 지원하지 않으며, 일반 최저 공차는±0.05 mm이고 개별
  형상·검사는 STEP/CNC Remark 업로드 후 심사한다고 답했다. 같은 주문에서 coupon을
  먼저 제작·승인한 뒤 본품을 진행하는 순서도 지원하지 않는다. 따라서 JLCCNC는
  현 EX-SCR-01/EX-BAR-01 사양의 일괄 공급처에서 `REJECTED_FOR_CURRENT_SPEC`이며,
  전문 SCM440/QT/질화/후가공 업체 선정 전 발주 금지를 유지한다.
  증적: docs/final/jlccnc_response_2026-09-08_ko.md
- T1–T4 기준품은 Tempco MTA1 맞춤 K형 비접지 MI probe다. 계약은 Alloy600,
  Ø3.00±0.03 mm, 25.40±0.25 mm sheath, 공급자 용접 Ø6.00±0.05×0.80±0.05 mm
  stop collar, 배럴 collar-to-tip5.20±0.05 mm 및 다이10.00±0.05 mm다.
  TH-TCR-01 bridge/SYS-17 체결과 보어 공차를 RFQ·BOM·FreeCAD 원본에 반영했다.
  제조사 승인도면·견적과 수령 후 치수/절연/교정/열응답/pull 시험 전에는
  `QUOTE_AND_RECEIPT_HOLD`이며 구매 승인이나 실물 검증 완료가 아니다.
  근거: docs/final/thermocouple_selection_basis_ko.md
- M8 spring/compression형 제품 ID `1005004962533904`는 나사 포트가 없는 현행 blind bore와
  직접 호환된다는 증거가 없어 채택하지 않았다. 배럴을 M8로 재가공하지 않는다.

## branch/PR/release state

- branch: `{branch}`; PR: `{remote.get('pr_url', 'NOT_ESTABLISHED')}` / `{pr.get('state', 'UNKNOWN')}`.
- GitHub publication: `PRERELEASE_AUTHORIZED`; actual published state is observed from the GitHub Release API; fabrication approval: `{remote.get('fabrication_release_approval', 'USER_APPROVAL_REQUIRED')}`.
""", encoding="utf-8")
    final_report_text = CURRENT_REPORT.read_text()
    final_report_ok = "report_state: `CURRENT`" in final_report_text and all(token in final_report_text for token in (
        "source baseline", "architecture", "LC04", "hot-zone", "safety factor", "STEP", "STL", "3MF",
        "BOM", "firmware", "release ZIP", "known limitations", "physical validation", "branch", "PR"))
    release_notes = (ROOT / "docs/final/release_notes_v1.0.0-rc1_ko.md").read_text()
    final_states_ok = all_checks_ok and "FINAL_DESIGN_FROZEN" in release_notes and "READY_FOR_USER_APPROVAL" in release_notes
    sections = audit_sections(checks, {
        "$scope_decision": scope_ok,
        "$architecture_freeze": architecture_ok,
        "$final_states": final_states_ok,
        "$execution_complete": all_checks_ok and final_report_ok,
        "$final_report": final_report_ok,
    })
    passed = sum(v["status"] == "PASS" for v in checks.values())
    passed_sections = sum(v["status"] == "PASS" for v in sections.values())
    complete = all_checks_ok and passed_sections == len(sections)
    result = {"evidence_freshness": freshness_audits, "revision": REV, "status": "PASS" if complete else "FAIL", "passed": passed, "total": len(checks), "checks": checks,
              "section_coverage": sections, "passed_sections": passed_sections, "total_sections": len(sections),
              "technical_state": "DIGITAL_TECHNICAL_CLOSURE" if complete else "IN_PROGRESS",
              "physical_validation_state": "NOT_RUN", "safety_certification": "NOT_CERTIFIED", "fabrication_release_approval": "USER_APPROVAL_REQUIRED"}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    rows = ["# v0.8 전체 compliance", "", "첨부 goal 0–25절의 디지털 gate다. 물리시험·안전인증이 아니다.", ""]
    rows += [f"- `{v['status']}` {k}: {v['evidence']}" for k, v in checks.items()]
    rows += ["", f"산출물 gate: **{passed}/{len(checks)}**", f"원문 절 완료: **{passed_sections}/{len(sections)}**", f"전체 결과: **{result['status']}**", "", "물리시험 `NOT_RUN` · 안전인증 `NOT_CERTIFIED` · 제작 승인 `USER_APPROVAL_REQUIRED`", ""]
    REPORT.write_text("\n".join(rows), encoding="utf-8")
    print(f"V08_FULL_COMPLIANCE_{result['status']} {passed}/{len(checks)}")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        names = {name for values in SECTION_BINDINGS.values() for name in values if not name.startswith("$")}
        fake = {name: {"status": "PASS"} for name in names}
        extras = {name: True for name in ("$scope_decision", "$architecture_freeze", "$final_states", "$execution_complete", "$final_report")}
        assert all(row["covered"] and row["status"] == "PASS" for row in audit_sections(fake, extras).values())
        fake.pop("00_authoritative_baseline")
        assert audit_sections(fake, extras)["00"]["covered"] is False
        print("V08_SECTION_COVERAGE_SELF_TEST_PASS sections=26")
    else:
        main()
