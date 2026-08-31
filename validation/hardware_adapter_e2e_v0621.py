#!/usr/bin/env python3
"""Compile and verify the v0.6.2.1 production hardware-adapter E2E host harness."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "firmware" / "arduino_mega"
RESULT_DIR = ROOT / "validation" / "results" / "hardware_adapter_e2e"
TRACE = RESULT_DIR / "scenario_trace.csv"
SUMMARY = RESULT_DIR / "summary.json"

SOURCES = [
    "src/machine_supervisor.cpp",
    "src/process_state.cpp",
    "src/shredder_control.cpp",
    "src/drive_speed_control.cpp",
    "src/heater_control.cpp",
    "src/heater_power_allocator.cpp",
    "src/gauge_control.cpp",
    "src/puller_speed_control.cpp",
    "src/screw_motion_monitor.cpp",
    "src/cooling_monitor.cpp",
    "src/spooler_control.cpp",
    "src/traverse_control.cpp",
    "src/traverse_homing.cpp",
    "src/tach_estimator.cpp",
    "tests/test_hardware_adapter_e2e.cpp",
]

REQUIRED_SCENARIOS = {
    "cold_boot_no_cal",
    "partial_calibration",
    "complete_calibration",
    "shredder_start",
    "shredder_nominal",
    "shredder_jam",
    "shredder_reverse",
    "screw_nominal",
    "screw_load",
    "screw_tach_loss",
    "purge_actual_pulse_revolutions",
    "puller_nominal",
    "puller_deadzone",
    "puller_saturation",
    "puller_slip",
    "spool_empty",
    "spool_half",
    "spool_full",
    "spool_jam",
    "traverse_homing",
    "traverse_endpoint_loss",
    "fan1_loss",
    "fan2_loss",
    "dual_fan_loss",
    "gauge_loss",
    "gauge_requalification",
    "forming_rundown",
    "estop_shredding",
    "estop_preheating",
    "estop_requalifying",
    "estop_extrusion",
    "estop_maintenance_purge",
    "estop_forming_rundown",
    "estop_thermal_hold",
    "estop_cooldown",
    "atomic_fault_clear",
    "uint32_rollover",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ppr-v0621-e2e-") as tmp:
        binary = Path(tmp) / "test_hardware_adapter_e2e"
        compile_command = [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Isrc",
            *SOURCES,
            "-o",
            str(binary),
        ]
        compile_run = subprocess.run(
            compile_command,
            cwd=FW,
            text=True,
            capture_output=True,
            check=False,
        )
        if compile_run.returncode != 0:
            raise SystemExit(f"compile failed\n{compile_run.stdout}\n{compile_run.stderr}")
        harness_run = subprocess.run(
            [str(binary), str(TRACE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if harness_run.returncode != 0:
            raise SystemExit(f"harness failed\n{harness_run.stdout}\n{harness_run.stderr}")

    with TRACE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    names = [row["scenario"] for row in rows]
    observed = set(names)
    missing = sorted(REQUIRED_SCENARIOS - observed)
    unexpected = sorted(observed - REQUIRED_SCENARIOS)
    duplicates = sorted(name for name in observed if names.count(name) != 1)
    failed = [row for row in rows if row["status"] != "PASS"]
    if missing or unexpected or duplicates or failed or len(rows) != len(REQUIRED_SCENARIOS):
        raise SystemExit(
            f"scenario manifest mismatch missing={missing} unexpected={unexpected} "
            f"duplicates={duplicates} failed={len(failed)} rows={len(rows)}"
        )
    if "HARDWARE_ADAPTER_E2E_V0621_OK scenarios=37" not in harness_run.stdout:
        raise SystemExit(f"success marker missing: {harness_run.stdout!r}")

    source_hashes = {relative: sha256(FW / relative) for relative in SOURCES}
    summary = {
        "schema": "ppr.hardware_adapter_e2e.v0.6.2.1",
        "status": "HOST_SIMULATION_PASS",
        "physical_test_status": "NOT_RUN",
        "evidence_class": "host simulation with production C++ classes",
        "scenario_count": len(rows),
        "required_scenario_count": len(REQUIRED_SCENARIOS),
        "all_scenarios_unique": True,
        "all_scenarios_passed": True,
        "adapter_boundary": {
            "tach": "timestamp pulse trains through TachEstimator; no post-adapter ideal RPM injection",
            "current": "integer ADC counts converted to calibrated amperes",
            "actuation": "quantized integer PWM with calibrated dead zones and saturation",
            "time": "uint32_t modular rollover exercised",
        },
        "production_paths": [
            "MachineSupervisor",
            "CalibrationRecord v4 CRC/readiness",
            "TachEstimator",
            "ShredderController",
            "ScrewMotionMonitor",
            "PullerSpeedController",
            "SpoolerController",
            "CoolingMonitor",
            "GaugeController",
            "TraverseHomingController",
            "TraverseController",
            "ProcessController",
        ],
        "scenarios": names,
        "trace": str(TRACE.relative_to(ROOT)),
        "trace_sha256": sha256(TRACE),
        "source_sha256": source_hashes,
        "compile_command": " ".join(compile_command[:-1] + ["<temporary-binary>"]),
        "harness_stdout": harness_run.stdout.strip(),
        "limitations": [
            "This is a deterministic host-side hardware-adapter simulation, not a physical machine test.",
            "Motor, thermal, and material plants are intentionally bounded surrogates; controller and supervisor code are production sources.",
            "No cutter, heater, mains, or high-current hardware was energized.",
        ],
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"HARDWARE_ADAPTER_E2E_V0621_PASS scenarios={len(rows)}")
    print(f"trace={TRACE.relative_to(ROOT)}")
    print(f"summary={SUMMARY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
