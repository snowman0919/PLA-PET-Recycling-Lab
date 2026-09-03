#!/usr/bin/env python3
"""v0.8 critical interface의 worst-case tolerance stack 단일 생성원."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "final-design-fabrication-closure-v0.8"
JSON_OUT = ROOT / "calculations/tolerance_stack_final.json"
CSV_OUT = ROOT / "exports/final/interface_catalog.csv"
DOC_OUT = ROOT / "docs/tolerance_and_fit_guide_ko.md"


def symmetric(nominal: float, *contributors: float) -> list[float]:
    total = sum(abs(value) for value in contributors)
    return [nominal - total, nominal + total]


def clearance(inner: tuple[float, float], outer: tuple[float, float], divisor: float = 1) -> list[float]:
    return [(inner[0] - outer[1]) / divisor, (inner[1] - outer[0]) / divisor]


def interface(interface_id: str, part_a: str, part_b: str, nominal: str, limits: list[float], unit: str,
              components: list[str], calculation: str, criterion: str, required_minimum: float,
              fit: str, finish: str, assembly: str, inspection: str, adjustment: str, thermal: str) -> dict:
    low, high = (round(value, 4) for value in limits)
    return {
        "interface_id": interface_id, "part_a": part_a, "part_b": part_b,
        "nominal_dimension": nominal, "minimum": low, "maximum": high, "unit": unit,
        "components": "; ".join(components), "calculation": calculation,
        "criterion": criterion, "required_minimum": required_minimum,
        "fit_tolerance": fit, "surface_finish": finish, "assembly_method": assembly,
        "inspection_method": inspection, "adjustment_shim_method": adjustment,
        "thermal_condition": thermal, "revision": REV,
        "status": "PASS" if low >= required_minimum and high >= low else "FAIL",
    }


def rows() -> list[dict]:
    screw = clearance((16.20, 16.22), (15.90, 15.92), 2)
    heater = clearance((34.00, 34.10), (33.97, 34.00))
    feeder = clearance((25.00, 25.05), (24.55, 24.60), 2)
    ligament = [16.985 - 8.11 - 5.55, 17.00 - 8.10 - 5.45]
    thermal_margin = [1.30 - 1.1662, 1.50 - 1.1662]
    alpha = 12e-6
    hot_screw = [
        (16.20 * (1 + alpha * (245 - 20)) - 15.92 * (1 + alpha * (270 - 20))) / 2,
        (16.22 * (1 + alpha * (270 - 20)) - 15.90 * (1 + alpha * (245 - 20))) / 2,
    ]
    return [
        interface("TS-01", "CUT-01 discs", "CUT-02 spacers/collars", "0.375 selected axial gap", symmetric(.375, .125), "mm", ["selected metal shim/gap 0.375 ±0.125"], "0.375 ± 0.125", "working gap 0.25–0.50", .25, "metal shim controlled", "disc faces Ra≤1.6", "dry stack then collar clamp", "four-position feeler gauge", "0.05/0.10/0.25 mm metal shim only", "20–40 °C dry assembly"),
        interface("TS-02", "CUT-05 shafts", "CUT-03 matched plates", "0.125 axial float", symmetric(.125, .075), "mm", ["collar/bearing datum allowance ±0.05", "selected shim allowance ±0.025"], "0.125 ± (0.050 + 0.025)", "axial float ≥0.05", .05, "one fixed/one floating bearing per shaft", "journal Ra≤0.8", "metal collars retain inner rings", "dial indicator", "select metal shim", "20–80 °C"),
        interface("TS-03", "DRV-03 phase gears", "CUT-03 bearing centres", "48.00 centre / 0.25 backlash", symmetric(.25, .03, .05, .02), "mm", ["centre distance ±0.03", "tooth thickness/backlash ±0.05", "gear runout ±0.02"], "0.25 ± (0.03 + 0.05 + 0.02)", "backlash 0.15–0.35", .15, "centre distance 48.00 ±0.03", "gear flank Ra≤3.2", "key+dowel then bolt", "indicator and blue check", "select 0.05 mm bearing-plate shim", "20–80 °C"),
        interface("TS-04", "CUT-03 front plate", "CUT-03 rear plate", "seat-axis parallelism", [0, .025 + .025], "mm/140mm", ["front matched-seat location ±0.025", "rear matched-seat location ±0.025"], "|front| + |rear| = 0.050 max", "parallelism ≤0.05/140", 0, "match-machine", "seat Ra≤1.6", "temporary datum bars before frame torque", "two ground bars + indicator", "frame foot shim", "20 °C inspection"),
        interface("TS-05", "EX-SCR-01 flight", "EX-BAR-01 bore", "radial cold clearance", screw, "mm", ["bore ID 16.20 +0.02/0", "flight OD 15.92 -0.02/0"], "(ID limit − OD opposite limit) / 2", "radial clearance ≥0.14", .14, "matched supplier pair", "flight/bore Ra≤0.8", "matched supplier pair", "micrometer + 3-point bore gauge at three stations", "reject or finish-hone; no printed shim", "20 °C cold"),
        interface("TS-06", "EX-BAR-01 bore axis", "EX-DIE-01 channel axis", "axis offset", [0, .025 + .025], "mm", ["barrel datum-axis location ±0.025", "die channel-axis location ±0.025"], "|barrel| + |die| = 0.050 max", "axis offset ≤0.05", 0, "dowel/datum controlled", "gasket face Ra≤1.6", "dowel/bolt on copper gasket", "coaxial pin + indicator", "0.05 mm copper face shim", "20 °C assembly / 270 °C check"),
        interface("TS-07", "TH-BH-01 heater ID", "EX-BAR-01 OD", "clamped diametral clearance", heater, "mm", ["TH-BH-01 as-clamped ID 34.00 +0.10/0", "EX-BAR-01 OD 34.00 -0.03/0"], "heater ID limit − barrel OD opposite limit", "diametral clearance ≥0", 0, "custom clamp fit", "barrel Ra≤1.6", "torque band clamp cold", "360° 0.05 mm feeler rejection", "supplier clamp only", "20 °C install / 300 °C design"),
        interface("TS-08", "TEMP-01..03 bore tip", "EX-BAR-01 melt bore", "remaining ligament", ligament, "mm", ["barrel OD radius 16.985–17.000", "melt-bore radius 8.100–8.110", "probe-bore depth 5.45–5.55"], "OD radius − melt radius − blind depth", "ligament ≥3.30", 3.30, "Ø3.20 +0.05/0 blind 5.50 ±0.05", "bore Ra≤3.2", "depth-stop drill/ream", "ultrasonic wall or depth+OD/ID", "reject part; no repair shim", "20 °C inspect / 270 °C analysis"),
        interface("TS-09", "FD-MET-02 auger", "FD-MET-01 housing", "radial running clearance", feeder, "mm", ["housing ID 25.00 +0.05/0", "auger OD 24.60 -0.05/0"], "(housing ID limit − auger OD opposite limit) / 2", "radial clearance ≥0.20", .20, "running fit", "Ra≤3.2 deburred", "Ø8 common auger/agitator shaft with removable coupling", "bore gauge + micrometer", "finish-turn auger OD", "20–80 °C"),
        interface("TS-10", "FM-RL-01 roller pair", "1.75 mm strand", "1.75 loaded roller gap", symmetric(1.75, .10, .05), "mm", ["screw setting ±0.10", "roller TIR contribution ±0.05"], "1.75 ± (0.10 + 0.05)", "gap ≥1.60", 1.60, "spring adjustable", "roller TIR≤0.05", "symmetric screw adjustment", "feeler gauge under lockout", "paired M6 adjusters", "ambient"),
        interface("TS-11", "PPR-C06 X gauge", "PPR-C06 Y gauge", "optical centreline offset", [0, .05 + .05], "mm", ["X fixture centre ±0.05", "Y fixture centre ±0.05"], "|X| + |Y| = 0.10 max", "offset ≤0.10", 0, "fixture aligned", "matte optical bridge", "dowel then fasten", "calibration wire scan", "metal gauge shim", "ambient stable"),
        interface("TS-12", "SP-TR-01 traverse", "Ø8 rods", "rod parallelism", [0, .025 + .025 + .05], "mm/160mm", ["left plate centre ±0.025", "right plate centre ±0.025", "rod straightness 0.05/160"], "|left| + |right| + straightness = 0.10 max", "parallelism ≤0.10/160", 0, "matched end plates", "rod Ra≤0.8", "loose fit then sweep and torque", "indicator full 160 mm span", "end-plate metal shim", "ambient"),
        interface("TS-13", "guards/panels", "moving envelopes", "3.0 static clearance", symmetric(3, .5, .5), "mm", ["nominal CAD gap 3.0", "panel position ±0.5", "motion envelope ±0.5"], "3.0 ± (0.5 + 0.5)", "moving clearance ≥2.0", 2, "metal guard spacers", "deburr R0.3", "fasten after motion sweep", "feeler + envelope CAD", "metal washer/spacer", "cold motion"),
        interface("TS-14", "hot shield", "300 °C hot envelope", "12.0 static clearance", symmetric(12, 1, 1), "mm", ["nominal CAD gap 12.0", "shield position ±1.0", "hot envelope allowance ±1.0"], "12.0 ± (1.0 + 1.0)", "hot clearance ≥10.0", 10, "grounded metal shield", "deburr R0.3", "fasten after thermal-envelope check", "feeler + envelope CAD", "metal washer/spacer", "20→300 °C"),
        interface("TS-15", "EX-MT-02 radial guide", "EX-BAR-01", "remaining axial thermal margin", thermal_margin, "mm", ["available cold travel 1.30–1.50", "predicted 25→270 °C growth 1.1662"], "available travel limit − predicted growth", "remaining travel ≥0", 0, "rear datum fixed; front guide axial sliding", "guide Ra≤1.6 dry-film compatible", "cold datum then verify free slide", "depth gauge before/after heat simulation", "metal stop/shim", "25→270 °C"),
        interface("TS-16", "EX-SCR-01 flight", "EX-BAR-01 bore", "radial hot differential clearance", hot_screw, "mm", ["SCM440 alpha 12e-6/K", "worst bore 245 °C / screw 270 °C", "opposite bound bore 270 °C / screw 245 °C"], "(hot bore ID − hot screw OD) / 2", "hot radial clearance ≥0.13", .13, "matched nitrided SCM440 pair", "flight/bore Ra≤0.8", "cold clearance report then free thermal growth", "temperature map + three-station bore/flight report", "reject or finish-hone; no shim", "20→270 °C differential bound"),
    ]


def main() -> None:
    data = rows()
    if len({item["interface_id"] for item in data}) != len(data) or any(item["status"] != "PASS" for item in data):
        raise SystemExit("FINAL_TOLERANCE_STACK_FAIL")
    JSON_OUT.write_text(json.dumps({"revision": REV, "method": "explicit worst-case arithmetic", "physical_validation_state": "NOT_RUN", "interfaces": data, "status": "PASS"}, indent=2, ensure_ascii=False) + "\n")
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=data[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(data)
    lines = ["# v0.8 공차·끼워맞춤 지침", "", "모든 수치는 component limit의 worst-case 산술 결과다. 실제 수령검사와 물리 조립 시험을 대신하지 않는다.", "", "|ID|인터페이스|Worst-case|계산|", "|---|---|---:|---|"]
    lines += [f"|{r['interface_id']}|{r['part_a']} ↔ {r['part_b']}|{r['minimum']}–{r['maximum']} {r['unit']}|{r['calculation']}|" for r in data]
    lines += ["", "Cutter/blade gap은 출력 공차가 아니라 금속 shim으로만 맞춘다. Heater, cutter, screw 및 고전류 작업의 물리 합격은 별도 lockout·사용자 확인 전까지 `NOT_RUN`이다.", ""]
    DOC_OUT.write_text("\n".join(lines))
    print(f"FINAL_TOLERANCE_STACK_OK interfaces={len(data)}")


if __name__ == "__main__":
    main()
