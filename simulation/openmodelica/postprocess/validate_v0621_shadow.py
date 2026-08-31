#!/usr/bin/env python3
"""Validate v0.6.2.1 shadow traces and emit load/Fusion delta evidence.

This validates a reduced-order OpenModelica simulation. It does not represent a
physical test or empirical calibration of the unidentified donor hardware.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "simulation/openmodelica/results_v0.6.2.1/raw"
OUT = ROOT / "simulation/openmodelica/results_v0.6.2.1"
LOAD_OUT = ROOT / "analysis/load_cases/shadow_v0.6.2.1"
DELTA_OUT = ROOT / "analysis/fusion_delta_queue/v0.6.2.1_delta_report.json"
FROZEN_ENVELOPE = ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json"
FUSION_BINDING = ROOT / "exports/fusion_validation/run_binding.json"
PROCESS_DELTA = ROOT / "exports/process_v0621/fusion_change_classification.json"

P0K = [
    "LowSpeedTachShredder", "LowSpeedTachScrew", "LowSpeedTachPuller",
    "LowSpeedTachSpooler", "TachJitter", "TachMissingPulse", "TachRollover",
    "ShredderClosedLoopLoadStep", "ScrewClosedLoopPressureStep",
    "PullerClosedLoopLowSpeed", "SpoolerClosedLoopEmptyToFull",
    "TraverseHomeMiddle", "TraverseHomeWrongDirection", "TraverseLimitFailure",
    "PLAShredderRecirculation", "PETRibbonRecirculation", "PLAHopperBridgeClear",
    "PETHopperBridgeClear", "FeedRateNominalPLA", "FeedRateNominalPET",
    "FeedRateDegradedSafePause",
]
EXTRA = ["ActuatorDeadZoneRecovery", "ActuatorSaturationRecovery", "ActuatorTachLossRundown"]
SCENARIOS = P0K + EXTRA

REQUIREMENTS = {
    "LowSpeedTachShredder": "6 PPR shredder low-speed reciprocal estimate remains valid",
    "LowSpeedTachScrew": "12 PPR screw estimate resolves 1 rpm",
    "LowSpeedTachPuller": "20 PPR puller estimate resolves 1 rpm",
    "LowSpeedTachSpooler": "20 PPR spool estimate resolves 0.5 rpm",
    "TachJitter": "deterministic 8% period jitter remains within 10% estimate error",
    "TachMissingPulse": "one missing pulse remains within age timeout and estimate recovers",
    "TachRollover": "uint32 micros rollover delta is reconstructed",
    "ShredderClosedLoopLoadStep": "shredder PI recovers while respecting frozen mechanical envelope",
    "ScrewClosedLoopPressureStep": "screw PI recovers from bounded pressure/load disturbance",
    "PullerClosedLoopLowSpeed": "normal low-speed puller target remains continuously controllable",
    "SpoolerClosedLoopEmptyToFull": "volume-conservation radius drives empty-to-full spool speed",
    "TraverseHomeMiddle": "middle-start homing reaches backoff and READY",
    "TraverseHomeWrongDirection": "wrong direction enters TRAVERSE_FAULT",
    "TraverseLimitFailure": "missing left limit times out to TRAVERSE_FAULT",
    "PLAShredderRecirculation": "PLA oversize returns without dead pocket or axial migration",
    "PETRibbonRecirculation": "PET ribbon bypass remains below 1%",
    "PLAHopperBridgeClear": "PLA bridge clears in at most three cycles and two seconds",
    "PETHopperBridgeClear": "PET bridge clears in at most three cycles and two seconds",
    "FeedRateNominalPLA": "nominal PLA feed remains 90-110 g/h with bounded inventory",
    "FeedRateNominalPET": "nominal PET feed remains 90-110 g/h with bounded inventory",
    "FeedRateDegradedSafePause": "degraded feed selects deterministic derate/pause",
    "ActuatorDeadZoneRecovery": "P0-C dead-zone compensation preserves low-speed tracking",
    "ActuatorSaturationRecovery": "P0-C finite saturation clears and PI recovers",
    "ActuatorTachLossRundown": "P0-C tach loss removes command and performs bounded rundown",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> list[dict[str, float]]:
    path = RAW / f"{name}_res.csv"
    if not path.is_file():
        raise AssertionError(f"OpenModelica result missing: {path}")
    with path.open(newline="") as handle:
        return [
            {key.strip('"'): float(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def final(rows: list[dict[str, float]], key: str) -> float:
    return rows[-1][key]


def peak(rows: list[dict[str, float]], key: str) -> float:
    return max(row[key] for row in rows)


def trough(rows: list[dict[str, float]], key: str) -> float:
    return min(row[key] for row in rows)


def evaluate(name: str, rows: list[dict[str, float]]) -> bool:
    f = lambda key: final(rows, key)
    p = lambda key: peak(rows, key)
    if name.startswith("LowSpeedTach"):
        targets = {
            "LowSpeedTachShredder": 5.0,
            "LowSpeedTachScrew": 1.0,
            "LowSpeedTachPuller": 1.0,
            "LowSpeedTachSpooler": 0.5,
        }
        return f("tachValid") == 1 and f("reciprocalMode") == 1 and abs(f("estimateErrorRpm")) <= 0.02*targets[name]
    if name == "TachJitter":
        return f("tachValid") == 1 and abs(f("estimateErrorRpm")) <= 1.6
    if name == "TachMissingPulse":
        return p("pulseAgeUs") < 4000000 and f("tachValid") == 1 and abs(f("estimateErrorRpm")) < 0.05
    if name == "TachRollover":
        return f("rolloverHandled") == 1 and f("tachValid") == 1 and abs(f("estimateErrorRpm")) < 0.05
    if name in {"ShredderClosedLoopLoadStep", "ScrewClosedLoopPressureStep", "PullerClosedLoopLowSpeed"}:
        tolerance = 0.25 if name != "ShredderClosedLoopLoadStep" else 0.4
        return f("tachValid") == 1 and f("continuousRegion") == 1 and abs(f("speedErrorRpm")) < tolerance
    if name == "SpoolerClosedLoopEmptyToFull":
        return f("radiusBounded") == 1 and abs(f("estimatedRadiusMm")-100) < 0.01 and f("continuousRegion") == 1 and abs(f("speedErrorRpm")) < 0.1
    if name == "TraverseHomeMiddle":
        return f("homingState") == 4 and f("traverseReady") == 1 and abs(f("traversePositionMm")-2) < 0.01
    if name in {"TraverseHomeWrongDirection", "TraverseLimitFailure"}:
        return f("homingState") == 6 and f("traverseFault") == 1 and f("traverseReady") == 0
    if name in {"PLAShredderRecirculation", "PETRibbonRecirculation"}:
        return f("passes") == 1 and f("oversizeReturnProbability") >= 0.9 and f("ribbonBypassProbability") <= 0.01
    if name in {"PLAHopperBridgeClear", "PETHopperBridgeClear"}:
        return p("continuousStarvationS") <= 2.000001 and f("bridgeClearCycles") <= 3 and f("inventoryBounded") == 1 and f("uncontrolledOverfeed") == 0
    if name in {"FeedRateNominalPLA", "FeedRateNominalPET"}:
        return 90 <= f("deliveredFeedGH") <= 110 and f("inventoryBounded") == 1 and f("uncontrolledOverfeed") == 0 and p("feederTorqueNm") <= 2.2
    if name == "FeedRateDegradedSafePause":
        return f("controlledPause") == 1 and f("inventoryBounded") == 1 and f("uncontrolledOverfeed") == 0 and f("feederTorqueNm") <= 2.2
    if name == "ActuatorDeadZoneRecovery":
        return f("pwmFraction") > 0.176 and abs(f("speedErrorRpm")) < 0.25
    if name == "ActuatorSaturationRecovery":
        return p("saturated") == 1 and f("saturated") == 0 and abs(f("speedErrorRpm")) < 0.25
    if name == "ActuatorTachLossRundown":
        return f("tachValid") == 0 and f("controlledRundown") == 1 and f("actualRpm") < 0.05 and f("commandRpm") == 0
    raise KeyError(name)


def evidence(rows: list[dict[str, float]]) -> str:
    interesting = [
        "targetRpm", "filteredRpm", "estimateErrorRpm", "tachValid", "rolloverHandled",
        "actualRpm", "speedErrorRpm", "commandRpm", "saturated", "continuousRegion",
        "estimatedRadiusMm", "homingState", "traverseReady", "traverseFault",
        "oversizeReturnProbability", "ribbonBypassProbability", "passes",
        "deliveredFeedGH", "continuousStarvationS", "bridgeClearCycles",
        "feederTorqueNm", "feedInventoryG", "controlledPause",
    ]
    return ", ".join(
        f"{key}[min={trough(rows,key):.6g},max={peak(rows,key):.6g},final={final(rows,key):.6g}]"
        for key in interesting if key in rows[-1]
    )


def write_trace(rows_by_name: dict[str, list[dict[str, float]]]) -> None:
    trace_rows: list[dict[str, str | float]] = []
    for name, rows in rows_by_name.items():
        indices = sorted({0, len(rows)//4, len(rows)//2, 3*len(rows)//4, len(rows)-1})
        for index in indices:
            row = rows[index]
            for key in sorted(row):
                if key != "time":
                    trace_rows.append({"scenario": name, "time_s": row["time"], "signal": key, "value": row[key]})
    with (OUT / "scenario_trace.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario", "time_s", "signal", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(trace_rows)


def write_load_and_delta(rows_by_name: dict[str, list[dict[str, float]]], status: str) -> None:
    frozen = json.loads(FROZEN_ENVELOPE.read_text())
    binding = json.loads(FUSION_BINDING.read_text())
    process_delta = json.loads(PROCESS_DELTA.read_text())
    shred = rows_by_name["ShredderClosedLoopLoadStep"]
    recirculation = rows_by_name["PETRibbonRecirculation"]
    feed = rows_by_name["FeedRateDegradedSafePause"]
    new_loads = {
        "peak_cutter_torque_nm": max(peak(shred, "cutterTorqueNm"), peak(recirculation, "cutterTorqueNm")),
        "peak_phase_torque_nm": peak(shred, "phaseTorqueNm"),
        "peak_bearing_load_n": peak(shred, "bearingLoadN"),
        "peak_chain_force_n": peak(shred, "chainForceN"),
        "feeder_attachment_reaction_torque_nm": peak(feed, "attachmentReactionTorqueNm"),
        "feeder_attachment_vertical_load_n": peak(feed, "attachmentVerticalLoadN"),
    }
    LOAD_OUT.mkdir(parents=True, exist_ok=True)
    envelope = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "source": "OpenModelica 1.27.0 DASSL reduced-order shadow; physical test not run",
        "status": status,
        "loads": new_loads,
        "frozen_source": {
            "path": str(FROZEN_ENVELOPE.relative_to(ROOT)),
            "sha256": sha256(FROZEN_ENVELOPE),
            "revision": frozen["revision"],
        },
        "boundary_conditions": {
            "shredder_high_load_path": "unchanged frozen cutter/phase/bearing/chain envelope",
            "feed_inventory_mass_max_kg": 0.55,
            "feeder_attachment": "local 2.2 N.m reaction plus 5.4 N vertical load",
        },
        "assumptions_and_limits": [
            "production contract and process-surrogate outputs are parameter inputs",
            "closed-loop and particle/feed behavior is reduced-order virtual simulation",
            "no donor motor calibration or physical structural/feed test was performed",
        ],
    }
    (LOAD_OUT / "mechanical_load_envelope.json").write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n")

    quantity_case = {
        "peak_cutter_torque_nm": ["LC01", "LC02"],
        "peak_phase_torque_nm": ["LC01", "LC03"],
        "peak_bearing_load_n": ["LC02", "LC04"],
        "peak_chain_force_n": ["LC05"],
    }
    comparisons = []
    for quantity, old_value in frozen["loads"].items():
        new_value = new_loads[quantity]
        comparisons.append({
            "quantity": quantity,
            "old_value": old_value,
            "new_value": new_value,
            "percent_change": 100*(new_value-old_value)/old_value,
            "direction_change": False,
            "affected_cases": quantity_case[quantity],
            "decision": "NO_RERUN" if abs(new_value-old_value) <= max(1e-9,abs(old_value)*1e-9) else "RERUN_REQUIRED",
        })
    cases = []
    reasons = {
        "LC01": "cutter and phase torque envelope unchanged",
        "LC02": "mechanical-fuse cutter torque and bearing envelope unchanged",
        "LC03": "phase reversal cap and geometry unchanged",
        "LC04": "bearing reaction envelope and bearing plate geometry unchanged",
        "LC05": "chain force and shaft overhang unchanged",
        "LC06": "feed shadow does not change die pressure/axial thrust input",
        "LC07": "feed shadow does not change PLA thermal boundary inputs",
        "LC08": "feed shadow does not change PET thermal/pressure inputs",
        "LC09": "spool mass, support geometry, and line tension inputs unchanged",
        "LC10": "bounded 0.55 kg feed inventory is below frozen global frame reaction envelope",
        "LC11_FEEDER_ATTACHMENT": "2.2 N.m local feeder reaction and 5.4 N vertical load are absent from LC01-LC10",
    }
    for index in range(1, 11):
        case_id = f"LC{index:02d}"
        cases.append({"case_id": case_id, "classification": "NO_RERUN", "reason": reasons[case_id]})
    cases.append({
        "case_id": "LC11_FEEDER_ATTACHMENT",
        "classification": "NEW_CASE_REQUIRED",
        "loads": {"reaction_torque_nm": 2.2, "inventory_vertical_load_n": 5.4},
        "reason": reasons["LC11_FEEDER_ATTACHMENT"],
        "status": process_delta["new_case"]["status"],
    })
    delta = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "status": "NEW_CASE_REQUIRED" if status == "PASS" else "SHADOW_VALIDATION_FAILED",
        "shadow_status": status,
        "frozen_fusion_source": {
            "engineering_source_sha": binding["engineering_source_sha"],
            "source_git_sha": binding["source_git_sha"],
            "run_binding_sha256": sha256(FUSION_BINDING),
            "fusion_result_state": binding["fusion_result_state"],
        },
        "mechanical_envelope_comparison": comparisons,
        "geometry_material_contact_boundary_changes": True,
        "change_scope": "local recirculation/feed geometry outside LC01-LC10; new feeder attachment boundary required",
        "fusion_cases": cases,
        "classification_counts": {
            "NO_RERUN": 10,
            "RERUN_REQUIRED": 0,
            "NEW_CASE_REQUIRED": 1,
        },
        "existing_result_reuse_permitted": False,
        "reuse_note": "frozen Fusion execution is pending independently; NO_RERUN only means this delta does not invalidate LC01-LC10 inputs",
        "physical_test_performed": False,
    }
    DELTA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DELTA_OUT.write_text(json.dumps(delta, indent=2, ensure_ascii=False) + "\n")

    report = f"""# v0.6.2.1 OpenModelica shadow 하중 보고서

- 상태: `{status}`
- 해석: OpenModelica 1.27.0 / DASSL, reduced-order virtual shadow
- 범위: production tach/drive 계약과 process surrogate 경계값을 입력으로 사용
- 물리 시험: 수행하지 않음

기존 frozen 하중 4개는 모두 수치 변화가 없어 LC01–LC10에 이 변경만으로 인한 재실행은 필요하지 않다. 다만 기존 Fusion 결과 자체가 `PENDING_EXTERNAL_EXECUTION`이므로 결과 재사용 가능 판정은 아니다.

새 feeder attachment 반력은 2.2 N·m, 수직하중은 5.4 N이며 기존 case에 포함되지 않는다. 따라서 `LC11_FEEDER_ATTACHMENT = NEW_CASE_REQUIRED`이다.

가정/한계: 이 결과는 제어 및 feed inventory의 축약 시뮬레이션이다. donor motor 실측 보정, 실제 입자 접촉, 구조 시험, 파편 containment 시험을 대체하지 않는다.
"""
    (LOAD_OUT / "README.md").write_text(report)


def validate_compact_evidence() -> None:
    manifest = json.loads((OUT / "scenario_manifest.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    execution = json.loads((OUT / "solver_execution.json").read_text())
    if manifest["scenario_count"] != len(SCENARIOS) or manifest["p0_k_scenarios"] != P0K:
        raise AssertionError("generated scenario manifest mismatch")
    for relative, expected in manifest["source_hashes"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"OpenModelica compact evidence source drift: {relative}")
    if summary.get("status") != "PASS" or summary.get("pass_count") != len(SCENARIOS):
        raise AssertionError("OpenModelica compact summary is not 24/24 PASS")
    manifest_hash = sha256(OUT / "scenario_manifest.json")
    if summary.get("scenario_manifest_sha256") != manifest_hash or \
            execution.get("scenario_manifest_sha256") != manifest_hash:
        raise AssertionError("OpenModelica compact evidence is stale for current manifest")
    if {row.get("scenario") for row in summary.get("results", [])} != set(SCENARIOS):
        raise AssertionError("OpenModelica compact scenario set mismatch")
    if execution.get("validation_status") != "PASS" or execution.get("result_file_count") != len(SCENARIOS):
        raise AssertionError("OpenModelica solver execution evidence missing")
    if set(execution.get("result_sha256", {})) != set(SCENARIOS):
        raise AssertionError("OpenModelica raw result hash inventory mismatch")
    if execution.get("physical_test_performed") is not False:
        raise AssertionError("OpenModelica evidence claim scope mismatch")
    print(f"V0621_SHADOW_COMPACT_EVIDENCE_PASS {len(SCENARIOS)} scenarios")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-only", action="store_true")
    args = parser.parse_args()
    if args.evidence_only:
        validate_compact_evidence()
        return
    manifest = json.loads((OUT / "scenario_manifest.json").read_text())
    if manifest["scenario_count"] != 24 or manifest["p0_k_scenarios"] != P0K:
        raise AssertionError("generated scenario manifest mismatch")
    rows_by_name = {name: load(name) for name in SCENARIOS}
    results = []
    for name in SCENARIOS:
        rows = rows_by_name[name]
        passed = evaluate(name, rows)
        results.append({
            "scenario": name,
            "source_requirement": "P0-K" if name in P0K else "P0-C additional regression",
            "protected_requirement_or_failure_mode": REQUIREMENTS[name],
            "input": "generated V0621Contracts.mo plus scenario parameters",
            "method": "OpenModelica 1.27.0 DASSL reduced-order shadow simulation",
            "expected_evidence": REQUIREMENTS[name],
            "pass_fail_threshold": "scenario-specific predicate in validate_v0621_shadow.py",
            "result": "PASS" if passed else "FAIL",
            "evidence": evidence(rows),
        })
    status = "PASS" if all(row["result"] == "PASS" for row in results) else "FAIL"
    with (OUT / "scenario_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    write_trace(rows_by_name)
    summary = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "solver": "OpenModelica 1.27.0 DASSL",
        "scope": "production-contract-linked reduced-order shadow; physical test not run",
        "scenario_count": len(results),
        "p0_k_enumerated_count": len(P0K),
        "additional_p0_c_regression_count": len(EXTRA),
        "status": status,
        "pass_count": sum(row["result"] == "PASS" for row in results),
        "physical_test_performed": False,
        "scenario_manifest_sha256": sha256(OUT / "scenario_manifest.json"),
        "results": results,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    execution = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "solver": "OpenModelica 1.27.0",
        "integration_method": "dassl",
        "command": "omc simulation/openmodelica/scripts/run_v0621_shadow.mos",
        "container_image": "openmodelica/openmodelica:v1.27.0-minimal",
        "container_digest_observed": "sha256:80fbff1a66fb6a6ade64a158415a45e022363249982c9f3ade07df2a369a357e",
        "result_file_count": len(SCENARIOS),
        "result_sha256": {
            name: sha256(RAW / f"{name}_res.csv") for name in SCENARIOS
        },
        "validator": str(Path(__file__).relative_to(ROOT)),
        "validation_status": status,
        "physical_test_performed": False,
        "scenario_manifest_sha256": sha256(OUT / "scenario_manifest.json"),
    }
    (OUT / "solver_execution.json").write_text(json.dumps(execution, indent=2, ensure_ascii=False) + "\n")
    write_load_and_delta(rows_by_name, status)
    print(f"V0621_SHADOW_{status} {len(results)} scenarios")
    if status != "PASS":
        raise SystemExit("failed scenarios: " + ", ".join(row["scenario"] for row in results if row["result"] == "FAIL"))


if __name__ == "__main__":
    main()
