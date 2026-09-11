#!/usr/bin/env python3
"""Fail-closed P9 empty-hot-zone evidence checker."""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P7_VALIDATOR = ROOT / "validation/physical_v08/validate_p7_stage_release.py"
P8_VALIDATOR = ROOT / "validation/physical_v08/validate_p8_stage_release.py"
RECEIPT_ANALYZER = ROOT / "validation/physical_v08/analyze_p9_receipt.py"
TOPOLOGY_VALIDATOR = ROOT / "validation/physical_v08/validate_thermal_cutoff_topology.py"
PROFILE_SOURCE = ROOT / "firmware/arduino_mega/src/generated_profiles.h"
SOURCE_FILES = (
    "firmware/arduino_mega/src/generated_profiles.h",
    "control/thermal_cutoff_contract.json",
    "control/thermal_barrier_tape_contract.json",
    "exports/thermal/manifest.csv",
    "exports/thermal/channel_schedule.csv",
    "exports/final/electrical/fuse_schedule.csv",
    "exports/final/electrical/wire_schedule.csv",
    "validation/physical_v08/physical_gate_contract.json",
)
NUMERIC = {
    "cold_axial_travel_reference": ("min", 1.50, "mm"),
    "die_fastener_length_min": ("min", 42.4, "mm"),
    "die_fastener_length_max": ("max", 42.6, "mm"),
    "tcr_hot_cycle_pull_motion_max": ("max", 0.10, "mm"),
    "post_cycle_pe_bond_worst": ("max", 0.10, "ohm"),
    "post_cycle_insulation_resistance": ("min", 1.0, "Mohm"),
    "post_cycle_insulation_test_voltage": ("range", (500.0, 500.0), "VDC"),
    "thermal_barrier_tape_edge_lift_max": ("max", 2.0, "mm"),
}
BOOL_TRUE = {
    "p9_heater_power_approval_recorded", "motor_branches_isolated", "motor_commands_inhibited",
    "grounded_metal_hot_shield_installed", "remote_stop_available", "t1_t5_mapping_correct",
    "sensor_open_fault_detected", "sensor_short_fault_detected",
    "tf_barrel_open_removes_k0_heater_energy", "tf_die_open_removes_k0_heater_energy",
    "thermal_cutoff_series_order_match_contract", "heater_branch_fuse_ids_match_schedule",
    "die_fasteners_dry_1p50Nm_setting", "tcr_hot_cycle_pull_20n_verified",
    "thermal_barrier_tape_installed_allowed_surfaces_only",
    "thermal_barrier_tape_no_sensor_cutoff_terminal_vent_coverage",
    "thermal_barrier_tape_no_smoke_char_melt_adhesive_flow",
}
BOOL_FALSE = {
    "hot_mount_hard_stop_contact", "polymer_leak_evaluated_in_p9",
    "automatic_restart_after_thermal_cut_recovery",
}
DYNAMIC_NUMERIC = {"thermal_barrier_tape_interface_peak": "C", "thermal_barrier_tape_outer_surface_peak": "C"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(path: Path, label: str) -> Path:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must be an existing repository file")
    return path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric value")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + ": non-finite numeric value")
    return out


def timestamp(value: str, field: str) -> None:
    parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(field + " must include timezone")

def authenticate(row: dict[str, str], *, numeric: bool, logger: bool = False) -> None:
    required = ["operator", "reviewer", "measured_at", "evidence_path", "sha256"]
    if numeric:
        required += ["calibration_ref", "logger_id" if logger else "instrument_id"]
    missing = [key for key in required if not str(row.get(key, "")).strip()]
    if missing:
        raise ValueError("missing evidence metadata: " + ",".join(missing))
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError("independent reviewer must differ from operator")
    timestamp(row["measured_at"], "measured_at")
    evidence = (ROOT / row["evidence_path"]).resolve()
    if not evidence.is_relative_to(ROOT) or not evidence.is_file():
        raise ValueError("invalid evidence path: " + row["evidence_path"])
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(evidence) != digest:
        raise ValueError("evidence hash mismatch: " + row["evidence_path"])


def bool_value(row: dict[str, str], metric: str) -> bool:
    token = row.get("value", "").strip().upper()
    if token not in {"TRUE", "FALSE", "YES", "NO", "1", "0", "PASS"}:
        raise ValueError(metric + ": invalid boolean")
    return token in {"TRUE", "YES", "1", "PASS"}


def limit_ok(value: float, u95: float, mode: str, limit) -> bool:
    if u95 < 0:
        return False
    if mode == "min":
        return value - u95 >= float(limit)
    if mode == "max":
        return value + u95 <= float(limit)
    lo, hi = limit
    return value - u95 >= lo and value + u95 <= hi

def profile_contract(path: Path = PROFILE_SOURCE) -> tuple[dict[tuple[str, str], float], float]:
    text = path.read_text(encoding="utf-8")
    targets: dict[tuple[str, str], float] = {}
    for name in ("PLA", "PET"):
        match = re.search(rf"constexpr ProcessProfile {name}_PROFILE\{{(.*?)\}};", text, re.S)
        if not match:
            raise ValueError(name + " profile missing from generated firmware contract")
        thermal = re.search(r"\{\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\}\s*,\s*([0-9.]+)\s*,", match.group(1))
        if not thermal:
            raise ValueError(name + " thermal targets missing from generated firmware contract")
        z1, z2, z3, die = map(float, thermal.groups())
        targets.update({(name, "Z1"): z1, (name, "Z2"): z2, (name, "Z3"): z3, (name, "DIE"): die})
    over = re.search(r"HEATER_OVERTEMPERATURE_C\s*=\s*([0-9.]+)f?;", text)
    if not over:
        raise ValueError("firmware overtemperature ceiling missing")
    return targets, float(over.group(1))


def require_prerequisites(p7_release: Path, p8_release: Path, receipt: Path, *,
                          p7_checker=None, p8_checker=None, receipt_checker=None,
                          topology_checker=None) -> dict:
    p7 = (p7_checker or load(P7_VALIDATOR, "ppr_p9_p7").validate)(p7_release)
    p8 = (p8_checker or load(P8_VALIDATOR, "ppr_p9_p8").validate)(p8_release)
    receipt_result = (receipt_checker or load(RECEIPT_ANALYZER, "ppr_p9_receipt").evaluate)(receipt)
    topology = (topology_checker or load(TOPOLOGY_VALIDATOR, "ppr_p9_topology").validate)()
    if p7.get("status") != "P7_STAGE_RELEASE_VALIDATED" or p7.get("p9_entry_prerequisite") is not True:
        raise ValueError("P7 stage release is not a valid P9 prerequisite")
    if p7.get("heater_energization_authorized") is not False or p7.get("machine_release") != "HOLD":
        raise ValueError("P7 release authorization semantics drift")
    if p8.get("status") != "P8_STAGE_RELEASE_VALIDATED" or p8.get("p9_entry_prerequisite") is not True:
        raise ValueError("P8 stage release is not a valid P9 prerequisite")
    if p8.get("heater_energization_authorized") is not False or p8.get("machine_release") != "HOLD":
        raise ValueError("P8 release authorization semantics drift")
    if receipt_result.get("status") != "HOT_ZONE_RECEIPT_RECORD_CHECK_PASS" or receipt_result.get("p9_receipt_prerequisite") is not True:
        raise ValueError("hot-zone receipt evidence is not a valid P9 prerequisite")
    if receipt_result.get("power_authorization") is not False or receipt_result.get("machine_release") != "HOLD":
        raise ValueError("P9 receipt authorization semantics drift")
    if topology.get("status") != "THERMAL_CUTOFF_TOPOLOGY_PASS":
        raise ValueError("thermal cutoff topology is not validated")
    return {"p7": p7, "p8": p8, "receipt": receipt_result, "topology": topology}


def evaluate(thermal_path: Path, safety_path: Path, p7_release: Path, p8_release: Path, receipt: Path, *,
             p7_checker=None, p8_checker=None, receipt_checker=None, topology_checker=None) -> dict:
    out = {"status": "NOT_RUN_OR_REJECTED", "stage_p9_pass": False,
           "p10_entry_prerequisite": False, "material_feed_authorized": False,
           "continuing_power_authority": False, "machine_release": "HOLD"}
    try:
        thermal_path = repo_file(thermal_path, "P9 thermal profile")
        safety_path = repo_file(safety_path, "P9 hot-safety record")
        p7_release = repo_file(p7_release, "P7 release")
        p8_release = repo_file(p8_release, "P8 release")
        receipt = repo_file(receipt, "P9 hot-zone receipt")
        prerequisites = require_prerequisites(
            p7_release, p8_release, receipt, p7_checker=p7_checker, p8_checker=p8_checker,
            receipt_checker=receipt_checker, topology_checker=topology_checker)
        source_hashes = {}
        for relative in SOURCE_FILES:
            source = ROOT / relative
            if not source.is_file():
                raise ValueError("missing controlling source: " + relative)
            source_hashes[relative] = sha(source)
        targets, overtemperature_c = profile_contract()
        thermal_rows = rows(thermal_path)
        by_thermal = {(r.get("profile", "").strip(), r.get("zone", "").strip()): r for r in thermal_rows}
        if len(thermal_rows) != len(targets) or set(by_thermal) != set(targets):
            raise ValueError("P9 thermal profile coverage mismatch")
        thermal_checks = {}
        for key, target in targets.items():
            row = by_thermal[key]; authenticate(row, numeric=True, logger=True)
            if row.get("unit", "").strip() != "C":
                raise ValueError(f"{key}: unit mismatch")
            recorded_target = number(row.get("target_c"), f"{key} target")
            mean = number(row.get("measured_mean_c"), f"{key} mean")
            u95 = number(row.get("u95_c"), f"{key} mean U95")
            peak = number(row.get("run_peak_c"), f"{key} peak")
            peak_u95 = number(row.get("run_peak_u95_c"), f"{key} peak U95")
            if not math.isclose(recorded_target, target, abs_tol=1e-9):
                raise ValueError(f"{key}: target differs from generated firmware profile")
            if u95 < 0 or mean - u95 < target - 5.0 or mean + u95 > target + 5.0:
                raise ValueError(f"{key}: mean temperature outside U95-bounded target band")
            if peak_u95 < 0 or peak < mean or peak + peak_u95 > overtemperature_c:
                raise ValueError(f"{key}: peak temperature acceptance failed")
            thermal_checks[f"{key[0]}-{key[1]}"] = {
                "target_c": target, "mean_c": mean, "mean_u95_c": u95,
                "peak_c": peak, "peak_u95_c": peak_u95,
                "overtemperature_ceiling_c": overtemperature_c, "pass": True,
            }

        safety_rows = rows(safety_path)
        by_safety = {r.get("metric", "").strip(): r for r in safety_rows}
        required_safety = set(NUMERIC) | set(DYNAMIC_NUMERIC) | BOOL_TRUE | BOOL_FALSE
        if len(safety_rows) != len(required_safety) or set(by_safety) != required_safety:
            raise ValueError("P9 hot-safety metric set mismatch")
        safety_checks = {}
        for metric, (mode, limit, unit) in NUMERIC.items():
            row = by_safety[metric]; authenticate(row, numeric=True)
            if row.get("unit", "").strip() != unit:
                raise ValueError(metric + ": unit mismatch")
            value = number(row.get("value"), metric)
            u95 = number(row.get("u95"), metric + " U95")
            if value < 0 or not limit_ok(value, u95, mode, limit):
                raise ValueError(metric + ": outside U95-bounded acceptance")
            safety_checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": True}
        for metric, unit in DYNAMIC_NUMERIC.items():
            row = by_safety[metric]; authenticate(row, numeric=True)
            if row.get("unit", "").strip() != unit:
                raise ValueError(metric + ": unit mismatch")
            value = number(row.get("value"), metric); u95 = number(row.get("u95"), metric + " U95")
            if value < 0 or u95 < 0:
                raise ValueError(metric + ": invalid temperature evidence")
            safety_checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": True}
        tape_rating = prerequisites["receipt"].get("checks", {}).get("tape_continuous_service_rating", {}).get("value")
        if tape_rating is None:
            raise ValueError("thermal barrier tape continuous service rating missing from receipt")
        interface = safety_checks["thermal_barrier_tape_interface_peak"]
        required_margin = 30.0
        if interface["value"] + interface["u95"] + required_margin > float(tape_rating):
            raise ValueError("thermal barrier tape continuous-service temperature margin failed")
        safety_checks["thermal_barrier_tape_rating_margin"] = {
            "documented_rating_c": float(tape_rating),
            "interface_peak_plus_u95_c": interface["value"] + interface["u95"],
            "required_margin_c": required_margin,
            "remaining_margin_c": float(tape_rating) - interface["value"] - interface["u95"],
            "pass": True,
        }
        for metric, expected in [(x, True) for x in BOOL_TRUE] + [(x, False) for x in BOOL_FALSE]:
            row = by_safety[metric]; authenticate(row, numeric=False)
            actual = bool_value(row, metric)
            if actual is not expected:
                raise ValueError(metric + ": boolean acceptance failed")
            safety_checks[metric] = {"value": actual, "pass": True}
        out.update({
            "status": "P9_RECORD_CHECK_PASS",
            "stage_p9_pass": False,
            "p10_entry_prerequisite": False,
            "input_heater_power_approval_recorded": safety_checks["p9_heater_power_approval_recorded"]["value"],
            "material_feed_authorized": False,
            "continuing_power_authority": False,
            "machine_release": "HOLD",
            "thermal": thermal_checks,
            "safety": safety_checks,
            "thermal_profile_contract": {
                "targets_c": {f"{p}-{z}": value for (p, z), value in targets.items()},
                "overtemperature_ceiling_c": overtemperature_c,
                "source_sha256": sha(PROFILE_SOURCE),
            },
            "prerequisites": {
                "p7_release_sha256": sha(p7_release),
                "p8_release_sha256": sha(p8_release),
                "p9_receipt_sha256": sha(receipt),
                "topology_status": prerequisites["topology"]["status"],
            },
            "source_bindings_sha256": source_hashes,
            "thermal_record_sha256": sha(thermal_path),
            "safety_record_sha256": sha(safety_path),
            "note": "Authenticated bounded P9 evidence passed. A separate reviewed stage release is required before P10 entry review.",
        })
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        out["reason"] = str(exc)
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("thermal", type=Path)
    ap.add_argument("safety", type=Path)
    ap.add_argument("--p7-release", required=True, type=Path)
    ap.add_argument("--p8-release", required=True, type=Path)
    ap.add_argument("--receipt", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = evaluate(args.thermal, args.safety, args.p7_release, args.p8_release, args.receipt)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "P9_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__":
    main()
