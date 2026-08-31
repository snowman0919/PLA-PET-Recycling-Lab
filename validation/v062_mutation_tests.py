#!/usr/bin/env python3
"""핵심 v0.6.2 회귀가 production source mutation을 실제로 거부하는지 증명한다."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def checks(sources: dict[str, str]) -> dict[str, bool]:
    puller = sources["puller"]
    cooling = sources["cooling"]
    supervisor = sources["supervisor"]
    heater = sources["heater"]
    importer = sources["importer"]
    return {
        "puller_saturation_not_hardcoded_false":
            "out.saturated = speed.saturated" in puller,
        "both_fan_feedback_channels_required":
            "!fan1_running" in cooling and "!fan2_running" in cooling,
        "purge_uses_measured_revolutions":
            "screw_motion_output_.cumulative_revolutions - purge_start_screw_revolutions_" in supervisor and
            "purge_screw_revolutions_measured_" in supervisor,
        "heater_applied_duty_feedback_present":
            "z.applied_duty - z.requested_duty" in heater,
        "spooler_is_not_fixed_pwm":
            "spooler_control_.update" in supervisor and "c.spooler_pwm = 96" not in supervisor,
        "traverse_is_not_time_reversed":
            "traverse_control_.update(spooler_output_.cumulative_turns" in supervisor and
            "now_ms / 4000UL" not in supervisor,
        "fusion_hash_binding_required": all(token in importer for token in (
            'row["source_git_sha"] != binding["engineering_source_sha"]',
            'row["step_sha256"] != model["step_sha256"]',
            'row["load_case_manifest_sha256"] != binding["load_case_manifest_sha256"]',
        )),
    }


def main() -> None:
    sources = {
        "puller": read("firmware/arduino_mega/src/puller_speed_control.cpp"),
        "cooling": read("firmware/arduino_mega/src/cooling_monitor.cpp"),
        "supervisor": read("firmware/arduino_mega/src/machine_supervisor.cpp"),
        "heater": read("firmware/arduino_mega/src/heater_control.cpp"),
        "importer": read("analysis/cross_solver/import_fusion_results.py"),
    }
    baseline = checks(sources)
    if not all(baseline.values()):
        raise AssertionError("baseline validator failed: " + str(baseline))
    mutations = {
        "puller_saturation_hardcoded_false": ("puller", "out.saturated = speed.saturated", "out.saturated = false"),
        "fan2_channel_ignored": ("cooling", "if (commanded && !fan2_running) bits |= COOLING_FAN2_STOPPED;", ""),
        "purge_commanded_revolutions": ("supervisor", "screw_motion_output_.cumulative_revolutions - purge_start_screw_revolutions_", "input.screw_rpm"),
        "heater_feedback_removed": ("heater", "z.applied_duty - z.requested_duty", "0.0f"),
        "spooler_fixed_pwm": ("supervisor", "c.spooler_pwm = spooler_output_.pwm;", "c.spooler_pwm = 96;"),
        "traverse_time_reversal": ("supervisor", "c.traverse_direction = traverse_output_.direction;", "c.traverse_direction = ((now_ms / 4000UL) & 1U) != 0;"),
        "fusion_binding_removed": ("importer", 'row["step_sha256"] != model["step_sha256"]', "False"),
    }
    results = []
    for name, (key, old, new) in mutations.items():
        if old not in sources[key]:
            raise AssertionError(f"mutation target missing: {name}")
        changed = dict(sources)
        changed[key] = changed[key].replace(old, new, 1)
        rejected = not all(checks(changed).values())
        results.append({"mutation": name, "expected": "validator rejection", "result": "PASS" if rejected else "FAIL"})
    payload = {
        "revision": "parallel-actuation-hardening-v0.6.2",
        "mutation_count": len(results), "status": "PASS" if all(r["result"] == "PASS" for r in results) else "FAIL",
        "mutations": results,
    }
    path = ROOT / "validation/results/v062_mutation_tests.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"V062_MUTATION_TESTS_{payload['status']} count={len(results)}")
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
