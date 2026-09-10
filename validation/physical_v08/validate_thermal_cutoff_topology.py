#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "control/thermal_cutoff_contract.json"
THERMAL = ROOT / "exports/thermal"
ELECTRICAL = ROOT / "exports/final/electrical"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inv = contract["inventory"]
    devices = [item["id"] for item in contract["installed_devices"]]
    require(devices == ["TF-BARREL", "TF-DIE"], "installed cutoff IDs drift")
    require(inv == {"procurement_quantity": 3, "installed_quantity": 2, "spare_quantity": 1}, "cutoff inventory drift")
    require(contract["policy"]["heater_branch_thermal_fuse"] is False, "branch thermal-fuse policy drift")
    require(contract["policy"]["k0_coil_series_cutoff"] is True, "K0 cutoff policy drift")

    exported = json.loads((THERMAL / "thermal_cutoff_topology.json").read_text(encoding="utf-8"))
    require(exported == contract, "thermal exported topology differs from control contract")

    manifest = {row["part_id"]: row for row in rows(THERMAL / "manifest.csv")}
    require(manifest["TH-FUSE-01"]["quantity"] == "3", "TH-FUSE-01 procurement quantity must be 3")

    channels = rows(THERMAL / "channel_schedule.csv")
    require([row["channel"] for row in channels] == ["HZ1", "HZ2", "HZ3", "HDIE"], "heater channel set drift")
    for index, row in enumerate(channels, 1):
        expected = f"F-H{index} branch fuse + K0 dual thermal-cutoff chain"
        require(row["hard_cut"] == expected, f"{row['channel']} hard-cut description drift")

    wires = {row["wire_id"]: row for row in rows(ELECTRICAL / "wire_schedule.csv")}
    for index in range(1, 5):
        wire = wires[f"24-H{index}+"]
        require(wire["fuse"] == f"F-H{index} 5 A DC", f"H{index} branch fuse topology drift")
        require("thermal" not in wire["fuse"].lower(), f"H{index} incorrectly carries a branch thermal fuse")
    safety_segments = [(row["from"], row["to"]) for row in wires.values() if row["wire_id"].startswith("SAFE-")]
    require(("S2 service NC", "TF-BARREL thermal cutoff") in safety_segments, "TF-BARREL missing from K0 safety chain")
    require(("TF-BARREL thermal cutoff", "TF-DIE thermal cutoff") in safety_segments, "dual thermal cutoffs are not series-connected")
    require(("TF-DIE thermal cutoff", "K0 contactor A1") in safety_segments, "TF-DIE missing before K0 coil")
    require(len(safety_segments) == 7, "hardwired safety chain must contain seven scheduled wire segments")

    fuses = {row["fuse_id"]: row for row in rows(ELECTRICAL / "fuse_schedule.csv")}
    for index in range(1, 5):
        basis = fuses[f"F-H{index}"]["basis"]
        require("branch overcurrent protection only" in basis, f"F-H{index} role drift")
        require("TF-BARREL/TF-DIE" in basis, f"F-H{index} missing K0 thermal-cut reference")

    safety_doc = (ROOT / "electronics/safety_power_topology.md").read_text(encoding="utf-8")
    require("TF-BARREL -> TF-DIE -> K0 safety contactor/relay coil" in safety_doc, "human safety topology drift")
    require("two installed devices plus one same-spec spare" in safety_doc, "installed/spare allocation missing")

    print("THERMAL_CUTOFF_TOPOLOGY_PASS procurement=3 installed=2 spare=1 safety_segments=7 heater_branches=4")


if __name__ == "__main__":
    main()
