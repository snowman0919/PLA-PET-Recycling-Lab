#!/usr/bin/env python3
"""Fail-closed P10/P11 low-feed material-run evidence checker."""
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
PROFILE_SOURCE = ROOT / "firmware/arduino_mega/src/generated_profiles.h"
P4_VALIDATOR = ROOT / "validation/physical_v08/validate_p4_stage_release.py"
P6_VALIDATOR = ROOT / "validation/physical_v08/validate_p6_stage_release.py"
P8_VALIDATOR = ROOT / "validation/physical_v08/validate_p8_stage_release.py"
P9_VALIDATOR = ROOT / "validation/physical_v08/validate_p9_stage_release.py"
P10_VALIDATOR = ROOT / "validation/physical_v08/validate_p10_stage_release.py"
EXPECTED_MATERIAL = {"P10": "PLA", "P11": "PET"}
APPROVAL_SCOPE = {"P10": "P10_BOUNDED_PLA_RUN", "P11": "P11_BOUNDED_PET_RUN"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repo_file(value, label: str) -> Path:
    if value is None or not str(value).strip():
        raise ValueError(label + " missing")
    path = Path(value)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric field")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + ": non-finite numeric field")
    return out


def yes(value) -> bool:
    token = str(value).strip().upper()
    if token not in {"TRUE", "FALSE", "YES", "NO", "1", "0", "PASS"}:
        raise ValueError("invalid boolean token: " + str(value))
    return token in {"TRUE", "YES", "1", "PASS"}


def stamp(value: str, field: str) -> datetime.datetime:
    try:
        parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(field + ": invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(field + " must include timezone")
    return parsed


def profile_targets() -> dict[str, tuple[float, float, float, float]]:
    text = PROFILE_SOURCE.read_text(encoding="utf-8")
    result = {}
    for material in ("PLA", "PET"):
        block = re.search(rf"constexpr ProcessProfile {material}_PROFILE\{{(.*?)\}};", text, re.S)
        if not block:
            raise ValueError(material + " profile missing")
        thermal = re.search(r"\{\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\}\s*,\s*([0-9.]+)\s*,", block.group(1))
        if not thermal:
            raise ValueError(material + " thermal targets missing")
        result[material] = tuple(map(float, thermal.groups()))
    return result


def validate_prerequisites(stage: str, releases: dict[str, Path | None], checkers=None) -> dict:
    checkers = checkers or {}
    if stage == "P10":
        specs = (
            ("p4", P4_VALIDATOR, "P4_STAGE_RELEASE_VALIDATED"),
            ("p6", P6_VALIDATOR, "P6_STAGE_RELEASE_VALIDATED"),
            ("p8", P8_VALIDATOR, "P8_STAGE_RELEASE_VALIDATED"),
            ("p9", P9_VALIDATOR, "P9_STAGE_RELEASE_VALIDATED"),
        )
    else:
        specs = (("p10", P10_VALIDATOR, "P10_STAGE_RELEASE_VALIDATED"),)
    out = {}
    for key, validator_path, expected in specs:
        path = repo_file(releases.get(key), key.upper() + " stage release")
        checker = checkers.get(key)
        result = checker(path) if checker else load(validator_path, "material_" + key).validate(path)
        if result.get("status") != expected or result.get("machine_release") != "HOLD":
            raise ValueError(key.upper() + " stage release is not a valid prerequisite")
        if key == "p9" and result.get("p10_entry_prerequisite") is not True:
            raise ValueError("P9 release does not unlock P10 entry review")
        if key == "p10" and result.get("p11_entry_prerequisite") is not True:
            raise ValueError("P10 release does not unlock P11 entry review")
        if result.get("material_feed_authorized", False) is not False:
            raise ValueError(key.upper() + " release authorization semantics drift")
        out[key + "_release_sha256"] = sha(path)
    return out


def authenticate_run_context(rows: list[dict[str, str]], stage: str) -> dict:
    first = rows[0]
    expected_material = EXPECTED_MATERIAL[stage]
    if any(row.get("material", "").strip() != expected_material for row in rows):
        raise ValueError("material does not match requested stage")
    stable_fields = ("lot_id", "drying_record", "drying_record_sha256", "material_feed_approval_path",
                     "material_feed_approval_sha256", "material_feed_approval_scope", "operator", "reviewer")
    for field in stable_fields:
        value = first.get(field, "").strip()
        if not value or any(row.get(field, "").strip() != value for row in rows):
            raise ValueError(field + " must be nonblank and constant for the run")
    if first["operator"].strip() == first["reviewer"].strip():
        raise ValueError("independent reviewer must differ from operator")
    if first["material_feed_approval_scope"].strip() != APPROVAL_SCOPE[stage]:
        raise ValueError("material-feed approval scope mismatch")
    drying = repo_file(first["drying_record"], "drying record")
    approval = repo_file(first["material_feed_approval_path"], "material-feed approval record")
    if first["drying_record_sha256"].strip().lower() != sha(drying):
        raise ValueError("drying record hash mismatch")
    if first["material_feed_approval_sha256"].strip().lower() != sha(approval):
        raise ValueError("material-feed approval hash mismatch")
    return {
        "material": expected_material,
        "lot_id": first["lot_id"].strip(),
        "drying_record_sha256": sha(drying),
        "material_feed_approval_sha256": sha(approval),
        "material_feed_approval_scope": APPROVAL_SCOPE[stage],
        "operator": first["operator"].strip(),
        "reviewer": first["reviewer"].strip(),
    }


def authenticate_sample(row: dict[str, str], index: int) -> datetime.datetime:
    required = ("sample_id", "measured_at", "logger_id", "logger_calibration_ref", "diameter_gauge_id",
                "diameter_calibration_ref", "torque_calibration_ref", "current_calibration_ref",
                "raw_evidence_path", "raw_evidence_sha256")
    missing = [field for field in required if not row.get(field, "").strip()]
    if missing:
        raise ValueError(f"sample {index} provenance incomplete: " + ",".join(missing))
    measured_at = stamp(row["measured_at"], f"sample {index} measured_at")
    evidence = repo_file(row["raw_evidence_path"], f"sample {index} raw evidence")
    if row["raw_evidence_sha256"].strip().lower() != sha(evidence):
        raise ValueError(f"sample {index} raw evidence hash mismatch")
    return measured_at


def evaluate(record: Path, stage: str, releases: dict[str, Path | None], checkers=None) -> dict:
    out = {"status": "NOT_RUN_OR_REJECTED", "stage": stage, "stage_pass": False,
           "next_stage_entry_prerequisite": False, "material_feed_authorized": False,
           "continuing_power_authority": False, "machine_release": "HOLD"}
    try:
        if stage not in EXPECTED_MATERIAL:
            raise ValueError("stage must be P10 or P11")
        record = repo_file(record, stage + " material record")
        with record.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) < 20:
            raise ValueError("fewer than 20 samples")
        context = authenticate_run_context(rows, stage)
        prerequisites = validate_prerequisites(stage, releases, checkers=checkers)
        targets = profile_targets()[context["material"]]
        start_rpm = number(rows[0].get("screw_rpm"), "start screw rpm")
        if not 8.0 <= start_rpm <= 10.0:
            raise ValueError("start screw rpm outside 8-10")

        cooked = []
        previous_elapsed = -1.0
        previous_mass = -1.0
        previous_stamp = None
        torque_trip_count = 0
        for index, row in enumerate(rows):
            measured_at = authenticate_sample(row, index)
            if previous_stamp is not None and measured_at <= previous_stamp:
                raise ValueError("sample measured_at values must increase")
            previous_stamp = measured_at
            elapsed = number(row.get("elapsed_s"), f"sample {index} elapsed_s")
            mass = number(row.get("cumulative_mass_g"), f"sample {index} cumulative_mass_g")
            if elapsed <= previous_elapsed or mass < previous_mass:
                raise ValueError("time/mass not monotonic")
            previous_elapsed, previous_mass = elapsed, mass

            temp_u95 = number(row.get("temperature_u95_c"), f"sample {index} temperature U95")
            if temp_u95 < 0:
                raise ValueError("negative temperature U95")
            temps = [number(row.get(key), f"sample {index} {key}") for key in ("zone1_c", "zone2_c", "zone3_c", "die_c")]
            temp_ok = all(value - temp_u95 >= target - 5.0 and value + temp_u95 <= target + 5.0
                          for value, target in zip(temps, targets))

            x = number(row.get("diameter_x_mm"), f"sample {index} diameter_x")
            y = number(row.get("diameter_y_mm"), f"sample {index} diameter_y")
            diameter_u95 = number(row.get("diameter_u95_mm"), f"sample {index} diameter U95")
            torque = number(row.get("gearbox_torque_nm"), f"sample {index} torque")
            torque_u95 = number(row.get("gearbox_torque_u95_nm"), f"sample {index} torque U95")
            current = number(row.get("motor_current_a"), f"sample {index} current")
            current_u95 = number(row.get("motor_current_u95_a"), f"sample {index} current U95")
            if min(diameter_u95, torque, torque_u95, current, current_u95) < 0:
                raise ValueError(f"sample {index}: negative physical value or U95")
            mean_diameter = (x + y) / 2.0
            ovality = abs(x - y)
            torque_ok = torque + torque_u95 < 8.0
            current_ok = current + current_u95 <= 6.0
            hazards = any(yes(row.get(key)) for key in ("leak", "pressure_symptom", "guard_contact"))
            torque_trip = yes(row.get("torque_trip"))
            if torque_trip:
                torque_trip_count += 1
            stable = (yes(row.get("stable_candidate")) and temp_ok and diameter_u95 <= 0.03 and
                      ovality <= 0.05 and not hazards and not torque_trip and torque_ok and current_ok)
            cooked.append({
                "index": index,
                "elapsed_s": elapsed,
                "mass_g": mass,
                "mean_diameter_mm": mean_diameter,
                "ovality_mm": ovality,
                "diameter_u95_mm": diameter_u95,
                "torque_nm": torque,
                "torque_plus_u95_nm": torque + torque_u95,
                "current_a": current,
                "current_plus_u95_a": current + current_u95,
                "temperature_ok": temp_ok,
                "stable": stable,
            })
        if torque_trip_count > 1:
            raise ValueError("repeated torque trips are not an accepted control mode")

        found = None
        for start in range(len(cooked) - 19):
            window = cooked[start:start + 20]
            if not all(sample["stable"] for sample in window):
                continue
            mean_diameter = sum(sample["mean_diameter_mm"] for sample in window) / 20.0
            if abs(mean_diameter - 1.75) <= 0.05:
                found = (start, window, mean_diameter)
                break
        if found is None:
            raise ValueError("no 20-consecutive-sample stable window")

        start, window, mean_diameter = found
        delta_t = window[-1]["elapsed_s"] - window[0]["elapsed_s"]
        delta_mass = window[-1]["mass_g"] - window[0]["mass_g"]
        if delta_t <= 0 or delta_mass < 0:
            raise ValueError("invalid stable throughput interval")
        throughput = delta_mass / delta_t * 3600.0
        out.update({
            "status": "MATERIAL_RUN_RECORD_CHECK_PASS",
            "material": context["material"],
            "record_sha256": sha(record),
            "context": context,
            "prerequisites": prerequisites,
            "profile_source_sha256": sha(PROFILE_SOURCE),
            "stable_window_start_index": start,
            "stable_window_end_index": start + 19,
            "mean_diameter_mm": mean_diameter,
            "mean_error_mm": abs(mean_diameter - 1.75),
            "max_ovality_mm": max(sample["ovality_mm"] for sample in window),
            "max_diameter_u95_mm": max(sample["diameter_u95_mm"] for sample in window),
            "max_torque_plus_u95_nm": max(sample["torque_plus_u95_nm"] for sample in window),
            "max_current_plus_u95_a": max(sample["current_plus_u95_a"] for sample in window),
            "stable_throughput_g_h": throughput,
            "stage_pass": False,
            "next_stage_entry_prerequisite": False,
            "material_feed_authorized": False,
            "continuing_power_authority": False,
            "machine_release": "HOLD",
            "note": "Authenticated bounded material-run evidence passed. Separate reviewed stage release is required.",
        })
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        out["reason"] = str(exc)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    ap.add_argument("--stage", choices=("P10", "P11"), required=True)
    ap.add_argument("--p4-release", type=Path)
    ap.add_argument("--p6-release", type=Path)
    ap.add_argument("--p8-release", type=Path)
    ap.add_argument("--p9-release", type=Path)
    ap.add_argument("--p10-release", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    releases = {
        "p4": args.p4_release,
        "p6": args.p6_release,
        "p8": args.p8_release,
        "p9": args.p9_release,
        "p10": args.p10_release,
    }
    result = evaluate(args.record, args.stage, releases)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "MATERIAL_RUN_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__":
    main()
