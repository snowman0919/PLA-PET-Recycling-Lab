#!/usr/bin/env python3
"""Generate bounded-control timing and power-arbitration evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    loop_ms = 10
    heartbeat_timeout_ms = 750
    jam = {
        "load_to_feed_limit_max_ms": 250 + loop_ms,
        "load_to_forward_stop_max_ms": 250 + 500 + 2 * loop_ms,
        "first_reverse_start_max_ms": 250 + 500 + 300 + 3 * loop_ms,
        "reverse_duration_ms": 800,
        "maximum_retries": 3,
        "persistent_jam_to_latched_fault_max_ms": 7362 + loop_ms,
    }
    cases = {
        "extrude_worst_case": {
            "software_limit_w": 480.0,
            "non_heater_reserve_w": 396.0,
            "requested_heater_w": 300.0,
            "granted_heater_w": 84.0,
            "heater_scale": 0.28,
        },
        "extrude_normal": {
            "software_limit_w": 480.0,
            "non_heater_reserve_w": 226.0,
            "requested_heater_w": 84.0,
            "granted_heater_w": 84.0,
            "heater_scale": 1.0,
        },
    }
    report = {
        "status": "SOFTWARE_TIMING_ANALYSIS_NOT_PHYSICAL_SAFETY_VALIDATION",
        "control_loop_period_ms": loop_ms,
        "heartbeat_timeout_ms": heartbeat_timeout_ms,
        "heartbeat_safe_output_latency_max_ms": heartbeat_timeout_ms + loop_ms,
        "avr_watchdog_timeout_nominal_ms": 2000,
        "thermal_no_rise_window_ms": 60000,
        "jam": jam,
        "power_cases": cases,
        "limitations": [
            "E-stop physical opening time is controlled by the selected safety relay/contactor and is not represented here.",
            "480 W is a provisional software ceiling, not a wire, fuse, connector or PSU rating.",
            "Loop latency excludes driver coast-down and mechanical stopping time; physical stop-time measurement is mandatory.",
        ],
    }
    output = ROOT / "simulation" / "control" / "safety_timing.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
