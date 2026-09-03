#!/usr/bin/env python3
"""v0.8 critical interface/tolerance catalog의 단일 생성원."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "final-design-fabrication-closure-v0.8"
JSON_OUT = ROOT / "calculations" / "tolerance_stack_final.json"
CSV_OUT = ROOT / "exports" / "final" / "interface_catalog.csv"
DOC_OUT = ROOT / "docs" / "tolerance_and_fit_guide_ko.md"


def interface(interface_id: str, part_a: str, part_b: str, nominal: str, limits: list[float], unit: str,
              fit: str, finish: str, assembly: str, inspection: str, adjustment: str, thermal: str) -> dict:
    return {
        "interface_id": interface_id, "part_a": part_a, "part_b": part_b,
        "nominal_dimension": nominal, "minimum": limits[0], "maximum": limits[1], "unit": unit,
        "fit_tolerance": fit, "surface_finish": finish, "assembly_method": assembly,
        "inspection_method": inspection, "adjustment_shim_method": adjustment,
        "thermal_condition": thermal, "revision": REV,
        "status": "PASS" if limits[0] >= 0 else "FAIL",
    }


def rows() -> list[dict]:
    screw_min = (16.20 - 15.92) / 2
    screw_max = (16.22 - 15.90) / 2
    return [
        interface("TS-01", "CUT-01 discs", "CUT-02 spacers/collars", "0.375 axial working gap", [0.25, 0.50], "mm", "metal shim controlled", "disc faces Ra≤1.6", "dry stack then collar clamp", "four-position feeler gauge", "0.05/0.10/0.25 mm metal shim only", "20–40 °C dry assembly"),
        interface("TS-02", "CUT-05 shafts", "CUT-03 matched plates", "dual-shaft axial datum", [0.05, 0.20], "mm", "one fixed/one floating bearing per shaft", "journal Ra≤0.8", "metal collars retain inner rings", "dial indicator", "select metal shim", "20–80 °C"),
        interface("TS-03", "DRV-03 phase gears", "CUT-03 bearing centres", "48.00 centre / backlash", [0.15, 0.35], "mm", "centre distance ±0.03", "gear flank Ra≤3.2", "key+dowel then bolt", "indicator and blue check", "select 0.05 mm bearing-plate shim", "20–80 °C"),
        interface("TS-04", "CUT-03 front plate", "CUT-03 rear plate", "seat-axis parallelism", [0.00, 0.05], "mm/140mm", "match-machine", "seat Ra≤1.6", "temporary datum bars before frame torque", "two ground bars + indicator", "frame foot shim", "20 °C inspection"),
        interface("TS-05", "EX-SCR-01 flight", "EX-BAR-01 bore", "radial cold clearance", [round(screw_min, 3), round(screw_max, 3)], "mm", "flight Ø15.92 -0.02/0; bore Ø16.20 +0.02/0", "flight/bore Ra≤0.8", "matched supplier pair", "micrometer + 3-point bore gauge at three stations", "reject or finish-hone; no printed shim", "20 °C cold"),
        interface("TS-06", "EX-BAR-01 bore axis", "EX-DIE-01 channel axis", "axis offset", [0.00, 0.05], "mm", "datum face flatness 0.03", "gasket face Ra≤1.6", "dowel/bolt on copper gasket", "coaxial pin + indicator", "0.05 mm copper face shim", "20 °C assembly / 270 °C check"),
        interface("TS-07", "HT-BAND-01", "EX-BAR-01 OD", "clamped diametral fit", [0.00, 0.15], "mm", "band clamp range includes Ø33.95–34.05", "barrel Ra≤1.6", "torque band clamp cold", "360° 0.05 mm feeler rejection", "supplier clamp only", "20 °C install / 300 °C design"),
        interface("TS-08", "TEMP-01..03 bore tip", "EX-BAR-01 melt bore", "remaining ligament", [3.35, 3.45], "mm", "Ø3.20 +0.05/0 blind 5.50 ±0.05", "bore Ra≤3.2", "depth-stop drill/ream", "ultrasonic wall or depth+OD/ID", "reject part; no repair shim", "20 °C inspect / 270 °C analysis"),
        interface("TS-09", "PF-04 auger", "PF-05 housing", "radial running clearance", [1.45, 1.55], "mm", "OD24.0 ±0.05 / ID27.0 ±0.05", "Ra≤3.2 deburred", "removable metal thrust retention", "bore gauge + micrometer", "finish-turn auger", "20–80 °C"),
        interface("TS-10", "FM-RL-01 roller pair", "1.75 mm strand", "loaded roller gap", [1.60, 1.90], "mm", "spring adjustable", "roller TIR≤0.05", "symmetric screw adjustment", "feeler gauge under lockout", "paired M6 adjusters", "ambient"),
        interface("TS-11", "PPR-C06 X gauge", "PPR-C06 Y gauge", "optical centreline offset", [0.00, 0.10], "mm", "fixture aligned", "matte optical bridge", "dowel then fasten", "calibration wire scan", "metal gauge shim", "ambient stable"),
        interface("TS-12", "SP-TR-01 traverse", "spool winding width", "rod parallelism", [0.00, 0.10], "mm/160mm", "matched end plates", "rod Ra≤0.8", "loose fit then sweep and torque", "indicator full stroke", "end-plate metal shim", "ambient"),
        interface("TS-13", "guards/panels", "moving/hot envelopes", "minimum static clearance", [2.00, 12.00], "mm", "2 mm moving / 10 mm hot nominal minima", "deburr R0.3", "fasten after motion sweep", "feeler + envelope CAD", "metal washer/spacer", "cold motion and 300 °C hot-zone envelope"),
        interface("TS-14", "EX-MT-02 radial guide", "EX-BAR-01", "available axial thermal travel", [1.30, 1.50], "mm", "rear datum fixed; front guide axial sliding", "guide Ra≤1.6 dry-film compatible", "cold datum then verify free slide", "depth gauge before/after heat simulation", "metal stop/shim", "25→270 °C; predicted growth 1.166 mm"),
    ]


def main() -> None:
    data = rows()
    if len({item["interface_id"] for item in data}) != len(data) or any(item["status"] != "PASS" for item in data):
        raise SystemExit("FINAL_TOLERANCE_STACK_FAIL")
    JSON_OUT.write_text(json.dumps({"revision": REV, "physical_validation_state": "NOT_RUN", "interfaces": data, "status": "PASS"}, indent=2, ensure_ascii=False) + "\n")
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=data[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(data)
    lines = ["# v0.8 공차·끼워맞춤 지침", "", "모든 수치는 디지털 제작 한계다. 실제 수령검사와 물리 조립 시험을 대신하지 않는다.", "", "|ID|인터페이스|허용 범위|조정|열 조건|", "|---|---|---:|---|---|"]
    lines += [f"|{r['interface_id']}|{r['part_a']} ↔ {r['part_b']}|{r['minimum']}–{r['maximum']} {r['unit']}|{r['adjustment_shim_method']}|{r['thermal_condition']}|" for r in data]
    lines += ["", "Cutter/blade gap은 출력 공차가 아니라 금속 shim으로만 맞춘다. Heater, cutter, screw 및 고전류 작업의 물리 합격은 별도 lockout·사용자 확인 전까지 `NOT_RUN`이다.", ""]
    DOC_OUT.write_text("\n".join(lines))
    print(f"FINAL_TOLERANCE_STACK_OK interfaces={len(data)}")


if __name__ == "__main__":
    main()
