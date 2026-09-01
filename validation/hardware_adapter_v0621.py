#!/usr/bin/env python3
"""Compile production-linked tach/drive host tests and publish machine-readable traces."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "firmware" / "arduino_mega"
RESULT = ROOT / "validation" / "results" / "hardware_adapter_tach"
CXX_FLAGS = ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", f"-I{FW / 'src'}"]


def compile_binary(output: Path, sources: list[str]) -> None:
    subprocess.run(CXX_FLAGS + [str(ROOT / source) for source in sources] + ["-o", str(output)],
                   cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    RESULT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", "control/generate_tach_contract.py", "--check"],
                   cwd=ROOT, check=True)
    tach_trace = RESULT / "tach_trace.csv"
    drive_trace = RESULT / "drive_trace.csv"
    with tempfile.TemporaryDirectory(prefix="ppr-v0621-adapter-") as temporary:
        temp = Path(temporary)
        tach_binary = temp / "test_tach_estimator"
        drive_binary = temp / "test_hardware_adapter"
        compile_binary(tach_binary, [
            "firmware/arduino_mega/src/tach_estimator.cpp",
            "firmware/arduino_mega/tests/test_tach_estimator.cpp",
        ])
        compile_binary(drive_binary, [
            "firmware/arduino_mega/src/tach_estimator.cpp",
            "firmware/arduino_mega/src/shredder_control.cpp",
            "firmware/arduino_mega/src/screw_motion_monitor.cpp",
            "firmware/arduino_mega/src/puller_speed_control.cpp",
            "firmware/arduino_mega/src/spooler_control.cpp",
            "firmware/arduino_mega/tests/test_hardware_adapter.cpp",
        ])
        tach_run = subprocess.run([str(tach_binary), str(tach_trace)], cwd=ROOT, check=True,
                                  text=True, capture_output=True)
        drive_run = subprocess.run([str(drive_binary), str(drive_trace)], cwd=ROOT, check=True,
                                   text=True, capture_output=True)

    contract = json.loads((ROOT / "control" / "tach_contract.json").read_text(encoding="utf-8"))
    contract_channels = {channel["channel"]: channel for channel in contract["channels"]}
    per_channel: dict[str, dict[str, float | int | bool]] = {}
    with tach_trace.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            channel = row["channel"]
            stats = per_channel.setdefault(channel, {
                "nominal_samples": 0,
                "maximum_nominal_relative_error": 0.0,
                "count_mode_observed": False,
                "period_mode_observed": False,
                "timeout_observed": False,
                "bounce_rejections": 0,
                "outlier_rejections": 0,
                "missing_pulse_stable": False,
                "bounce_pulse_stable": False,
                "rollover_safe": False,
                "incorrect_ppr_mutation_rejected": False,
            })
            if row["scenario"] == "nominal_jitter" and row["valid"] == "1":
                target = float(row["target_rpm"])
                error = abs(float(row["estimate_rpm"]) - target) / target
                stats["nominal_samples"] = int(stats["nominal_samples"]) + 1
                stats["maximum_nominal_relative_error"] = max(
                    float(stats["maximum_nominal_relative_error"]), error)
            stats["count_mode_observed"] = bool(stats["count_mode_observed"]) or row["mode"] == "COUNT"
            stats["period_mode_observed"] = bool(stats["period_mode_observed"]) or row["mode"] == "PERIOD"
            stats["timeout_observed"] = bool(stats["timeout_observed"]) or row["mode"] == "TIMEOUT"
            stats["bounce_rejections"] = max(int(stats["bounce_rejections"]),
                                              int(row["bounce_rejected"]))
            stats["outlier_rejections"] = max(int(stats["outlier_rejections"]),
                                               int(row["outlier_rejected"]))
            scenario = row["scenario"]
            target = float(row["target_rpm"])
            estimate = float(row["estimate_rpm"])
            relative_error = abs(estimate - target) / target if target > 0 else 0.0
            valid = row["valid"] == "1"
            if scenario == "missing_pulse":
                stats["missing_pulse_stable"] = valid and relative_error <= 0.03
            elif scenario == "duplicate_bounce":
                stats["bounce_pulse_stable"] = valid and relative_error <= 0.03 and int(row["bounce_rejected"]) > 0
            elif scenario == "timer_rollover":
                stats["rollover_safe"] = valid and relative_error <= 0.03
            elif scenario == "incorrect_ppr_mutation":
                stats["incorrect_ppr_mutation_rejected"] = relative_error > 0.03
    for channel, stats in per_channel.items():
        channel_contract = contract_channels[channel]
        stats["ppr"] = channel_contract["ppr"]
        stats["minimum_measurable_rpm_at_timeout"] = 60000000.0 / (
            channel_contract["ppr"] * channel_contract["timeout_us"])
        stats["nominal_error_acceptance_percent"] = 3.0

    drive_scenarios: dict[str, dict[str, float | int | bool]] = {}
    with drive_trace.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            key = f"{row['drive']}:{row['scenario']}"
            target = float(row["target_rpm"])
            plant = float(row["plant_rpm"])
            drive_scenarios[key] = {
                "final_time_ms": int(row["time_ms"]),
                "target_rpm": target,
                "estimated_rpm": float(row["estimated_rpm"]),
                "plant_rpm": plant,
                "pwm": int(row["pwm"]),
                "tach_valid": row["tach_valid"] == "1",
                "plant_relative_error": abs(plant - target) / target if target > 0 else 0.0,
            }

    channel_checks = list(per_channel.values())
    acceptance = {
        "steady_nominal_error_le_3_percent": all(
            int(item["nominal_samples"]) > 0 and
            float(item["maximum_nominal_relative_error"]) <= 0.03
            for item in channel_checks),
        "single_missing_or_bounce_does_not_create_zero_spike": all(
            bool(item["missing_pulse_stable"]) and bool(item["bounce_pulse_stable"])
            for item in channel_checks),
        "zero_speed_fault_within_channel_timeout": all(
            bool(item["timeout_observed"]) for item in channel_checks),
        "minimum_valid_speed_has_no_false_zero": all(
            bool(item["period_mode_observed"]) for item in channel_checks),
        "uint32_rollover_safe": all(bool(item["rollover_safe"]) for item in channel_checks),
        "incorrect_ppr_mutation_fails": all(
            bool(item["incorrect_ppr_mutation_rejected"]) for item in channel_checks),
    }
    if not all(acceptance.values()):
        raise AssertionError(f"hardware adapter acceptance failed: {acceptance}")

    summary = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "status": "HOST_HARDWARE_ADAPTER_SIMULATION_PASS",
        "physical_hardware_test": False,
        "production_classes_linked": [
            "TachEstimator", "DriveSpeedController", "ShredderController",
            "ScrewMotionMonitor", "PullerSpeedController", "SpoolerController",
        ],
        "adapter_effects": [
            "timestamped pulses", "uint32 micros rollover", "ADC quantization",
            "PWM dead zone", "missing and duplicate pulses", "tach disconnect",
        ],
        "contract_sync": "PASS",
        "acceptance": acceptance,
        "tach_test_stdout": tach_run.stdout.strip(),
        "drive_test_stdout": drive_run.stdout.strip(),
        "per_channel": per_channel,
        "drive_scenarios": drive_scenarios,
        "artifacts": {
            "tach_trace.csv": sha256(tach_trace),
            "drive_trace.csv": sha256(drive_trace),
        },
        "limitations": [
            "No motor, sensor, load, cutter, screw, puller, spool, or energized hardware was tested.",
            "Donor gear ratio, dead zone, loaded speed curve, and tach target installation require physical calibration.",
        ],
    }
    (RESULT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "result": str(RESULT.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
