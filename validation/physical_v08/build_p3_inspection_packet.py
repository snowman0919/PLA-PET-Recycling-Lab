#!/usr/bin/env python3
"""Build the authoritative GGM inspection packet from authenticated P3 field CSVs.

The builder only transforms already-recorded evidence. It preserves the source packet's
physical-authorization flag and cannot grant motor energization or stage release.
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
CONTROL = ROOT / "control/ggm_drive_contract.json"
DRAWING = ROOT / "analysis/drive_acceptance_v08/manufacturing/drawing_contract.json"
INSPECTION = ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py"
PREFLIGHT = ROOT / "validation/physical_v08/analyze_p3_preflight.py"



def load_inspection():
    spec = importlib.util.spec_from_file_location("ppr_ggm_inspection_builder", INSPECTION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load GGM inspection module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_preflight():
    spec = importlib.util.spec_from_file_location("ppr_p3_preflight_builder", PREFLIGHT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P3 preflight module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_preflight(preflight_path: Path, receipt_packet_path: Path) -> dict:
    preflight_path = preflight_path.resolve(); receipt_packet_path = receipt_packet_path.resolve()
    for path, name in ((preflight_path, "preflight result"), (receipt_packet_path, "receipt packet")):
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(name + " must be an existing file inside the repository")
    result = json.loads(preflight_path.read_text(encoding="utf-8"))
    load_preflight().validate_result(result, ROOT)
    receipt_digest = sha(receipt_packet_path)
    if result.get("receipt_packet_sha256") != receipt_digest:
        raise ValueError("P3 preflight was not evaluated against this exact receipt packet")
    return {
        "performed": True,
        "result_path": str(preflight_path.relative_to(ROOT)),
        "result_sha256": sha(preflight_path),
        "receipt_packet_sha256": receipt_digest,
        "status": result["status"],
        "p0_snapshot_head": result["p0_snapshot_head"],
        "p0_runtime_digest": result["p0_runtime_digest"],
        "motor_energization_authorized": False,
        "stage_p3_pass": False,
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def number(value: str, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(f"blank {field}")
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"non-finite {field}")
    return x


def verify_evidence(row: dict[str, str], required: tuple[str, ...]) -> tuple[str, str]:
    ident = row.get("sample_id") or row.get("coupon_id") or row.get("point") or row.get("trial") or "row"
    for field in ("evidence_path", "sha256", "operator", "measured_at", *required):
        if not row.get(field, "").strip():
            raise ValueError(f"{ident}: missing {field}")
    datetime.datetime.fromisoformat(row["measured_at"].replace("Z", "+00:00"))
    path = (ROOT / row["evidence_path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"{ident}: invalid evidence path")
    digest = row["sha256"].lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError(f"{ident}: stale evidence hash")
    return row["evidence_path"], digest


def merged_meta(rows: list[dict[str, str]], part_serial: str, instrument_fields: tuple[str, ...], calibration_fields: tuple[str, ...]) -> dict:
    raw_files = {}
    for row in rows:
        path, digest = verify_evidence(row, instrument_fields + calibration_fields)
        if path in raw_files and raw_files[path] != digest:
            raise ValueError("conflicting digest for " + path)
        raw_files[path] = digest
    instruments = sorted({row[field].strip() for row in rows for field in instrument_fields})
    calibrations = sorted({row[field].strip() for row in rows for field in calibration_fields})
    operators = sorted({row["operator"].strip() for row in rows})
    timestamps = sorted(row["measured_at"].strip() for row in rows)
    return {
        "performed": True,
        "kind": "PHYSICAL_MEASUREMENT",
        "operator": ";".join(operators),
        "part_serial": part_serial,
        "instrument_id": ";".join(instruments),
        "instrument_calibration_ref": ";".join(calibrations),
        "measured_at": timestamps[-1],
        "raw_files": raw_files,
    }


def torque_from_row(row: dict[str, str]) -> tuple[float, float]:
    force = number(row["force_n"], "force_n")
    u_force = number(row["u95_force_n"], "u95_force_n")
    arm = number(row["arm_mm"], "arm_mm")
    u_arm = number(row["u95_arm_mm"], "u95_arm_mm")
    if u_force < 0 or u_arm < 0 or arm <= 0:
        raise ValueError("invalid force/arm interval")
    torque = force * arm / 1000.0
    u_torque = math.hypot((arm / 1000.0) * u_force, force * (u_arm / 1000.0))
    return torque, u_torque


def check_bindings(packet: dict) -> None:
    expected = {
        "control/ggm_drive_contract.json": sha(CONTROL),
        "analysis/drive_acceptance_v08/manufacturing/drawing_contract.json": sha(DRAWING),
    }
    stale = [name for name, digest in expected.items() if packet.get("design_sha256", {}).get(name) != digest]
    if stale:
        raise ValueError("source receipt packet has stale design binding: " + ", ".join(stale))


def build(receipt_packet: dict, records_dir: Path, preflight_binding: dict) -> dict:
    check_bindings(receipt_packet)
    if preflight_binding.get("performed") is not True or preflight_binding.get("status") != "PREPOWER_RECORD_CHECK_PASS":
        raise ValueError("authenticated P3 preflight binding required")
    if preflight_binding.get("motor_energization_authorized") is not False or preflight_binding.get("stage_p3_pass") is not False:
        raise ValueError("P3 preflight binding has invalid authorization semantics")
    receipt = receipt_packet.get("receipt", {})
    if receipt.get("performed") is not True:
        raise ValueError("GGM receipt domain is not performed")
    receipt_data = receipt.get("data", {})
    for axis in ("SH", "EX"):
        if receipt_data.get(axis, {}).get("performed") is not True or not receipt_data[axis].get("part_serial"):
            raise ValueError(f"{axis}: authenticated receipt record required")
    load_inspection().receipt(receipt_data)

    current_rows = read_rows(records_dir / "p3_current_sensor_calibration.csv")
    no_load_rows = read_rows(records_dir / "p3_no_load.csv")
    torque_rows = read_rows(records_dir / "p3_torque_map.csv")
    pin_rows = read_rows(records_dir / "p3_pin_release.csv")
    result = json.loads(json.dumps(receipt_packet))

    current_data = {}
    for axis in ("SH", "EX"):
        cur = [row for row in current_rows if row.get("axis") == axis]
        idle = [row for row in no_load_rows if row.get("axis") == axis]
        loads = [row for row in torque_rows if row.get("axis") == axis]
        if len(cur) < 5 or len(idle) < 3 or len(loads) < 8:
            raise ValueError(f"{axis}: incomplete P3 current/no-load/torque rows")
        # The three CSV families use different instrument column names, so merge explicitly.
        raw_files = {}; operators = set(); timestamps = []; instruments = set(); calibrations = set()
        for row in cur:
            path, digest = verify_evidence(row, ("instrument_id", "calibration_ref")); raw_files[path] = digest
            instruments.add(row["instrument_id"]); calibrations.add(row["calibration_ref"]); operators.add(row["operator"]); timestamps.append(row["measured_at"])
        for row in idle:
            path, digest = verify_evidence(row, ("tach_id", "tach_calibration_ref", "current_ref_id", "current_ref_calibration_ref")); raw_files[path] = digest
            instruments.update((row["tach_id"], row["current_ref_id"])); calibrations.update((row["tach_calibration_ref"], row["current_ref_calibration_ref"])); operators.add(row["operator"]); timestamps.append(row["measured_at"])
        for row in loads:
            path, digest = verify_evidence(row, ("force_ref_id", "force_calibration_ref", "tach_id", "tach_calibration_ref", "arm_instrument_id", "arm_calibration_ref")); raw_files[path] = digest
            instruments.update((row["force_ref_id"], row["tach_id"], row["arm_instrument_id"])); calibrations.update((row["force_calibration_ref"], row["tach_calibration_ref"], row["arm_calibration_ref"])); operators.add(row["operator"]); timestamps.append(row["measured_at"])
        record = {
            "performed": True, "kind": "PHYSICAL_MEASUREMENT", "operator": ";".join(sorted(operators)),
            "part_serial": receipt_data[axis]["part_serial"], "instrument_id": ";".join(sorted(instruments)),
            "instrument_calibration_ref": ";".join(sorted(calibrations)), "measured_at": sorted(timestamps)[-1],
            "raw_files": raw_files, "current_location": "motor_lead",
            "units": {"current": "A", "torque": "N.m", "speed": "rpm", "adc": "count"},
            "adc_samples": [{"adc": number(row["adc_count"], "adc_count"), "reference_a": number(row["reference_current_a"], "reference_current_a"), "u95_a": number(row["u95_a"], "u95_a")} for row in cur],
            "no_load_a": [number(row["reference_current_a"], "reference_current_a") for row in idle],
            "no_load_samples": [{
                "trial": row["trial"], "direction": row["direction"], "output_rpm": number(row["output_rpm"], "output_rpm"),
                "reference_current_a": number(row["reference_current_a"], "reference_current_a"),
                "motor_case_c": number(row["motor_case_c"], "motor_case_c"), "gear_case_c": number(row["gear_case_c"], "gear_case_c"),
                "duration_s": number(row["duration_s"], "duration_s"), "observation": row.get("observation", ""),
            } for row in idle],
            "torque_samples": [],
        }
        for row in loads:
            torque, u_torque = torque_from_row(row)
            record["torque_samples"].append({
                "sample_id": row["sample_id"], "subset": row["subset"], "adc": number(row["adc_count"], "adc_count"),
                "reference_nm": torque, "u95_nm": u_torque, "rpm": number(row["rpm"], "rpm"), "direction": row["direction"],
                "target_nm": number(row["target_nm"], "target_nm"), "drum_temp_c": number(row["drum_temp_c"], "drum_temp_c"),
            })
        current_data[axis] = record
    result["current_calibration"] = {"performed": True, "data": current_data}

    pin_meta = merged_meta(pin_rows, "P3-PROTECTION-COUPLING", ("force_ref_id", "arm_instrument_id"), ("force_calibration_ref", "arm_calibration_ref"))
    samples = []
    for row in pin_rows:
        if not row.get("material_lot", "").strip() or not row.get("drawing_revision", "").strip():
            raise ValueError(row.get("coupon_id", "pin") + ": missing coupon binding")
        torque, u_torque = torque_from_row(row)
        if row.get("calculated_release_nm", "").strip() and abs(number(row["calculated_release_nm"], "calculated_release_nm") - torque) > 0.01:
            raise ValueError(row["coupon_id"] + ": recorded torque differs from force x arm")
        if row.get("u95_nm", "").strip() and abs(number(row["u95_nm"], "u95_nm") - u_torque) > 0.01:
            raise ValueError(row["coupon_id"] + ": recorded torque U95 differs from propagated value")
        samples.append({
            "axis": row["axis"], "direction": row["direction"], "coupon_id": row["coupon_id"],
            "material_lot": row["material_lot"], "drawing_revision": row["drawing_revision"],
            "neck_diameter_mm": number(row["neck_diameter_mm"], "neck_diameter_mm"),
            "free_after_release": row["free_after_release"], "hub_key_damage": row["hub_key_damage"],
            "release_torque": {"value": torque, "u95": u_torque, "unit": "N.m"},
        })
    pin_meta["samples"] = samples
    result["protection_pin"] = {"performed": True, "data": pin_meta}
    result["p3_preflight"] = dict(preflight_binding)
    result["record_status"] = "P3_RECORDS_COMPILED_NOT_STAGE_RELEASE"
    result["packet_builder"] = {
        "source": "validation/physical_v08/build_p3_inspection_packet.py",
        "records_dir": str(records_dir),
        "physical_authorization_preserved": bool(receipt_packet.get("all_physical_actions_authorized") is True),
        "stage_release_granted": False,
    }
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt-packet", type=Path, required=True)
    ap.add_argument("--records-dir", type=Path, required=True)
    ap.add_argument("--preflight-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    packet = json.loads(args.receipt_packet.read_text(encoding="utf-8"))
    preflight_binding = bind_preflight(args.preflight_result, args.receipt_packet)
    result = build(packet, args.records_dir, preflight_binding)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P3_INSPECTION_PACKET_BUILT authorization_preserved=%s stage_release=false" % str(result["packet_builder"]["physical_authorization_preserved"]).lower())


if __name__ == "__main__":
    main()
