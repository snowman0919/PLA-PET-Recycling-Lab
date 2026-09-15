#!/usr/bin/env python3
"""Fail closed when fabrication-facing handoff drifts from current v0.8 contracts."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "release"))
import build_bom_release as bom  # noqa: E402
import build_final_documents as docs  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    joint = next(row for row in bom.fasteners() if row["joint_id"] == "SYS-04")
    require(joint["specification"] == "M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1", "SYS-04 fastener drift")
    require(joint["torque_Nm"] == "1.5", "SYS-04 torque drift")
    require(joint["verification_state"] == "RELEASED_DIGITAL_PHYSICAL_NOT_RUN", "SYS-04 state drift")
    require("engagement6.82-7.40" in joint["inspection"] and "thread-bottom clearance0.60-1.18" in joint["inspection"], "SYS-04 stack drift")

    rows = {row["step_number"]: row for row in docs.assembly_rows()}
    step11 = rows["11"]
    step13 = rows["13"]
    require("cold axial free travel≥1.50 mm" in step11["clearance_tolerance"], "assembly step11 travel drift")
    require("hot calculated endplay" not in step11["clearance_tolerance"], "obsolete hot endplay remains controlling")
    require("first thermal cycle hard-stop contact 0" in step11["clearance_tolerance"], "thermal hard-stop check missing")
    require("M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1" in step13["fasteners"], "assembly step13 SYS-04 drift")
    require("SYS-04: 1.5 N·m" in step13["torque"], "assembly step13 torque drift")

    standalone = text("docs/final/hot_zone_mount_drawings.typ")
    require("cold axial free travel ≥1.50 mm" in standalone, "hot-zone drawing travel drift")
    require("cold axial travel ≥1.30 mm" not in standalone, "obsolete 1.30 mm hot-zone drawing value")

    rfq = text("exports/cnc/extruder/rfq_drawing_ko.typ")
    require("42.5±0.1" in rfq and "dry1.50 N·m" in rfq, "supplier RFQ SYS-04 drift")
    require("4×M4×40 class 10.9" not in rfq, "obsolete M4x40 remains supplier-facing")

    build = text("docs/build_manual_ko.typ")
    require("42.5±0.1" in build and "1.50 N·m" in build, "build manual SYS-04 drift")
    require("4×M4×40 class 10.9" not in build, "obsolete M4x40 remains in build manual")

    report = text("docs/design_report_ko.typ")
    require("42.5±0.1" in report and "1.50 N·m" in report, "design report SYS-04 drift")
    require("4×M4×40 class 10.9" not in report, "obsolete M4x40 remains in design report")

    with (ROOT / "docs/final/assembly_steps.csv").open(newline="", encoding="utf-8") as fh:
        generated = {row["step_number"]: row for row in csv.DictReader(fh)}
    require("cold axial free travel≥1.50 mm" in generated["11"]["clearance_tolerance"], "generated assembly CSV travel drift")
    require("hot calculated endplay" not in generated["11"]["clearance_tolerance"], "generated assembly CSV obsolete endplay")
    require("M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1" in generated["13"]["fasteners"], "generated assembly CSV SYS-04 drift")

    complete = text("docs/final/complete_build_manual_ko.typ")
    require("cold axial free travel≥1.50 mm" in complete, "complete manual travel drift")
    require("travel≥1.30 mm" not in complete, "obsolete 1.30 mm complete-manual value")

    pet = text("docs/final/PET_process_startup_ko.typ")
    require("cold axial travel ≥1.50 mm" in pet and "hard-stop 접촉 0" in pet, "PET startup thermal travel drift")
    require("hot-zone travel ≥1.30 mm" not in pet, "obsolete PET travel criterion")

    die_path = ROOT / "analysis/final_validation/results/v0.8/die_joint_qualification.json"
    if die_path.is_file():
        die = json.loads(die_path.read_text())
        require(die["status"] == "PASS" and die["physical_validation_state"] == "NOT_RUN", "die qualification state drift")
        require(abs(die["assembly_torque_nm"] - 1.5) < 1e-12, "die qualification torque drift")
        die_evidence = "generated-crosscheck=PASS"
    else:
        die_evidence = "generated-crosscheck=NOT_PRESENT; committed fastener registry checked"

    print(f"FABRICATION_HANDOFF_CONSISTENCY_PASS SYS04=42.5mm@1.5Nm travel=1.50mm physical=NOT_RUN {die_evidence}")


if __name__ == "__main__":
    main()
