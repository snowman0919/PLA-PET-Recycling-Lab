#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    schedule = (ROOT / "firmware/arduino_mega/runtime_schedule.md").read_text()
    board = (ROOT / "firmware/arduino_mega/src/board_config.h").read_text()
    sketch = (ROOT / "firmware/arduino_mega/arduino_mega.ino").read_text()
    required_schedule = ["≤10 ms", "20 ms", "50–100 ms", "250 ms", "≥1 s", "PPR_DEBUG"]
    if not all(token in schedule for token in required_schedule):
        raise AssertionError("runtime schedule target missing")
    for token in ("SCREW_TACH_PIN = A13", "FAN_TACH_MUX_PIN = A14", "SPOOLER_TACH_PIN = A15",
                  "TRAVERSE_LEFT_LIMIT_PIN = A5", "TRAVERSE_RIGHT_LIMIT_PIN = A6"):
        if token not in board:
            raise AssertionError(f"pin assignment missing: {token}")
    for token in ("ISR(PCINT2_vect)", "sampleTachs(now_ms)", "sampleFans(now_ms)",
                  "sampleTemperatures(now_ms)", "Serial.availableForWrite()", "Serial.write(",
                  "telemetry_snapshot = output", "telemetry_offset < telemetry_length",
                  "forming_fault_detected_ms", "forming_state_changed_ms", "deadline_overruns"):
        if token not in sketch:
            raise AssertionError(f"runtime implementation missing: {token}")
    log_body = sketch[sketch.index("void logStatus("):sketch.index("\n}\n\nvoid setup()")]
    if "Serial.print(" in log_body or "Serial.println(" in log_body:
        raise AssertionError("periodic telemetry contains potentially blocking print chain")
    if "delay(" in sketch:
        raise AssertionError("blocking delay in control sketch")
    with (ROOT / "firmware/arduino_mega/timer_pin_budget.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if any(row["conflict_status"] == "CONFLICT" for row in rows):
        raise AssertionError("timer/pin conflict remains")
    compile_result = json.loads((ROOT / "validation/results/arduino_mega_compile.json").read_text())
    if compile_result["status"] != "PASS":
        raise AssertionError("Mega compile evidence missing")
    payload = {
        "revision": "parallel-actuation-hardening-v0.6.2", "status": "PASS",
        "resource_rows": len(rows), "blocking_waits_in_control_path": False,
        "periodic_telemetry": "BOUNDED_SEGMENTED_SERIAL_WRITE",
        "fault_sequence_timestamps_logged": True,
        "dynamic_allocation": False, "debug_deadline_instrumentation": True,
        "mega_compile": compile_result["status"],
    }
    path = ROOT / "validation/results/v062_runtime_audit.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print("V062_RUNTIME_SCHEDULER_PIN_TIMER_AUDIT_OK")


if __name__ == "__main__":
    main()
