#!/usr/bin/env python3
"""v0.6.2.1 technical blocker mutation gate.

Mutations are applied only to temporary copies or in-memory inputs.  A mutation
passes this suite only when the production-linked test/validator rejects it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "firmware" / "arduino_mega"
RESULT = ROOT / "validation" / "results" / "v0621_mutation_tests.json"
CXX = ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror"]

TACH_SOURCES = ["src/tach_estimator.cpp", "tests/test_tach_estimator.cpp"]
DRIVE_SOURCES = [
    "src/tach_estimator.cpp",
    "src/shredder_control.cpp",
    "src/screw_motion_monitor.cpp",
    "src/puller_speed_control.cpp",
    "src/spooler_control.cpp",
    "tests/test_hardware_adapter.cpp",
]
TRAVERSE_SOURCES = [
    "src/traverse_control.cpp",
    "src/traverse_homing.cpp",
    "tests/test_traverse_homing.cpp",
]
CALIBRATION_SOURCES = ["tests/test_calibration_record.cpp"]
E2E_SOURCES = [
    "src/machine_supervisor.cpp", "src/process_state.cpp", "src/shredder_control.cpp",
    "src/drive_speed_control.cpp", "src/heater_control.cpp", "src/heater_power_allocator.cpp",
    "src/gauge_control.cpp", "src/puller_speed_control.cpp", "src/screw_motion_monitor.cpp",
    "src/cooling_monitor.cpp", "src/spooler_control.cpp", "src/traverse_control.cpp",
    "src/traverse_homing.cpp", "src/tach_estimator.cpp", "tests/test_hardware_adapter_e2e.cpp",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tail(text: str, limit: int = 500) -> str:
    clean = " ".join(text.strip().split())
    clean = re.sub(r"/tmp/ppr-[^/ ]+/arduino_mega/", "TEMP/arduino_mega/", clean)
    return clean[-limit:]


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise AssertionError(f"expected one mutation anchor in {path.name}, found {count}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def replace_all(path: Path, old: str, new: str, expected: int) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != expected:
        raise AssertionError(
            f"expected {expected} mutation anchors in {path.name}, found {count}"
        )
    path.write_text(content.replace(old, new), encoding="utf-8")


def compile_and_run(tree: Path, sources: list[str], binary_name: str) -> dict:
    binary = tree / binary_name
    command = CXX + [f"-I{tree / 'src'}"] + [str(tree / item) for item in sources]
    command += ["-o", str(binary)]
    compiled = subprocess.run(command, cwd=tree, text=True, capture_output=True)
    if compiled.returncode != 0:
        return {
            "compile_returncode": compiled.returncode,
            "run_returncode": None,
            "diagnostic": tail(compiled.stdout + compiled.stderr),
        }
    ran = subprocess.run([str(binary)], cwd=tree, text=True, capture_output=True)
    return {
        "compile_returncode": 0,
        "run_returncode": ran.returncode,
        "diagnostic": tail(ran.stdout + ran.stderr),
    }


def firmware_tree(parent: Path) -> Path:
    tree = parent / "arduino_mega"
    shutil.copytree(FW / "src", tree / "src")
    shutil.copytree(FW / "tests", tree / "tests")
    return tree


def cpp_mutation(
    mutation_id: str,
    description: str,
    sources: list[str],
    edits: Callable[[Path], None],
    test_file: str,
) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"ppr-{mutation_id}-") as temporary:
        tree = firmware_tree(Path(temporary))
        edits(tree)
        execution = compile_and_run(tree, sources, mutation_id)
    rejected = execution["compile_returncode"] == 0 and execution["run_returncode"] != 0
    return {
        "mutation_id": mutation_id,
        "description": description,
        "method": "temporary production source mutation; compile and execute existing host test",
        "production_test": test_file,
        "expected": "runtime rejection",
        "observed": "REJECTED" if rejected else "ACCEPTED_OR_INVALID_MUTATION",
        "status": "PASS" if rejected else "FAIL",
        **execution,
    }


def baseline_cpp() -> list[dict]:
    suites = [
        ("tach", TACH_SOURCES),
        ("drive", DRIVE_SOURCES),
        ("traverse", TRAVERSE_SOURCES),
        ("calibration", CALIBRATION_SOURCES),
        ("adapter_e2e", E2E_SOURCES),
    ]
    rows = []
    with tempfile.TemporaryDirectory(prefix="ppr-v0621-baseline-") as temporary:
        tree = firmware_tree(Path(temporary))
        write_physical_ppr_probe(tree)
        suites.append(("physical_ppr", ["src/tach_estimator.cpp", "tests/test_wrong_ppr_physical.cpp"]))
        for name, sources in suites:
            execution = compile_and_run(tree, sources, f"baseline_{name}")
            passed = execution["compile_returncode"] == 0 and execution["run_returncode"] == 0
            rows.append({"suite": name, "status": "PASS" if passed else "FAIL", **execution})
    return rows


def edit_fixed_window(tree: Path) -> None:
    path = tree / "src" / "tach_estimator.cpp"
    replace_once(
        path,
        "  if (period_us == 0 || config_.pulses_per_revolution == 0) return 0.0f;\n",
        "  if (period_us == 0 || config_.pulses_per_revolution == 0) return 0.0f;\n"
        "  // MUTATION: a 20 ms fixed window reports zero whenever no edge lands in it.\n"
        "  if (period_us > 20000U) return 0.0f;\n",
    )


def write_physical_ppr_probe(tree: Path) -> None:
    probe = tree / "tests" / "test_wrong_ppr_physical.cpp"
    probe.write_text(
        """#include <assert.h>
#include <math.h>
#include <stdint.h>
#include "tach_contract_generated.h"
#include "tach_estimator.h"
int main() {
  TachEstimator e;
  assert(e.configure(SHREDDER_TACH_CONFIG));
  uint32_t t = 1000U;
  e.onPulse(t);
  const uint32_t physical_six_pole_interval_us = 312500U;
  TachEstimate x{};
  for (int i = 0; i < 18; ++i) {
    t += physical_six_pole_interval_us;
    e.onPulse(t);
    x = e.estimate(t);
  }
  assert(x.valid);
  assert(fabsf(x.rpm - 32.0f) / 32.0f <= 0.03f);
  return 0;
}
""",
        encoding="utf-8",
    )


def edit_wrong_ppr(tree: Path) -> None:
    path = tree / "src" / "tach_contract_generated.h"
    replace_once(path, "constexpr TachEstimatorConfig SHREDDER_TACH_CONFIG{\n    6,", "constexpr TachEstimatorConfig SHREDDER_TACH_CONFIG{\n    7,")
    write_physical_ppr_probe(tree)


def edit_rollover_removed(tree: Path) -> None:
    replace_once(
        tree / "src" / "tach_estimator.cpp",
        "  const uint32_t pulse_period_us = timestamp_us - last_pulse_us_;",
        "  const uint32_t pulse_period_us = timestamp_us >= last_pulse_us_\n"
        "      ? timestamp_us - last_pulse_us_ : 0U;  // MUTATION: no modular rollover",
    )


def edit_open_loop_screw(tree: Path) -> None:
    replace_once(
        tree / "src" / "screw_motion_monitor.cpp",
        "          speed.target_rpm, speed.pwm, speed.saturated, speed.tach_loss};",
        "          speed.target_rpm, static_cast<int16_t>(commanded_rpm * 10.0f),\n"
        "          speed.saturated, false};  // MUTATION: direct RPM-to-PWM map",
    )


def edit_open_loop_shredder(tree: Path) -> None:
    path = tree / "src" / "shredder_control.cpp"
    replace_once(
        path,
        "  out.pwm = speed.pwm;",
        "  out.pwm = static_cast<int16_t>(signed_target * 6.0f);  // MUTATION: open loop",
    )
    replace_once(path, "  if (enabled && speed.tach_loss) {", "  if (false && enabled && speed.tach_loss) {")


def edit_radius_quarter_removed(tree: Path) -> None:
    replace_all(
        tree / "src" / "spooler_control.cpp",
        "4.0f * config_.packing_factor * config_.spool_width_mm",
        "config_.packing_factor * config_.spool_width_mm",
        2,
    )


def edit_radius_packing_removed(tree: Path) -> None:
    replace_all(
        tree / "src" / "spooler_control.cpp",
        "4.0f * config_.packing_factor * config_.spool_width_mm",
        "4.0f * config_.spool_width_mm",
        2,
    )


def edit_traverse_calibration_ignored(tree: Path) -> None:
    replace_once(
        tree / "src" / "traverse_control.cpp",
        "  if (configured_) config_ = c;",
        "  if (configured_) { config_ = c; config_.steps_per_mm = 10.0f; } // MUTATION",
    )


def edit_traverse_starts_homed(tree: Path) -> None:
    replace_once(
        tree / "src" / "traverse_homing.cpp",
        "  state_ = TraverseHomingState::TRAVERSE_UNHOMED;",
        "  state_ = TraverseHomingState::TRAVERSE_READY;  // MUTATION: bypass homing",
    )


def edit_shared_calibration(tree: Path) -> None:
    path = tree / "src" / "calibration_record.h"
    old = """inline bool calibrationDomainReady(const CalibrationRecord &record, CalibrationId id) {
  return id < CAL_COUNT && calibrationValueRecordValid(record.records[id], id) &&
         record.records[id].verified != 0;
}"""
    new = """inline bool calibrationDomainReady(const CalibrationRecord &record, CalibrationId id) {
  // MUTATION: one puller-drive flag incorrectly approves unrelated motion domains.
  if (id == CAL_SCREW_TACH || id == CAL_SPOOLER_TACH || id == CAL_TRAVERSE)
    id = CAL_PULLER_DRIVE;
  return id < CAL_COUNT && calibrationValueRecordValid(record.records[id], id) &&
         record.records[id].verified != 0;
}"""
    replace_once(path, old, new)


def edit_adapter_bypass(tree: Path) -> None:
    replace_once(
        tree / "tests" / "test_hardware_adapter_e2e.cpp",
        "  TachEstimate sample(uint64_t absolute_now_us, float physical_rpm, bool connected = true) {\n",
        "  TachEstimate sample(uint64_t absolute_now_us, float physical_rpm, bool connected = true) {\n"
        "    (void)absolute_now_us;\n"
        "    // MUTATION: ideal RPM is injected after the hardware-adapter boundary.\n"
        "    return {physical_rpm, connected && physical_rpm > 0.0f, "
        "TachEstimateMode::PERIOD, 0U, 1U, 0U, 0U};\n",
    )


def feasibility_gate(contract: dict) -> tuple[bool, list[str]]:
    failures = []
    for name in ("puller", "spooler"):
        drive = contract["drives"][name]
        normal_min, normal_max = drive.get(
            "normal_target_rpm", drive.get("normal_target_rpm_empty_to_full", [])
        )
        minimum, maximum = drive["required_controllable_rpm"]
        if minimum > 0.7 * normal_min:
            failures.append(f"{name}: minimum stable RPM exceeds 0.7 x minimum demand")
        if maximum < 1.5 * normal_max:
            failures.append(f"{name}: maximum RPM below 1.5 x maximum demand")
        fractions = (normal_min / maximum, normal_max / maximum)
        if min(fractions) < 0.10 or max(fractions) > 0.85:
            failures.append(f"{name}: normal target outside 10-85 percent controllable range")
    return not failures, failures


def feasibility_mutation(name: str, minimum_rpm: float) -> dict:
    contract = json.loads((ROOT / "control" / "drive_actuation_contract_v0.6.2.1.json").read_text())
    baseline_ok, baseline_errors = feasibility_gate(contract)
    mutated = json.loads(json.dumps(contract))
    mutated["drives"][name]["required_controllable_rpm"][0] = minimum_rpm
    mutation_ok, mutation_errors = feasibility_gate(mutated)
    rejected = baseline_ok and not mutation_ok
    return {
        "mutation_id": f"{name}_minimum_pwm_infeasible",
        "description": f"{name} minimum stable operating point raised above normal-demand feasibility",
        "method": "in-memory contract mutation and equation-based actuator acceptance gate",
        "expected": "gate rejection",
        "observed": "REJECTED" if rejected else "ACCEPTED",
        "status": "PASS" if rejected else "FAIL",
        "baseline_errors": baseline_errors,
        "mutation_errors": mutation_errors,
        "mutated_minimum_stable_rpm": minimum_rpm,
    }


def run_python_source_mutation(
    mutation_id: str,
    description: str,
    source: Path,
    old: str,
    new: str,
    supporting: list[tuple[Path, Path]],
) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"ppr-{mutation_id}-") as temporary:
        temp = Path(temporary)
        target = temp / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        for original, relative in supporting:
            copied = temp / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, copied)
        replace_once(target, old, new)
        ran = subprocess.run(["python3", str(target)], cwd=temp, text=True, capture_output=True)
    rejected = ran.returncode != 0
    return {
        "mutation_id": mutation_id,
        "description": description,
        "method": "temporary production model source mutation and full model execution",
        "expected": "model acceptance rejection",
        "observed": "REJECTED" if rejected else "ACCEPTED",
        "status": "PASS" if rejected else "FAIL",
        "run_returncode": ran.returncode,
        "diagnostic": tail(ran.stdout + ran.stderr),
    }


def feed_gravity_only() -> dict:
    source = ROOT / "analysis" / "process_feed" / "run_feed_surrogate.py"
    old = "        delivered = 0.0 if bridge_active else min(109.5, 60.0 * rpm * basis[\"mass_per_rev_g\"] * (1.0 - 0.18 * basis[\"bridge_index\"]))"
    new = (
        "        # MUTATION: PET bypasses the metering auger and depends on gravity alone.\n"
        "        gravity_pet = 45.0 * (1.0 - basis[\"bridge_index\"])\n"
        "        delivered = 0.0 if bridge_active else (gravity_pet if material[\"polymer\"] == \"PET\" "
        "else min(109.5, 60.0 * rpm * basis[\"mass_per_rev_g\"] * (1.0 - 0.18 * basis[\"bridge_index\"])))"
    )
    return run_python_source_mutation(
        "gravity_only_pet_feed", "PET positive-displacement feed replaced by gravity-only delivery",
        source, old, new,
        [(ROOT / "analysis/process_feed/feed_parameters.json", Path("analysis/process_feed/feed_parameters.json"))],
    )


def recirculation_removed() -> dict:
    source = ROOT / "analysis" / "shredder_recirculation" / "run_recirculation_surrogate.py"
    old = "    return_probability = clamp(0.985 - 0.022 * friction_n - 0.018 * fill_n - 0.010 * aspect_n, 0.0, 1.0)"
    new = "    return_probability = 0.0  # MUTATION: recirculation path removed"
    return run_python_source_mutation(
        "recirculation_path_removed", "oversize return path removed from shredder transport model",
        source, old, new,
        [
            (ROOT / "analysis/shredder_recirculation/recirculation_parameters.json", Path("analysis/shredder_recirculation/recirculation_parameters.json")),
            (ROOT / "analysis/process_feed/feed_parameters.json", Path("analysis/process_feed/feed_parameters.json")),
        ],
    )


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fusion_row(importer, evidence: Path) -> dict[str, str]:
    binding, models, _ = importer.load_contract()
    model = models["bearing_plate.step"]
    return {
        "run_id": "mutation", "case_id": "LC04", "study_type": "static_stress",
        "source_git_sha": binding["engineering_source_sha"], "step_file": "bearing_plate.step",
        "step_sha256": model["step_sha256"],
        "load_case_manifest_sha256": binding["load_case_manifest_sha256"],
        "mesh_level": "fine", "element_count": "1000", "metric": "global displacement",
        "value": "0.35", "unit": "mm", "solver_version": "mutation-fixture",
        "completed_utc": "2026-08-31T00:00:00Z", "evidence_file": str(evidence),
        "evidence_sha256": digest(evidence), "operator": "red-team", "status": "COMPLETE",
    }


def fusion_mutations() -> list[dict]:
    importer = load_module(
        "v0621_fusion_importer", ROOT / "analysis" / "cross_solver" / "import_fusion_results.py"
    )
    rows = []
    with tempfile.TemporaryDirectory(prefix="ppr-fusion-mutations-") as temporary:
        evidence = Path(temporary) / "evidence.txt"
        evidence.write_text("external solver mutation fixture", encoding="utf-8")
        valid = fusion_row(importer, evidence)
        baseline = importer.validate_rows([valid])
        for mutation_id, key, value in (
            ("stale_fusion_hash", "step_sha256", "0" * 64),
            ("fusion_unit_mismatch", "unit", "inch"),
        ):
            mutated = dict(valid)
            mutated[key] = value
            result = importer.validate_rows([mutated])
            rejected = baseline["state"] == "CORRELATION_REVIEW" and result["state"] == "INVALID_BINDING"
            rows.append({
                "mutation_id": mutation_id,
                "description": f"Fusion row mutation: {key}={value}",
                "method": "production Fusion import validator with in-memory mutated result row",
                "expected": "INVALID_BINDING",
                "observed": result["state"],
                "status": "PASS" if rejected else "FAIL",
                "errors": result["errors"],
            })
    return rows


def budget_mutation() -> dict:
    source = ROOT / "bom" / "build_budget_views.py"
    with tempfile.TemporaryDirectory(prefix="ppr-budget-mutation-") as temporary:
        target = Path(temporary) / source.name
        shutil.copy2(source, target)
        replace_once(
            target,
            '        "technical_release_blocked": False,',
            '        "technical_release_blocked": absolute_total_krw > 200000,  # MUTATION',
        )
        module = load_module("v0621_budget_mutated", target)
        policy = module.price_policy(200001)
    accepted = (
        policy["price_status"] == "INFORMATIONAL"
        and policy["price_release_blocking"] is False
        and policy["technical_release_blocked"] is False
        and policy["procurement_approval_gate"] == "USER_APPROVAL_REQUIRED"
    )
    return {
        "mutation_id": "budget_above_200k_technical_failure",
        "description": "200,001 KRW budget incorrectly blocks technical release",
        "method": "temporary production price_policy source mutation and policy gate evaluation",
        "expected": "policy gate rejection",
        "observed": "REJECTED" if not accepted else "ACCEPTED",
        "status": "PASS" if not accepted else "FAIL",
        "mutated_policy": policy,
    }


def main() -> int:
    baselines = baseline_cpp()
    mutations = [
        cpp_mutation("fixed_window_20ms_tach", "fixed 20 ms low-speed pulse window reintroduced",
                     TACH_SOURCES, edit_fixed_window, "test_tach_estimator.cpp"),
        cpp_mutation("wrong_ppr", "shredder PPR changed from physical six-pole target to seven",
                     ["src/tach_estimator.cpp", "tests/test_wrong_ppr_physical.cpp"],
                     edit_wrong_ppr, "generated physical-target probe"),
        cpp_mutation("micros_rollover_removed", "uint32 micros modular subtraction removed",
                     TACH_SOURCES, edit_rollover_removed, "test_tach_estimator.cpp"),
        feasibility_mutation("puller", 4.0),
        feasibility_mutation("spooler", 1.0),
        cpp_mutation("open_loop_screw_pwm", "screw speed PI replaced by direct RPM-to-PWM map",
                     DRIVE_SOURCES, edit_open_loop_screw, "test_hardware_adapter.cpp"),
        cpp_mutation("open_loop_shredder_pwm", "shredder PI/tach-loss path bypassed by direct PWM",
                     DRIVE_SOURCES, edit_open_loop_shredder, "test_hardware_adapter.cpp"),
        cpp_mutation("spool_radius_factor_four_removed", "volume-conservation 1/4 factor removed",
                     DRIVE_SOURCES, edit_radius_quarter_removed, "test_hardware_adapter.cpp"),
        cpp_mutation("spool_radius_packing_removed", "packing factor removed from radius estimate",
                     DRIVE_SOURCES, edit_radius_packing_removed, "test_hardware_adapter.cpp"),
        cpp_mutation("traverse_calibration_ignored", "stored steps/mm replaced by fixed value",
                     TRAVERSE_SOURCES, edit_traverse_calibration_ignored, "test_traverse_homing.cpp"),
        cpp_mutation("traverse_starts_unhomed_bypassed", "traverse starts READY without homing",
                     TRAVERSE_SOURCES, edit_traverse_starts_homed, "test_traverse_homing.cpp"),
        cpp_mutation("shared_calibration_flag", "puller drive record reused for unrelated domains",
                     CALIBRATION_SOURCES, edit_shared_calibration, "test_calibration_record.cpp"),
        cpp_mutation("hardware_adapter_ideal_rpm_bypass",
                     "timestamp pulse boundary replaced by ideal post-adapter RPM injection",
                     E2E_SOURCES, edit_adapter_bypass, "test_hardware_adapter_e2e.cpp"),
        feed_gravity_only(),
        recirculation_removed(),
        *fusion_mutations(),
        budget_mutation(),
    ]
    baseline_pass = all(row["status"] == "PASS" for row in baselines)
    mutations_pass = all(row["status"] == "PASS" for row in mutations)
    payload = {
        "schema_version": 1,
        "revision": "technical-blocker-closure-v0.6.2.1",
        "status": "PASS" if baseline_pass and mutations_pass else "FAIL",
        "semantics": "PASS means the clean baseline passed and every defect mutation was rejected",
        "physical_hardware_test": False,
        "baseline_suites": baselines,
        "mutation_count": len(mutations),
        "rejected_mutation_count": sum(row["status"] == "PASS" for row in mutations),
        "mutations": mutations,
        "limitations": [
            "All C++ tests are host simulations; no energized hardware or physical calibration was used.",
            "Actuator feasibility uses the contract's calibrated-range requirements, not donor motor measurements.",
            "Feed and recirculation mutations exercise deterministic virtual surrogates, not physical particle tests.",
        ],
        "audit_findings_resolved": [
            {
                "severity": "INTEGRATION_RISK",
                "path": "validation/hardware_adapter_v0621.py",
                "finding": "summary acceptance booleans previously used constants",
                "mitigation": "validator now computes acceptance from trace data; mutation runner independently requires runtime rejection",
            },
            {
                "severity": "INTEGRATION_RISK",
                "path": "analysis/process_feed/verify_process_lane.py",
                "finding": "artifact-only verification previously could accept stale generated JSON",
                "mitigation": "process verifier now reruns feed and recirculation models before checking artifacts",
            },
        ],
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"V0621_MUTATION_GATE_{payload['status']} "
        f"rejected={payload['rejected_mutation_count']}/{payload['mutation_count']}"
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
