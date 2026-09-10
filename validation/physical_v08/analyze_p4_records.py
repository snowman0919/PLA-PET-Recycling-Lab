#!/usr/bin/env python3
"""Fail-closed P4 two-cutter coupon record checker.

This tool authenticates recorded evidence and recomputes P4 acceptance metrics.
It never authorizes P4 energization, fabrication, or a later stage release.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
P4_FILES = ("p4_preflight.csv", "p4_quasistatic.csv", "p4_jam.csv", "p4_chip.csv")
SOURCE_FILES = (
    "control/ggm_drive_contract.json",
    "validation/physical_v08/physical_gate_contract.json",
    "validation/physical_v08/P4_SHREDDER_COUPON_KO.md",
    "validation/physical_v08/validate_p3_stage_release.py",
)

PRE_NUMERIC = {
    "cutter_coupon_count": ("exact", 2.0, "count"),
    "shaft_tir_left": ("max", 0.10, "mm"),
    "shaft_tir_right": ("max", 0.10, "mm"),
    "phase_error": ("max", 1.0, "deg"),
    "min_cutter_screen_clearance": ("min", 1.90, "mm"),
    "hand_rotation_contacts": ("exact", 0.0, "count"),
    "pe_bond_worst": ("max", 0.10, "ohm"),
    "chain_alignment_150": ("max", 0.20, "mm"),
    "chain_midspan_slack_percent": ("range", (2.0, 3.0), "percent"),
    "drive_guard_clearance": ("min", 3.0, "mm"),
    "sprocket_12t_radial_tir": ("max", 0.10, "mm"),
    "sprocket_30t_radial_tir": ("max", 0.10, "mm"),
    "sprocket_12t_axial_shift": ("max", 0.20, "mm"),
    "sprocket_30t_axial_shift": ("max", 0.20, "mm"),
}
PRE_BOOLEAN = {
    "cutter_coupon_revision_match": True,
    "estop_removes_motor_power": True,
    "guard_interlock_removes_motor_power": True,
    "power_restore_auto_restart": False,
    "guard_reach_path": False,
    "bearing_axial_release": False,
    "key_relative_slip": False,
    "outer_guard_closed": True,
    "p4_energization_approval_record": True,
    "sprocket_12t_key_torque_path": True,
    "sprocket_30t_key_torque_path": True,
    "sprocket_12t_axial_retention_verified": True,
    "sprocket_30t_axial_retention_verified": True,
}
EXPECTED_SPECIMENS = {
    *(f"PLA12-{i:02d}" for i in range(1, 6)),
    *(f"PLA20-{i:02d}" for i in range(1, 6)),
    *(f"PLA30-{i:02d}" for i in range(1, 6)),
    *(f"PET-B-{i:02d}" for i in range(1, 6)),
    *(f"PET-F-{i:02d}" for i in range(1, 6)),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric value")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + ": non-finite numeric value")
    return out


def boolean(value, field: str) -> bool:
    token = str(value).strip().upper()
    if token in {"TRUE", "YES", "PASS", "1"}:
        return True
    if token in {"FALSE", "NO", "NONE", "0"}:
        return False
    raise ValueError(field + ": invalid boolean")


def evidence(row: dict[str, str], root: Path, time_field: str, instruments: tuple[str, ...] = ()) -> Path:
    ident = row.get("check_id") or row.get("specimen_id") or (row.get("material", "?") + "-" + row.get("trial", row.get("batch_id", "?")))
    required = ("operator", "reviewer", time_field, "evidence_path", "sha256", *instruments)
    missing = [name for name in required if not row.get(name, "").strip()]
    if missing:
        raise ValueError(f"{ident}: incomplete provenance: {','.join(missing)}")
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError(f"{ident}: independent reviewer required")
    stamp = datetime.datetime.fromisoformat(row[time_field].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError(f"{ident}: {time_field} must include timezone")
    path = (root / row["evidence_path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"{ident}: evidence path invalid")
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError(f"{ident}: stale evidence hash")
    return path


def interval_pass(value: float, u95: float, mode: str, limit) -> bool:
    if u95 < 0:
        return False
    if mode == "max":
        return value + u95 <= float(limit)
    if mode == "min":
        return value - u95 >= float(limit)
    if mode == "exact":
        return u95 == 0 and value == float(limit)
    if mode == "range":
        low, high = limit
        return value - u95 >= low and value + u95 <= high
    raise ValueError("unknown interval mode")


def preflight(rows: list[dict[str, str]], root: Path) -> dict:
    by = {row.get("check_id", "").strip(): row for row in rows}
    expected = set(PRE_NUMERIC) | set(PRE_BOOLEAN)
    if "" in by or len(by) != len(rows):
        raise ValueError("P4 preflight blank/duplicate check_id")
    if set(by) != expected:
        raise ValueError("P4 preflight check set mismatch")
    result = {}
    for check_id, (mode, limit, unit) in PRE_NUMERIC.items():
        row = by[check_id]
        evidence(row, root, "checked_at", ("instrument_id", "calibration_ref"))
        if row.get("unit", "").strip() != unit:
            raise ValueError(check_id + ": unit mismatch")
        value, u95 = number(row["value"], check_id), number(row["u95"], check_id + ".u95")
        if value < 0 or u95 < 0:
            raise ValueError(check_id + ": negative physical value/uncertainty")
        if check_id in {"cutter_coupon_count", "hand_rotation_contacts"} and not value.is_integer():
            raise ValueError(check_id + ": integer count required")
        if not interval_pass(value, u95, mode, limit):
            raise ValueError(check_id + ": acceptance interval failed")
        result[check_id] = {"value": value, "u95": u95, "unit": unit, "pass": True}
    for check_id, expected_value in PRE_BOOLEAN.items():
        row = by[check_id]
        evidence(row, root, "checked_at")
        if row.get("unit", "").strip() != "boolean":
            raise ValueError(check_id + ": unit must be boolean")
        value = boolean(row["value"], check_id)
        if value is not expected_value:
            raise ValueError(check_id + ": boolean acceptance failed")
        result[check_id] = {"value": value, "pass": True}
    return {"checks": len(result), "results": result}


def torque_from_force(row: dict[str, str]) -> tuple[float, float]:
    force = number(row["force_n"], "force_n")
    u_force = number(row["u95_force_n"], "u95_force_n")
    arm_mm = number(row["arm_mm"], "arm_mm")
    u_arm_mm = number(row["u95_arm_mm"], "u95_arm_mm")
    angle_deg = number(row["force_angle_error_deg"], "force_angle_error_deg")
    u_angle_deg = number(row["u95_angle_deg"], "u95_angle_deg")
    if min(force, arm_mm) < 0 or min(u_force, u_arm_mm, u_angle_deg) < 0:
        raise ValueError("negative torque input or uncertainty")
    if arm_mm - u_arm_mm < 249.5 or arm_mm + u_arm_mm > 250.5:
        raise ValueError("P4 torque-arm interval outside 250.0 +/-0.5 mm")
    if abs(angle_deg) + u_angle_deg >= 90:
        raise ValueError("force angle cannot define positive torque")
    r, ur = arm_mm / 1000.0, u_arm_mm / 1000.0
    theta, utheta = math.radians(angle_deg), math.radians(u_angle_deg)
    c, s = math.cos(theta), math.sin(theta)
    torque = force * r * c
    u_torque = math.sqrt((r * c * u_force) ** 2 + (force * c * ur) ** 2 + (force * r * s * utheta) ** 2)
    return torque, u_torque


def quasistatic(rows: list[dict[str, str]], root: Path) -> dict:
    ids = [row.get("specimen_id", "").strip() for row in rows]
    if len(ids) != 25 or len(set(ids)) != 25 or set(ids) != EXPECTED_SPECIMENS:
        raise ValueError("P4 quasi-static specimen coverage mismatch")
    by_material = {"PLA": [], "PET": []}
    for row in rows:
        sid = row["specimen_id"].strip()
        expected_material = "PLA" if sid.startswith("PLA") else "PET"
        if row.get("material") != expected_material:
            raise ValueError(sid + ": material/specimen identity mismatch")
        evidence(row, root, "measured_at", ("force_instrument_id", "force_calibration_ref", "arm_instrument_id", "arm_calibration_ref"))
        if number(row["actual_thickness_or_fold_mm"], sid + ".thickness") <= 0:
            raise ValueError(sid + ": invalid thickness/fold measurement")
        if not row.get("failure_mode", "").strip():
            raise ValueError(sid + ": failure_mode required")
        if boolean(row.get("permanent_damage"), sid + ".permanent_damage"):
            raise ValueError(sid + ": permanent machine damage")
        torque, u95 = torque_from_force(row)
        by_material[expected_material].append(torque)
    return {
        material: {"samples": len(values), "min_peak_nm": min(values), "max_peak_nm": max(values), "mean_peak_nm": sum(values) / len(values)}
        for material, values in by_material.items()
    }


def jam(rows: list[dict[str, str]], root: Path, mechanical_floor_nm: float) -> dict:
    expected = {(material, str(trial)) for material in ("PLA", "PET") for trial in range(1, 4)}
    keys = {(row.get("material", ""), row.get("trial", "").strip()) for row in rows}
    if len(rows) != 6 or len(keys) != 6 or keys != expected:
        raise ValueError("P4 jam trial coverage mismatch")
    result = []
    for row in rows:
        ident = row["material"] + "-jam-" + row["trial"]
        evidence(row, root, "measured_at", ("rpm_instrument_id", "rpm_calibration_ref", "torque_reference_id", "torque_calibration_ref"))
        rpm, urpm = number(row["pre_jam_cutter_rpm"], ident + ".rpm"), number(row["u95_rpm"], ident + ".u95_rpm")
        torque, utorque = number(row["max_gearbox_torque_nm"], ident + ".torque"), number(row["u95_torque_nm"], ident + ".u95_torque")
        if rpm <= 0 or urpm < 0 or rpm + urpm > 21.0:
            raise ValueError(ident + ": cutter RPM outside guarded envelope")
        if torque < 0 or utorque < 0 or torque + utorque >= mechanical_floor_nm:
            raise ValueError(ident + ": measured torque reaches mechanical-protection floor")
        retries = int(number(row["retry_count"], ident + ".retry_count"))
        if retries < 0 or retries > 3 or float(row["retry_count"]) != retries:
            raise ValueError(ident + ": retry count outside 0..3")
        cleared = boolean(row["jam_cleared"], ident + ".jam_cleared")
        latched = boolean(row["latched_fault_after_third_failure"], ident + ".latched")
        if not cleared and not (retries == 3 and latched):
            raise ValueError(ident + ": uncleared jam did not end in third-failure latch")
        if not boolean(row["guard_lockout_required_for_reset"], ident + ".lockout"):
            raise ValueError(ident + ": reset lockout not enforced")
        if boolean(row["automatic_restart"], ident + ".automatic_restart"):
            raise ValueError(ident + ": automatic restart observed")
        if boolean(row["permanent_damage"], ident + ".permanent_damage"):
            raise ValueError(ident + ": permanent damage observed")
        result.append({"material": row["material"], "trial": int(row["trial"]), "retry_count": retries, "jam_cleared": cleared, "latched": latched, "torque_upper_nm": torque + utorque})
    return {"trials": len(result), "max_torque_upper_nm": max(row["torque_upper_nm"] for row in result)}


def chip(rows: list[dict[str, str]], root: Path, mechanical_floor_nm: float) -> dict:
    if len(rows) != 2 or {row.get("material") for row in rows} != {"PLA", "PET"}:
        raise ValueError("P4 chip batch coverage mismatch")
    output = {}
    for row in rows:
        material = row["material"]
        evidence(row, root, "measured_at", ("scale_instrument_id", "scale_calibration_ref", "torque_reference_id", "torque_calibration_ref"))
        if number(row["screen_hole_mm"], material + ".screen") != 5.0:
            raise ValueError(material + ": screen must be released 5 mm coupon")
        recirc = int(number(row["oversize_recirc_count"], material + ".recirc"))
        if recirc < 0 or recirc > 1 or float(row["oversize_recirc_count"]) != recirc:
            raise ValueError(material + ": oversize recirculation count outside 0..1")
        input_mass = number(row["input_mass_g"], material + ".input_mass")
        masses = [number(row[name], material + "." + name) for name in ("mass_3_6_g", "mass_6_20_g", "mass_gt20_g", "fines_lt3_g")]
        u = number(row["u95_mass_g"], material + ".u95_mass")
        if input_mass < 30 or min(masses) < 0 or u < 0:
            raise ValueError(material + ": invalid mass record or less than 30 g input")
        recovered = sum(masses)
        denominator_low = recovered - 4 * u
        denominator_high = recovered + 4 * u
        if denominator_low <= 0:
            raise ValueError(material + ": mass uncertainty exceeds recovered mass")
        fraction_3_6_lower = max(0.0, masses[0] - u) / denominator_high * 100.0
        fraction_gt20_upper = (masses[2] + u) / denominator_low * 100.0
        fines_upper = (masses[3] + u) / denominator_low * 100.0
        recovery_lower = max(0.0, recovered - 4 * u) / (input_mass + u) * 100.0
        if fraction_3_6_lower < 70 or fraction_gt20_upper > 2 or fines_upper > 15 or recovery_lower < 95:
            raise ValueError(material + ": uncertainty-bounded chip-size/recovery acceptance failed")
        longest = number(row["longest_strip_mm"], material + ".longest_strip")
        if longest < 0:
            raise ValueError(material + ": longest strip cannot be negative")
        torque, utorque = number(row["max_gearbox_torque_nm"], material + ".torque"), number(row["u95_torque_nm"], material + ".u95_torque")
        if torque < 0 or utorque < 0 or torque + utorque >= mechanical_floor_nm:
            raise ValueError(material + ": representative feed reached mechanical-protection floor")
        events = int(number(row["software_torque_limit_events"], material + ".limit_events"))
        if events != 0 or float(row["software_torque_limit_events"]) != events:
            raise ValueError(material + ": software torque-limit event during representative normal feed")
        output[material] = {
            "input_mass_g": input_mass, "recovered_mass_g": recovered,
            "fraction_3_6_lower_percent": fraction_3_6_lower,
            "fraction_gt20_upper_percent": fraction_gt20_upper,
            "fines_upper_percent": fines_upper, "recovery_lower_percent": recovery_lower,
            "recirculation_count": recirc, "torque_upper_nm": torque + utorque,
        }
    return output


def evaluate_records(directory: Path, root: Path = ROOT) -> dict:
    directory = directory.resolve()
    if not directory.is_relative_to(root):
        raise ValueError("P4 records directory must be inside repository")
    paths = {name: directory / name for name in P4_FILES}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError("missing P4 record files: " + ", ".join(missing))
    ggm = json.loads((root / "control/ggm_drive_contract.json").read_text(encoding="utf-8"))
    if ggm["protection"]["command_limit_gearbox_nm"] != 8.0 or ggm["protection"]["mechanical_release_acceptance_nm"] != [8.8, 9.3]:
        raise ValueError("GGM protection hierarchy drift")
    mechanical_floor = float(ggm["protection"]["mechanical_release_acceptance_nm"][0])
    result = {
        "status": "NUMERIC_RECORD_CHECK_PASS",
        "record_check_only": True,
        "physical_evidence_evaluated": True,
        "stage_p4_pass": False,
        "hardware_authorization": False,
        "fabrication_authorized": False,
        "preflight": preflight(read_csv(paths["p4_preflight.csv"]), root),
        "quasistatic": quasistatic(read_csv(paths["p4_quasistatic.csv"]), root),
        "jam": jam(read_csv(paths["p4_jam.csv"]), root, mechanical_floor),
        "chip": chip(read_csv(paths["p4_chip.csv"]), root, mechanical_floor),
        "record_files_sha256": {name: sha(path) for name, path in paths.items()},
        "source_bindings_sha256": {name: sha(root / name) for name in SOURCE_FILES},
        "note": "P4 record acceptance does not authorize energization, remaining cutter fabrication, or stage release.",
    }
    return result


def canonical(data) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def repo_path(value: str, root: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else root / path
    path = path.resolve()
    if not path.is_relative_to(root) or not path.exists():
        raise ValueError(label + " must resolve inside repository")
    return path


def check_p3(path: Path) -> dict:
    validator = HERE / "validate_p3_stage_release.py"
    spec = importlib.util.spec_from_file_location("ppr_p4_p3_release", validator)
    if spec is None or spec.loader is None:
        raise ValueError("P3 stage-release validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.validate(path)
    if result.get("status") != "P3_STAGE_RELEASE_VALIDATED" or result.get("p4_entry_prerequisite") is not True:
        raise ValueError("P3 stage release did not validate")
    if result.get("p4_energization_authorized") is not False or result.get("machine_release") != "HOLD":
        raise ValueError("P3 stage release has unsafe downstream authorization semantics")
    result["stage_release_file_sha256"] = sha(path)
    return result


def build_result(directory: Path, p3_release: Path, root: Path = ROOT) -> dict:
    result = evaluate_records(directory, root)
    records_directory = directory.resolve()
    p3_path = p3_release.resolve()
    if not records_directory.is_relative_to(root) or not p3_path.is_relative_to(root) or not p3_path.is_file():
        raise ValueError("P4 records/P3 release must resolve inside repository")
    p3 = check_p3(p3_path)
    result.update({
        "records_directory": str(records_directory.relative_to(root)),
        "p3_stage_release_path": str(p3_path.relative_to(root)),
        "p3_stage_release_sha256": sha(p3_path),
        "p3_prerequisite": p3,
        "analyzer_sha256": sha(Path(__file__)),
    })
    return result


def validate_result(result: dict, root: Path = ROOT, p3_checker=None) -> dict:
    if result.get("status") != "NUMERIC_RECORD_CHECK_PASS" or result.get("record_check_only") is not True:
        raise ValueError("P4 result is not a numeric record PASS")
    if result.get("physical_evidence_evaluated") is not True:
        raise ValueError("P4 result did not evaluate physical evidence")
    if result.get("stage_p4_pass") is not False or result.get("hardware_authorization") is not False or result.get("fabrication_authorized") is not False:
        raise ValueError("P4 result has unsafe authorization semantics")
    if result.get("analyzer_sha256") != sha(Path(__file__)):
        raise ValueError("P4 result analyzer binding is stale")
    bindings = result.get("source_bindings_sha256", {})
    stale = [name for name in SOURCE_FILES if bindings.get(name) != sha(root / name)]
    if stale:
        raise ValueError("P4 result source binding stale: " + ", ".join(stale))
    records_dir = repo_path(result.get("records_directory", ""), root, "P4 records directory")
    if not records_dir.is_dir():
        raise ValueError("P4 records directory is not a directory")
    file_hashes = result.get("record_files_sha256", {})
    for name in P4_FILES:
        path = records_dir / name
        if not path.is_file() or file_hashes.get(name) != sha(path):
            raise ValueError("P4 record file hash mismatch: " + name)
    fresh = evaluate_records(records_dir, root)
    for key in ("preflight", "quasistatic", "jam", "chip", "record_files_sha256"):
        if canonical(result.get(key)) != canonical(fresh.get(key)):
            raise ValueError("P4 recomputed result mismatch: " + key)
    p3_path = repo_path(result.get("p3_stage_release_path", ""), root, "P3 stage release")
    if not p3_path.is_file() or result.get("p3_stage_release_sha256") != sha(p3_path):
        raise ValueError("P4 result P3-release binding is stale")
    checker = p3_checker or check_p3
    fresh_p3 = checker(p3_path)
    if canonical(result.get("p3_prerequisite")) != canonical(fresh_p3):
        raise ValueError("P4 result P3 prerequisite has changed")
    return {
        "records_directory": str(records_dir.relative_to(root)),
        "record_files": len(P4_FILES),
        "p3_stage_release_sha256": sha(p3_path),
        "analyzer_sha256": sha(Path(__file__)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", type=Path)
    ap.add_argument("--p3-release", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = build_result(args.dir, args.p3_release)
        code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {"status": "NOT_RUN_OR_REJECTED", "record_check_only": True, "stage_p4_pass": False,
                  "hardware_authorization": False, "fabrication_authorized": False, "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
