#!/usr/bin/env python3
"""v0.8 attachment completion criteria를 파일/증적 기준으로 감사한다."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def present(*paths: str) -> bool:
    return all((ROOT / path).is_file() and (ROOT / path).stat().st_size > 100 for path in paths)


def main() -> None:
    bom_ids = {row["part_id"] for row in csv.DictReader((ROOT / "bom/bom.csv").open())}
    step_rows = list(csv.DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
    print_rows = list(csv.DictReader((ROOT / "exports/print/print_manifest.csv").open()))
    checks = {
        "baseline_and_archive": present("validation/v0.8/baseline.json", "docs/archive/v0.7_exploratory_index.md"),
        "solver_evidence": present("analysis/final_validation/results/v0.8/summary.json", "simulation/openmodelica/results_v0.8/summary.json", "docs/final/solver_validation_ko.md"),
        "final_step": len(step_rows) == 10 and all(row["status"] == "PASS" for row in step_rows),
        "print_package": len(print_rows) == 12 and all(row["slicer_status"] == "PASS" for row in print_rows),
        "hot_zone_manufacturing": present("exports/final/manufacturing/hot_zone/hot_zone_mount_drawings.pdf") and len(list((ROOT / "exports/final/manufacturing/hot_zone").glob("*.dxf"))) == 4,
        "hot_zone_bom": {"EX-MT-01", "EX-MT-02", "EX-MT-03", "EX-MT-04"} <= bom_ids,
        "firmware_binary": present("exports/final/firmware/binaries/filament_recycler_atmega2560.hex", "validation/results/arduino_mega_compile.json"),
        "drawing_register": present("docs/drawings/drawing_register.csv"),
        "electrical_final_package": present(
            "exports/final/electrical/system_block_diagram.pdf", "exports/final/electrical/power_distribution.pdf",
            "exports/final/electrical/full_wiring_diagram.pdf", "exports/final/electrical/safety_chain.pdf",
            "exports/final/electrical/connector_schedule.csv", "exports/final/electrical/wire_schedule.csv",
            "exports/final/electrical/fuse_schedule.csv", "exports/final/electrical/grounding_bonding.pdf",
        ),
        "final_manual_set": present(
            "docs/final/complete_build_manual_ko.pdf", "docs/final/exploded_views_ko.pdf",
            "docs/final/tolerance_and_fit_guide_ko.pdf", "docs/final/electrical_assembly_ko.pdf",
            "docs/final/firmware_and_calibration_ko.pdf", "docs/final/maintenance_manual_ko.pdf",
        ),
        "commissioning_set": present(
            "docs/final/pre_power_checklist_ko.pdf", "docs/final/first_power_on_ko.pdf", "docs/final/dry_run_ko.pdf",
            "docs/final/heater_commissioning_ko.pdf", "docs/final/shredder_commissioning_ko.pdf",
            "docs/final/PLA_process_startup_ko.pdf", "docs/final/PET_process_startup_ko.pdf",
            "docs/final/material_change_purge_ko.pdf", "docs/final/physical_validation_plan_ko.pdf",
        ),
        "multimodal_review": present("validation/multimodal_final_review.json", "docs/final/multimodal_review_ko.md"),
        "release_package": present(
            "release/build_fabrication_release.py", "release/verify_fabrication_release.py",
            "release/release_manifest.schema.json", "release/active_part_set.json", "release/package_layout.json",
            "dist/PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION.zip",
        ),
    }
    result = {
        "revision": "final-design-fabrication-closure-v0.8",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "status": "PASS" if all(checks.values()) else "IN_PROGRESS",
        "physical_validation_state": "NOT_RUN",
        "procurement_gate": "USER_APPROVAL_REQUIRED",
        "commissioning_gate": "USER_APPROVAL_REQUIRED",
    }
    out = ROOT / "validation/results/v08_release_inventory.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    rows = ["# v0.8 릴리스 준비도", "", "물리 시험·안전 인증이 아닌 디지털 산출물 감사다.", ""]
    rows += [f"- `{'PASS' if ok else 'PENDING'}` {name}" for name, ok in checks.items()]
    rows += ["", f"결과: {result['passed']}/{result['total']} — `{result['status']}`", ""]
    (ROOT / "docs/final/release_readiness_ko.md").write_text("\n".join(rows))
    print(f"V08_RELEASE_INVENTORY_{result['status']} {result['passed']}/{result['total']}")


if __name__ == "__main__":
    main()
