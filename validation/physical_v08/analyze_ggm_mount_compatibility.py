#!/usr/bin/env python3
"""Convert authenticated GGM receipt geometry into an as-drawn mount compatibility decision.

This is an offline arithmetic gate only. It never authorizes drilling, fabrication,
purchase, or energization. A PASS means the received gearbox can be aligned to the
existing D02/D03 mount geometry using the released bolt-hole clearance budget.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSPECTION_PATH = ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py"
CONTROL = ROOT / "control/ggm_drive_contract.json"
DRAWING = ROOT / "analysis/drive_acceptance_v08/manufacturing/drawing_contract.json"

NOMINAL_PCD_MM = 104.0
NOMINAL_OUTPUT_OFFSET_MM = 18.0
MOUNT_HOLE_MIN_MM = 6.60
M6_SHANK_MAX_MM = 6.00
HOLE_POSITION_TOL_MM = 0.10
AVAILABLE_CENTER_MISMATCH_MM = (MOUNT_HOLE_MIN_MM - M6_SHANK_MAX_MM) / 2.0 - HOLE_POSITION_TOL_MM


def _load_inspection():
    spec = importlib.util.spec_from_file_location("ppr_ggm_inspection", INSPECTION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load GGM inspection module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _interval(row: dict) -> tuple[float, float]:
    value = float(row["value"])
    u95 = float(row["u95"])
    if not math.isfinite(value) or not math.isfinite(u95) or u95 < 0:
        raise ValueError("invalid measurement interval")
    return value - u95, value + u95


def bolt_pattern_mismatch_mm(pcd_mm: float, output_offset_mm: float) -> float:
    """Worst bolt-centre mismatch after translating the gearbox to align its output shaft."""
    da = (pcd_mm - NOMINAL_PCD_MM) / (2.0 * math.sqrt(2.0))
    dy = -(output_offset_mm - NOMINAL_OUTPUT_OFFSET_MM)
    return max(
        math.hypot(sx * da, dy + sy * da)
        for sx in (-1.0, 1.0)
        for sy in (-1.0, 1.0)
    )


def axis_compatibility(record: dict) -> dict:
    pcd_lo, pcd_hi = _interval(record["readings"]["bolt_pcd"])
    off_lo, off_hi = _interval(record["readings"]["output_offset"])
    candidates = [
        bolt_pattern_mismatch_mm(pcd, off)
        for pcd in (pcd_lo, pcd_hi)
        for off in (off_lo, off_hi)
    ]
    worst = max(candidates)
    shaft_lo, shaft_hi = _interval(record["readings"]["shaft_diameter"])
    projection_lo, projection_hi = _interval(record["readings"]["shaft_projection"])
    return {
        "part_serial": record["part_serial"],
        "pcd_u95_interval_mm": [pcd_lo, pcd_hi],
        "output_offset_u95_interval_mm": [off_lo, off_hi],
        "worst_bolt_center_mismatch_mm": worst,
        "available_center_mismatch_mm": AVAILABLE_CENTER_MISMATCH_MM,
        "bolt_alignment_margin_mm": AVAILABLE_CENTER_MISMATCH_MM - worst,
        "shaft_diameter_u95_interval_mm": [shaft_lo, shaft_hi],
        "hub_diametral_clearance_interval_mm": [12.05 - shaft_hi, 12.06 - shaft_lo],
        "shaft_projection_u95_interval_mm": [projection_lo, projection_hi],
        "as_drawn_compatible": worst <= AVAILABLE_CENTER_MISMATCH_MM + 1e-12,
    }


def evaluate(packet: dict) -> dict:
    result = {
        "status": "NOT_RUN",
        "drilling_authorized": False,
        "fabrication_authorized": False,
        "cad_regeneration_performed": False,
        "mount_redesign_required": None,
        "basis": {
            "drawing_mount_hole_min_mm": MOUNT_HOLE_MIN_MM,
            "assumed_m6_shank_max_mm": M6_SHANK_MAX_MM,
            "hole_position_tolerance_mm": HOLE_POSITION_TOL_MM,
            "available_center_mismatch_mm": AVAILABLE_CENTER_MISMATCH_MM,
            "nominal_pcd_mm": NOMINAL_PCD_MM,
            "nominal_output_offset_mm": NOMINAL_OUTPUT_OFFSET_MM,
        },
        "axes": {},
    }
    receipt = packet.get("receipt", {})
    if receipt.get("performed") is not True:
        result["reason"] = "GGM receipt measurements are NOT_RUN"
        return result
    bindings = packet.get("design_sha256", {})
    expected = {
        "control/ggm_drive_contract.json": _sha(CONTROL),
        "analysis/drive_acceptance_v08/manufacturing/drawing_contract.json": _sha(DRAWING),
    }
    stale = [name for name, digest in expected.items() if bindings.get(name) != digest]
    if stale:
        result.update(status="BLOCKED_STALE_DESIGN_BINDING", mount_redesign_required=True, reason="stale design binding: " + ", ".join(stale))
        return result
    inspection = _load_inspection()
    axes = {}
    seen_serials = set()
    try:
        for axis, gear in (("SH", "K9G75C"), ("EX", "K9G150C")):
            record = receipt["data"][axis]
            inspection.evidence(record)
            if record.get("motor_model") != "K9DG60N2" or record.get("gear_model") != gear:
                raise ValueError(f"{axis}: wrong motor/gear identity")
            serial = record.get("part_serial")
            if serial in seen_serials:
                raise ValueError("duplicate motor identity")
            seen_serials.add(serial)
            row = axis_compatibility(record)
            dimensional = {}
            for name, limits in inspection.RECEIPT.items():
                try:
                    inspection.interval(record["readings"][name], *limits)
                    dimensional[name] = True
                except ValueError:
                    dimensional[name] = False
            row["receipt_dimension_conformance"] = dimensional
            row["all_receipt_dimensions_conform"] = all(dimensional.values())
            axes[axis] = row
    except (KeyError, TypeError, ValueError) as exc:
        result.update(status="BLOCKED_RECEIPT_REJECTED", mount_redesign_required=True, reason=str(exc))
        return result
    bolt_fit = all(row["as_drawn_compatible"] for row in axes.values())
    dimensions_fit = all(row["all_receipt_dimensions_conform"] for row in axes.values())
    compatible = bolt_fit and dimensions_fit
    result["axes"] = axes
    result["mount_redesign_required"] = not compatible
    result["status"] = "AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED" if compatible else "HOLD_REDRAW_REQUIRED"
    result["reason"] = (
        "received geometry conforms to the current receipt envelope and D02/D03 bolt-clearance budget"
        if compatible else
        "received geometry requires engineering review before D02/D03 drilling; see per-axis conformance and bolt margin"
    )
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("packet", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = evaluate(json.loads(args.packet.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(2 if result["status"].startswith("BLOCKED") or result["status"] == "HOLD_REDRAW_REQUIRED" else 0)


if __name__ == "__main__":
    main()
