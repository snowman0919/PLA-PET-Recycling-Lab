#!/usr/bin/env python3
"""Build traceable DFM/RFQ precheck packages from the system BOM."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "cnc_quote_packages"
FIELDS = [
    "Part ID", "Module", "Quantity", "Description", "Primary source type",
    "Model STEP", "Profile DXF", "Drawing notes", "Material baseline",
    "Process baseline", "Critical characteristics", "RFQ status", "Open release gates",
]

PART_TO_STEP = {
    "SHR-SHAFT-001": "exports/step/stage1_shredder_proof.step",
    "SHR-CUT-001": "exports/step/stage1_cutter_disc.step",
    "SHR-PLATE-001": "exports/step/stage1_bearing_plate.step",
    "SHR-SPACER-001": "exports/step/stage1_cutter_stack.step",
    "SHR-RET-001": "exports/step/stage1_cutter_stack.step",
    "SHR2-SHAFT-001": "exports/step/stage2_shredder_proof.step",
    "SHR2-ROTOR-001": "exports/step/stage2_rotor.step",
    "SHR2-KNIFE-001": "exports/step/stage2_bed_knife.step",
    "SHR2-CARRIER-001": "exports/step/stage2_shredder_proof.step",
    "SHR2-PLATE-001": "exports/step/stage2_bearing_plate.step",
    "SHR2-RET-001": "exports/step/stage2_shredder_proof.step",
    "GRN-SHAFT-001": "exports/step/stage3_granulator_proof.step",
    "GRN-ROTOR-001": "exports/step/stage3_rotor.step",
    "GRN-STATOR-001": "exports/step/stage3_stator.step",
    "GRN-CARRIER-001": "exports/step/stage3_granulator_proof.step",
    "GRN-SCREEN-SET": "exports/step/stage3_screen_5mm.step",
    "GRN-PLATE-001": "exports/step/stage3_bearing_plate.step",
    "GRN-RET-001": "exports/step/stage3_granulator_proof.step",
    "SRT-TRAY-001": "exports/step/vibratory_sorter_proof.step",
    "SRT-MNT-001": "exports/step/vibratory_sorter_proof.step",
    "DRY-BASE-001": "exports/step/dryer_feeder_proof.step",
    "DRY-VSL-001": "exports/step/dryer_metal_hopper.step",
    "DRY-LID-001": "exports/step/dryer_feeder_proof.step",
    "DRY-AGT-001": "exports/step/dryer_feeder_proof.step",
    "DRY-GATE-001": "exports/step/dryer_feeder_proof.step",
    "DRY-FDR-001": "exports/step/dryer_metering_auger.step",
    "EXT-SCR-001": "exports/step/extruder_screw.step",
    "EXT-BRL-001": "exports/step/extruder_barrel.step",
    "EXT-BRK-001": "exports/step/extruder_breaker_plate.step",
    "EXT-DIE-001": "exports/step/extruder_die.step",
    "EXT-THR-001": "exports/step/extruder_thrust_plate.step",
    "INP-GATE-001": "exports/step/classifier_gate_pair.step",
    "BIN-DIV-001": "exports/step/classification_storage_proof.step",
    "CTL-ASM-001": "exports/step/control_enclosure_proof.step",
}

PART_TO_DXF = {
    "SHR-PLATE-001": "exports/dxf/stage1_bearing_plate.dxf",
    "SHR2-PLATE-001": "exports/dxf/stage2_bearing_plate.dxf",
    "GRN-PLATE-001": "exports/dxf/stage3_bearing_plate.dxf",
    "SRT-TRAY-001": "exports/dxf/sorter_base_plate.dxf",
    "DRY-BASE-001": "exports/dxf/dryer_base_plate.dxf",
    "EXT-THR-001": "exports/dxf/extruder_thrust_plate.dxf",
    "INP-GATE-001": "exports/dxf/classifier_gate_half.dxf",
    "CTL-ASM-001": "exports/dxf/control_door_half.dxf",
}

MODULE_DRAWING = {
    "Stage 1": "exports/drawings/stage1_cutter_notes.md",
    "Stage 2": "exports/drawings/stage2_rotor_bed_knife_notes.md",
    "Stage 3": "exports/drawings/stage3_granulator_notes.md",
    "Vibratory sorter": "exports/drawings/vibratory_sorter_notes.md",
    "Dryer": "exports/drawings/dryer_feeder_notes.md",
    "Extruder": "exports/drawings/extruder_notes.md",
    "Input classification": "exports/drawings/input_classifier_notes.md",
    "Classification storage": "exports/drawings/input_classifier_notes.md",
    "Control enclosure": "exports/drawings/control_enclosure_notes.md",
}


def package_for(module: str) -> str:
    if module in {"Stage 1", "Stage 2", "Stage 3"}:
        return "shredder_package.csv"
    if module == "Extruder":
        return "extruder_package.csv"
    return "sheet_metal_package.csv"


def characteristics(part_id: str) -> str:
    if "SHAFT" in part_id:
        return "bearing-seat fit; shoulder location; keyway; total indicated runout"
    if any(token in part_id for token in ("CUT", "KNIFE", "STATOR")):
        return "profile; edge geometry; flatness; hardness and heat-treatment certificate"
    if "ROTOR" in part_id:
        return "bearing-axis concentricity; pocket position; balance; no weld in proof rotor"
    if "PLATE" in part_id or part_id == "EXT-THR-001":
        return "datum flatness; bore position/fit; thickness; fastener pattern"
    if "SCREEN" in part_id:
        return "hole size/open area; flatness; edge retention; three coupon variants"
    if part_id == "EXT-SCR-001":
        return "flight profile; root diameter; pitch; runout; surface finish; heat treatment"
    if part_id == "EXT-BRL-001":
        return "finished bore; straightness; concentricity; pressure material traceability"
    if part_id == "EXT-BRK-001":
        return "hole pattern; sealing faces; screen retention; pressure-rated material"
    if part_id == "EXT-DIE-001":
        return "3.0 mm bore; 12 mm land; concentricity; polished flow surface"
    return "interface datums; hole pattern; flatness; service clearance; deburred edges"


def main() -> None:
    with (ROOT / "bom" / "bom.csv").open(newline="", encoding="utf-8") as handle:
        bom = list(csv.DictReader(handle))
    selected = [
        row for row in bom
        if row["Source type"] in {"CNC", "FABRICATE"} or row["Part ID"] == "EXT-THR-001"
    ]
    assert {row["Part ID"] for row in selected} == set(PART_TO_STEP)
    packages: dict[str, list[dict[str, str]]] = {
        "shredder_package.csv": [],
        "extruder_package.csv": [],
        "sheet_metal_package.csv": [],
    }
    for row in selected:
        part_id = row["Part ID"]
        step = PART_TO_STEP[part_id]
        dxf = PART_TO_DXF.get(part_id, "NOT_PROVIDED_USE_STEP_FOR_DFM")
        drawing = MODULE_DRAWING[row["Module"]]
        assert (ROOT / step).is_file()
        assert dxf.startswith("NOT_PROVIDED") or (ROOT / dxf).is_file()
        assert (ROOT / drawing).is_file()
        packages[package_for(row["Module"])].append({
            "Part ID": part_id,
            "Module": row["Module"],
            "Quantity": row["Quantity"],
            "Description": row["Description"],
            "Primary source type": row["Source type"],
            "Model STEP": step,
            "Profile DXF": dxf,
            "Drawing notes": drawing,
            "Material baseline": row["Material"],
            "Process baseline": row["Manufacturing method"],
            "Critical characteristics": characteristics(part_id),
            "RFQ status": "RFQ_PRECHECK_ONLY_NOT_FABRICATION_RELEASE",
            "Open release gates": row["Validation evidence"] + "; final material/tolerance/heat-treatment/DFM approval",
        })
    for filename, rows in packages.items():
        with (OUT / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    counts = Counter(package_for(row["Module"]) for row in selected)
    readme = [
        "# CNC·sheet-fabrication RFQ precheck package",
        "",
        "상태: `RFQ_PRECHECK_ONLY / NOT_FABRICATION_RELEASED / NO_ORDER_AUTHORIZED`.",
        "",
        "이 디렉터리는 업체가 공정 가능성·누락 정보·대략 견적 범위를 회신할 수 있도록 BOM Part ID를 STEP/DXF/도면 메모에 묶는다. 최종 치수도·GD&T·재료 규격·열처리·표면처리·검사 성적서 요구가 닫히지 않았으므로 즉시 제작용 도면 세트가 아니다.",
        "",
        "| 패키지 | 행 수 | 범위 |",
        "|---|---:|---|",
        f"| `shredder_package.csv` | {counts['shredder_package.csv']} | Stage 1/2/3 shaft cutter rotor plate screen |",
        f"| `extruder_package.csv` | {counts['extruder_package.csv']} | screw barrel breaker die와 mixed-source thrust plate |",
        f"| `sheet_metal_package.csv` | {counts['sheet_metal_package.csv']} | sorter dryer input gate bin diverter control enclosure |",
        "",
        "## 업체에 요청할 회신",
        "",
        "- 각 Part ID별 공정·setup·최소수량·단가·lead time·재료/열처리/검사 포함 여부",
        "- STEP와 DXF 불일치 또는 가공 불가능 형상 및 필요한 공차 완화",
        "- pressure/hot-zone/cutter 부품의 추적 가능한 소재 증명과 외주 열처리 범위",
        "- 세금·배송·후처리를 분리한 견적과 견적 유효기간",
        "",
        "## 주문 전 필수 gate",
        "",
        "1. Donor shaft/bearing/motor 실측과 coupon 결과를 CAD에 반영한다.",
        "2. Cutter impact/containment와 extruder pressure/relief risk review를 닫는다.",
        "3. 부품별 datum·fit·GD&T·표면거칠기·열처리·검사표가 있는 최종 도면을 승인한다.",
        "4. 사용자에게 실제 견적과 예산 차이를 제시하고 명시적 발주 승인을 받는다.",
        "",
        "`EXT-THR-001`은 BOM primary source가 BUY인 bearing assembly에 plate machining이 섞인 행이라 extruder package에 보조로 포함했다. 따라서 package 34행과 BOM의 primary CNC/FABRICATE 33행은 모순이 아니다. 비용 rollup은 primary source 기준이며 mixed-source 비용은 여전히 TBD다.",
    ]
    (OUT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(f"CNC_RFQ_PACKAGES_OK rows={len(selected)}")


if __name__ == "__main__":
    main()
