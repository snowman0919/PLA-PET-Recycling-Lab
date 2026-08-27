#!/usr/bin/env python3
"""Static safety/interface consistency checks."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    pinout_path = ROOT / "electronics" / "pinout" / "mega_pinout.csv"
    with pinout_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows and list(rows[0]) == [
        "Signal",
        "Direction",
        "Voltage domain",
        "Proposed pin",
        "Safe state",
        "Criticality",
        "Status",
        "Notes",
    ]
    by_signal = {row["Signal"]: row for row in rows}
    required = {
        "E_STOP_AUX",
        "CONTACTOR_FEEDBACK",
        "LID_INTERLOCK_AUX",
        "SERVICE_INTERLOCK_AUX",
        "THERMAL_CHAIN_AUX",
        "PRESSURE_TRIP_AUX",
        "EXT_HEATER_ZONE1",
        "EXT_HEATER_ZONE2",
        "EXT_HEATER_ZONE3",
        "EXT_HEATER_DIE",
        "SHREDDER_ENABLE",
        "EXTRUDER_ENABLE",
        "PULLER_ENABLE",
        "SPOOLER_ENABLE",
    }
    assert required <= by_signal.keys()
    assert not any(row["Status"] == "UNASSIGNED" for row in rows)

    occupied: dict[str, str] = {}
    alias = {"A12": "D66", "A13": "D67", "A14": "D68", "A15": "D69"}
    for row in rows:
        for pin in re.findall(r"(?:D|A)\d+", row["Proposed pin"]):
            normalized = alias.get(pin, pin)
            assert normalized not in occupied or occupied[normalized] == row["Signal"], (
                f"pin collision {normalized}: {occupied.get(normalized)} / {row['Signal']}"
            )
            occupied[normalized] = row["Signal"]
    for signal in ("E_STOP_AUX", "LID_INTERLOCK_AUX", "SERVICE_INTERLOCK_AUX", "THERMAL_CHAIN_AUX"):
        assert "open=fault" in by_signal[signal]["Safe state"]
    for signal in ("EXT_HEATER_ZONE1", "EXT_HEATER_ZONE2", "EXT_HEATER_ZONE3", "EXT_HEATER_DIE"):
        assert "LOW/off" in by_signal[signal]["Safe state"]
        assert "fuse" in by_signal[signal]["Notes"].lower()

    with (ROOT / "electronics" / "wiring" / "harness_schedule.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        harnesses = list(csv.DictReader(handle))
    assert len(harnesses) == 18
    assert {row["Harness"] for row in harnesses} == {f"H{number:02d}" for number in range(1, 19)}
    assert any("protective-earth" in row["From"].lower() for row in harnesses)

    config = (ROOT / "firmware" / "arduino_mega" / "src" / "configuration.h").read_text()
    assert config.count("Qualified = false") == 4, "commissioning locks unexpectedly opened"
    protocol = (ROOT / "electronics" / "protocol" / "frp1.md").read_text()
    assert "750 ms" in protocol and "CRC-16/CCITT-FALSE" in protocol

    timing = json.loads((ROOT / "simulation" / "control" / "safety_timing.json").read_text())
    assert timing["heartbeat_safe_output_latency_max_ms"] <= 760
    assert timing["jam"]["maximum_retries"] == 3
    assert timing["jam"]["persistent_jam_to_latched_fault_max_ms"] < 7500
    assert timing["power_cases"]["extrude_worst_case"]["granted_heater_w"] == 84.0
    print("ELECTRONICS_INTERFACES_OK")


if __name__ == "__main__":
    main()
