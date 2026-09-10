#!/usr/bin/env python3
"""Fail-closed record checker for P3 GGM bench pre-power readiness.

A PASS means the evidence packet is internally ready for a separate human
energization decision. This tool never authorizes motor power and never marks P3 PASS.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MOUNT_ANALYZER = HERE / "analyze_ggm_mount_compatibility.py"

EXPECTED = {
    "p2_applicable_cold_fit": {"PASS_REVIEWED"},
    "fixture_structure": {"RIGID_METAL"},
    "test_arbor_support": {"12MM_2X6201"},
    "coupling_guard": {"CLOSED_METAL_GUARD"},
    "brake_reference_guard": {"GUARDED_PRONY", "GUARDED_TORQUE_TRANSDUCER"},
    "process_load_state": {"CUTTER_AND_SCREW_ABSENT"},
    "heater_branch_state": {"ABSENT_OR_POSITIVELY_ISOLATED"},
    "axis_power_policy": {"ONE_AXIS_AT_A_TIME"},
    "shredder_driver": {"BTS7960"},
    "extruder_driver": {"BTS7960"},
    "shredder_current_channel": {"A0_MOTOR_LEAD"},
    "extruder_current_channel": {"A9_MOTOR_LEAD"},
    "shredder_branch_fuse": {"F-SH_20A_DC"},
    "extruder_branch_fuse": {"F-SCREW_10A_DC"},
    "hardcut_chain": {"DEENERGIZED_CONTINUITY_PASS"},
    "estop_guard_interlocks": {"PRESENT_POSITIVE_ACTION_CHECKED"},
    "current_reference": {"AVAILABLE_CALIBRATED"},
    "rpm_reference": {"AVAILABLE_CALIBRATED"},
    "torque_reference": {"AVAILABLE_CALIBRATED"},
    "workspace_clear": {"CLEAR"},
    "p3_energization_approval_record": {"APPROVED_FOR_P3_FIXTURE_ONLY"},
}

SOURCE_FILES = (
    "control/ggm_drive_contract.json",
    "validation/physical_v08/p3_fixture_contract.json",
    "validation/physical_v08/p3_bench_bom.csv",
    "electronics/io_schedule.csv",
    "exports/final/electrical/pin_schedule.csv",
    "exports/final/electrical/wire_schedule.csv",
    "exports/final/electrical/fuse_schedule.csv",
    "exports/final/firmware/build_manifest.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_mount_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p3_mount", MOUNT_ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load GGM mount analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_evidence(row: dict[str, str], root: Path) -> Path:
    check_id = row.get("check_id", "?")
    required = ("operator", "reviewer", "checked_at", "evidence_path", "sha256")
    missing = [name for name in required if not row.get(name, "").strip()]
    if missing:
        raise ValueError(f"{check_id}: incomplete provenance: {','.join(missing)}")
    stamp = datetime.datetime.fromisoformat(row["checked_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError(f"{check_id}: checked_at must include timezone")
    path = (root / row["evidence_path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"{check_id}: evidence path invalid")
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError(f"{check_id}: stale evidence hash")
    return path


def validate_machine_contract(root: Path) -> dict:
    ggm = json.loads((root / "control/ggm_drive_contract.json").read_text(encoding="utf-8"))
    fixture = json.loads((root / "validation/physical_v08/p3_fixture_contract.json").read_text(encoding="utf-8"))
    io = {r["signal"]: r for r in rows(root / "electronics/io_schedule.csv")}
    pins = {r["symbol"]: r for r in rows(root / "exports/final/electrical/pin_schedule.csv")}
    wires = {r["wire_id"]: r for r in rows(root / "exports/final/electrical/wire_schedule.csv")}
    fuses = {r["fuse_id"]: r for r in rows(root / "exports/final/electrical/fuse_schedule.csv")}
    bom = {r["id"]: r for r in rows(root / "validation/physical_v08/p3_bench_bom.csv")}
    fw = json.loads((root / "exports/final/firmware/build_manifest.json").read_text(encoding="utf-8"))

    if ggm["selected"]["shredder"] != "GGM K9DG60N2 + K9G75C" or ggm["selected"]["screw"] != "GGM K9DG60N2 + K9G150C":
        raise ValueError("GGM selected-drive contract drift")
    if ggm["protection"]["current_ceiling_a"] != 6 or ggm["protection"]["command_limit_gearbox_nm"] != 8.0:
        raise ValueError("GGM current/torque limit drift")
    if ggm["protection"]["mechanical_release_acceptance_nm"] != [8.8, 9.3] or ggm["screw"]["reverse_allowed"] is not False:
        raise ValueError("GGM mechanical protection or reverse policy drift")

    required_pins = {"SHREDDER_LPWM_PIN": "4", "SHREDDER_PWM_PIN": "5", "SHREDDER_ENABLE_PIN": "32", "SCREW_PWM_PIN": "6", "SCREW_DIR_PIN": "33", "SCREW_ENABLE_PIN": "34", "CURRENT_PIN": "A0", "EX_CURRENT_PIN": "A9"}
    if any(pins.get(name, {}).get("mega_pin") != pin for name, pin in required_pins.items()):
        raise ValueError("released GGM pin schedule drift")
    if "SHREDDER_FAULT_PIN" in pins or "SCREW_FAULT_PIN" in pins:
        raise ValueError("legacy GGM fault pin reappeared")
    if wires["SIG-A0"]["from"] != "Shredder Current" or wires["SIG-A9"]["from"] != "Extruder Current":
        raise ValueError("released GGM current wire drift")
    if fuses["F-SH"]["rating"] != "20 A DC" or fuses["F-SCREW"]["rating"] != "10 A DC":
        raise ValueError("GGM branch fuse schedule drift")
    if "SHREDDER_CURRENT_50A" in io or io["SHREDDER_CURRENT"]["owner"].split()[0] != "A0" or io["EXTRUDER_CURRENT"]["owner"].split()[0] != "A9":
        raise ValueError("GGM semantic I/O schedule drift")

    if fixture["physical_action_authorized"] is not False or fixture["prony"]["guard_required"] is not True or fixture["dynamic_map"]["max_current_a"] != 6.0:
        raise ValueError("P3 fixture fail-closed contract drift")
    for item in ("P3-FIX-04", "P3-MET-01", "P3-MET-02", "P3-MET-03", "P3-ELEC-01", "P3-ELEC-02", "P3-CONS-01"):
        if item not in bom:
            raise ValueError("P3 bench BOM missing " + item)

    binary = root / "exports/final/firmware" / fw["binary"]["path"]
    if fw.get("status") != "PASS" or fw.get("source_kind") != "GGM_BTS7960_VARIANT" or fw.get("clean_rebuild", {}).get("status") != "PASS":
        raise ValueError("GGM firmware release is not reproducible PASS")
    if not binary.is_file() or sha(binary) != fw["binary"]["sha256"]:
        raise ValueError("released firmware binary hash mismatch")
    revisions = {row["revision"] for row in pins.values()}
    if revisions != {fw["generation_base_git_sha"]}:
        raise ValueError("pin schedule and firmware generation-base mismatch")

    return {
        "selected_shredder": ggm["selected"]["shredder"],
        "selected_extruder": ggm["selected"]["screw"],
        "current_ceiling_a": ggm["protection"]["current_ceiling_a"],
        "software_limit_nm": ggm["protection"]["command_limit_gearbox_nm"],
        "mechanical_release_nm": ggm["protection"]["mechanical_release_acceptance_nm"],
        "firmware_binary_sha256": fw["binary"]["sha256"],
        "firmware_generation_base": fw["generation_base_git_sha"],
    }


def evaluate(record_rows: list[dict[str, str]], receipt_packet: dict, root: Path = ROOT) -> dict:
    by_id: dict[str, dict[str, str]] = {}
    for row in record_rows:
        check_id = row.get("check_id", "").strip()
        if not check_id:
            raise ValueError("blank P3 preflight check_id")
        if check_id in by_id:
            raise ValueError("duplicate P3 preflight check: " + check_id)
        by_id[check_id] = row
    missing = sorted(set(EXPECTED) - set(by_id))
    extra = sorted(set(by_id) - set(EXPECTED))
    if missing:
        raise ValueError("missing P3 preflight checks: " + ", ".join(missing))
    if extra:
        raise ValueError("unexpected P3 preflight checks: " + ", ".join(extra))

    checks = {}
    for check_id, accepted in EXPECTED.items():
        row = by_id[check_id]
        evidence_path = verify_evidence(row, root)
        if row.get("status", "").strip().upper() != "PASS":
            raise ValueError(check_id + ": status is not PASS")
        observed = row.get("observed", "").strip().upper()
        if observed not in accepted:
            raise ValueError(f"{check_id}: observed {observed!r}, expected one of {sorted(accepted)}")
        if check_id == "p2_applicable_cold_fit":
            try:
                p2_result = json.loads(evidence_path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("p2_applicable_cold_fit: evidence must be P2 analyzer JSON") from exc
            if p2_result.get("status") != "PASS" or p2_result.get("physical_evidence_evaluated") is not True:
                raise ValueError("p2_applicable_cold_fit: P2 analyzer result is not authenticated PASS")
            if p2_result.get("stage_release_granted") is not False:
                raise ValueError("p2_applicable_cold_fit: unexpected automatic stage release")
        checks[check_id] = {"observed": observed, "evidence_sha256": row["sha256"].lower(), "pass": True}

    machine = validate_machine_contract(root)
    mount = load_mount_analyzer().evaluate(receipt_packet)
    if mount.get("status") != "AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED":
        raise ValueError("GGM receipt/mount gate is not compatible: " + mount.get("status", "UNKNOWN"))

    simulation = json.loads((root / "validation/physical_v08/simulation_prerequisite.json").read_text(encoding="utf-8"))
    if simulation.get("status") != "PASS":
        raise ValueError("P0 technical prerequisite is not PASS")
    packet_sim = receipt_packet.get("simulation_prerequisite", {})
    expected_prereq_source = "validation/physical_v08/simulation_prerequisite.py"
    if packet_sim:
        if packet_sim.get("source") != expected_prereq_source or packet_sim.get("required_status") != "PASS":
            raise ValueError("receipt packet has invalid P0 prerequisite declaration")
        source_digest = packet_sim.get("source_sha256")
        if source_digest and source_digest != sha(root / expected_prereq_source):
            raise ValueError("receipt packet P0 checker source binding is stale")

    p0_snapshot = root / "validation/physical_v08/simulation_prerequisite.json"
    return {
        "status": "PREPOWER_RECORD_CHECK_PASS",
        "record_check_only": True,
        "physical_evidence_evaluated": True,
        "approval_record_present": True,
        "motor_energization_authorized": False,
        "stage_p3_pass": False,
        "mount_status": mount["status"],
        "p0_snapshot_sha256": sha(p0_snapshot),
        "p0_snapshot_head": simulation.get("head"),
        "checks": checks,
        "machine_contract": machine,
        "source_bindings_sha256": {name: sha(root / name) for name in SOURCE_FILES},
        "note": "A separate human decision at the fixture remains required. This analyzer never energizes hardware or grants P3 release.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preflight_csv", type=Path)
    ap.add_argument("--receipt-packet", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = evaluate(rows(args.preflight_csv), json.loads(args.receipt_packet.read_text(encoding="utf-8")))
        result["receipt_packet_sha256"] = sha(args.receipt_packet)
        code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {"status": "NOT_RUN_OR_REJECTED", "record_check_only": True, "motor_energization_authorized": False, "stage_p3_pass": False, "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
