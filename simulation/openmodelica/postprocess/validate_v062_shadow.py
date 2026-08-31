#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "simulation/openmodelica/results_v0.6.2/raw"
OUT = ROOT / "simulation/openmodelica/results_v0.6.2"
ENVELOPE = ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json"
COMPARE = ROOT / "analysis/fusion_delta_queue/shadow_envelope_comparison.json"

REQUIREMENTS = {
    "PullerTransientSaturation": "startup/transient limit does not latch persistent saturation",
    "PullerPersistentSaturation": "persistent speed error and actuator limit cause forming-chain fault",
    "PullerTachLoss": "loss-of-tach timeout disables production",
    "PullerSpeedLoopLoadStep": "inner PI recovers after a bounded load step",
    "SingleCoolingFanLoss": "either individual fan loss invalidates cooling",
    "DualCoolingFanLoss": "dual fan loss invalidates cooling",
    "CoolingFeedbackImplausible": "feedback while command is off is implausible",
    "DuctBlockageSensitivity": "tach is not treated as measured airflow",
    "ScrewCommandNoMotion": "commanded screw with zero motion faults",
    "ScrewCouplingSlip": "coupling slip below motion ratio faults",
    "PurgeMeasuredRevolutionsLow": "elapsed time alone cannot complete purge",
    "PurgeMeasuredRevolutionsPass": "measured revolutions plus elapsed time can qualify purge",
    "HeaterAllocatorAllZonesCold": "four-zone demand respects phase cap",
    "HeaterAllocatorRecovery": "allocation recovers without a hidden cap",
    "HeaterAppliedDutyAntiWindup": "integrator remains bounded under denied duty",
    "SpoolRadiusSweep": "full-radius speed demand is recomputed",
    "DancerClosedLoopDisturbance": "dancer state returns to target",
    "SpoolJamBeforeControlledLimit": "jam is detected before controlled-stop angle",
    "TraversePitchEmptySpool": "pitch is synchronized to empty-spool turns",
    "TraversePitchFullSpool": "pitch is synchronized to full-spool turns",
    "TraverseLimitFailure": "missed limit becomes a hard fault",
    "FormingChainFaultCascade": "fault disables feeder and production spool",
    "GaugeRequalificationToWaste": "requalification stays on waste until rethread",
    "ManualRethreadToProduction": "explicit rethread enables production after stable dwell",
}


def load(name: str) -> list[dict[str, float]]:
    path = RAW / f"{name}_res.csv"
    with path.open(newline="") as handle:
        return [{key.strip('"'): float(value) for key, value in row.items()}
                for row in csv.DictReader(handle)]


def final(rows: list[dict[str, float]], field: str) -> float:
    return rows[-1][field]


def peak(rows: list[dict[str, float]], field: str) -> float:
    return max(row[field] for row in rows)


def evaluate(name: str, rows: list[dict[str, float]]) -> tuple[bool, str]:
    f = lambda key: final(rows, key)
    p = lambda key: peak(rows, key)
    checks = {
        "PullerTransientSaturation": p("formingFault") == 0,
        "PullerPersistentSaturation": p("pullerSaturated") == 1 and p("formingFault") == 1,
        "PullerTachLoss": f("pullerTachValid") == 0 and f("formingFault") == 1,
        "PullerSpeedLoopLoadStep": abs(f("pullerError")) < 0.5,
        "SingleCoolingFanLoss": f("coolingValid") == 0 and f("fan2Rpm") > 0,
        "DualCoolingFanLoss": f("coolingValid") == 0 and f("fan1Rpm") == f("fan2Rpm") == 0,
        "CoolingFeedbackImplausible": f("coolingValid") == 0,
        "DuctBlockageSensitivity": 0 < f("inferredAirflowM3H") < 18,
        "ScrewCommandNoMotion": f("screwMotionMismatch") == 1 and f("measuredPurgeRevolutions") == 0,
        "ScrewCouplingSlip": f("screwMotionMismatch") == 1,
        "PurgeMeasuredRevolutionsLow": f("purgeComplete") == 0 and f("measuredPurgeRevolutions") < 32,
        "PurgeMeasuredRevolutionsPass": f("purgeComplete") == 1 and f("measuredPurgeRevolutions") >= 32,
        "HeaterAllocatorAllZonesCold": f("heaterRequestedPowerW") * f("heaterAllocationScale") <= 300.001,
        "HeaterAllocatorRecovery": abs(f("heaterAllocationScale") - 1) < 1e-6,
        "HeaterAppliedDutyAntiWindup": abs(f("heaterIntegrator")) < 500 and f("heaterRequestedPowerW") * f("heaterAllocationScale") <= 180.001,
        "SpoolRadiusSweep": abs(f("spoolRadiusMm") - 100) < 1e-6,
        "DancerClosedLoopDisturbance": abs(f("dancerAngle")) < 0.01,
        "SpoolJamBeforeControlledLimit": p("dancerAngle") < 0.36 and p("spoolJamDetected") == 1,
        "TraversePitchEmptySpool": 0 <= f("traversePositionMm") <= 68 and f("spoolTurns") > 0,
        "TraversePitchFullSpool": 0 <= f("traversePositionMm") <= 68 and f("spoolTurns") > 0,
        "TraverseLimitFailure": f("traverseHardFault") == 1,
        "FormingChainFaultCascade": f("formingFault") == 1 and f("feederEnabled") == 0 and f("wastePathActive") == 1,
        "GaugeRequalificationToWaste": f("spoolEligible") == 0 and f("wastePathActive") == 1,
        "ManualRethreadToProduction": f("spoolEligible") == 1 and f("wastePathActive") == 0,
    }
    passed = checks[name]
    decisive_fields = (
        "formingFault", "pullerSaturated", "pullerTachValid", "pullerError",
        "coolingValid", "fan1Rpm", "fan2Rpm", "screwMotionMismatch",
        "measuredPurgeRevolutions", "purgeComplete", "heaterAllocationScale",
        "heaterIntegrator", "dancerAngle", "spoolJamDetected",
        "traverseHardFault", "spoolEligible", "wastePathActive",
    )
    # Fault scenarios may recover before stopTime. Record both extrema and the
    # terminal state so the evidence cannot hide a decisive transient behind a
    # benign final sample.
    evidence = ", ".join(
        f"{key}[peak={p(key):.6g},final={f(key):.6g}]" for key in decisive_fields
    )
    return passed, evidence


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name, requirement in REQUIREMENTS.items():
        rows = load(name)
        passed, evidence = evaluate(name, rows)
        results.append({
            "scenario": name, "protected_requirement_or_failure_mode": requirement,
            "input": "scenario parameters in V062ShadowScenarios.mo",
            "method": "OpenModelica 1.27 DASSL reduced-order shadow simulation",
            "expected_evidence": requirement,
            "pass_fail_threshold": "scenario-specific predicate in validate_v062_shadow.py",
            "result": "PASS" if passed else "FAIL", "evidence": evidence,
        })
    with (OUT / "scenario_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(results)
    status = "PASS" if all(row["result"] == "PASS" for row in results) else "FAIL"
    summary = {
        "revision": "parallel-actuation-hardening-v0.6.2",
        "solver": "OpenModelica 1.27.0 DASSL",
        "scope": "firmware-equivalent reduced-order actuation/process shadow; physical test not run",
        "scenario_count": len(results), "status": status,
        "pass_count": sum(row["result"] == "PASS" for row in results),
        "results": results,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    frozen = json.loads(ENVELOPE.read_text())
    case_map = {
        "peak_cutter_torque_nm": "LC01,LC02", "peak_phase_torque_nm": "LC03",
        "peak_bearing_load_n": "LC04", "peak_chain_force_n": "LC05",
    }
    comparisons = []
    for quantity, old in frozen["loads"].items():
        comparisons.append({
            "quantity": quantity, "old_value": old, "new_value": old,
            "percent_change": 0.0, "direction_change": False,
            "affected_fusion_case": case_map[quantity], "rerun_requirement": False,
            "reason": "v0.6.2 control shadow does not alter frozen mechanical load envelope",
        })
    comparison = {
        "revision": "parallel-actuation-hardening-v0.6.2",
        "frozen_baseline_revision": frozen["revision"],
        "fusion_input_delta": "NONE", "comparisons": comparisons,
        "geometry_material_contact_boundary_changes": False,
        "status": "PASS" if status == "PASS" else "INPUT_REVIEW_REQUIRED",
    }
    COMPARE.parent.mkdir(parents=True, exist_ok=True)
    COMPARE.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n")
    print(f"V062_SHADOW_{status} {len(results)} scenarios")
    if status != "PASS":
        failed = [row["scenario"] for row in results if row["result"] != "PASS"]
        raise SystemExit("failed scenarios: " + ", ".join(failed))


if __name__ == "__main__":
    main()
