#!/usr/bin/env python3
"""v0.8 attachment completion criteria를 파일/증적 기준으로 감사한다."""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def present(*paths: str) -> bool:
    return all((ROOT / path).is_file() and (ROOT / path).stat().st_size > 100 for path in paths)


def pdfs(*paths: str) -> bool:
    return all((ROOT / path).is_file() and (ROOT / path).stat().st_size > 10_000 and (ROOT / path).read_bytes()[:5] == b"%PDF-" for path in paths)


def csv_has(path: str, fields: set[str], rows: int = 1) -> bool:
    with (ROOT / path).open() as fh:
        data = list(csv.DictReader(fh))
    return len(data) >= rows and fields <= set(data[0]) and all(all(row.get(field, "").strip() for field in fields) for row in data)


def release_zip_ok() -> bool:
    path = ROOT / "dist/PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION.zip"
    if not path.is_file():
        return False
    with zipfile.ZipFile(path) as zf:
        manifest = json.loads(zf.read("00_START_HERE/release_manifest.json"))
        return manifest["release_state"] == "FABRICATION_CANDIDATE" and manifest["physical_validation_state"] == "NOT_RUN" and len(manifest["files"]) > 100


def main() -> None:
    bom_ids = {row["part_id"] for row in csv.DictReader((ROOT / "exports/final/bom/BOM.csv").open())}
    step_rows = list(csv.DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
    print_rows = list(csv.DictReader((ROOT / "exports/final/print/print_manifest.csv").open()))
    checks = {
        "baseline_and_archive": present("validation/v0.8/baseline.json", "docs/archive/v0.7_exploratory_index.md"),
        "solver_evidence": present("analysis/final_validation/results/v0.8/summary.json", "simulation/openmodelica/results_v0.8/summary.json", "docs/final/solver_validation_ko.md"),
        "final_step": len(step_rows) >= 20 and all(row["status"] == "PASS" for row in step_rows),
        "print_package": len(print_rows) == 12 and all(row["slicer_status"] == "PASS" and row["status"] == "PASS" for row in print_rows),
        "hot_zone_manufacturing": csv_has("exports/final/manufacturing/hot_zone/manifest.csv", {"part_id", "revision", "quantity", "material", "process", "critical_tolerance", "inspection", "status"}, 5) and len(list((ROOT / "exports/final/manufacturing/hot_zone").glob("*.dxf"))) == 5 and len(list((ROOT / "exports/final/manufacturing/hot_zone").glob("*.step"))) == 5 and len(list((ROOT / "exports/final/manufacturing/hot_zone").glob("*.pdf"))) == 5,
        "hot_zone_bom": {"EX-MT-01", "EX-MT-02", "EX-MT-03", "EX-MT-04"} <= bom_ids,
        "firmware_binary": present("exports/final/firmware/binaries/filament_recycler_atmega2560.hex", "exports/final/firmware/build_manifest.json"),
        "drawing_register": csv_has("docs/drawings/drawing_register.csv", {"drawing_number", "part_assembly_id", "revision", "source_commit", "pdf", "page", "status"}, 20) and pdfs("docs/final/assembly_drawing_set.pdf"),
        "electrical_final_package": pdfs(
            "exports/final/electrical/system_block_diagram.pdf", "exports/final/electrical/power_distribution.pdf",
            "exports/final/electrical/full_wiring_diagram.pdf", "exports/final/electrical/safety_chain.pdf",
            "exports/final/electrical/Arduino_Mega_pinmap.pdf", "exports/final/electrical/grounding_bonding.pdf",
            "exports/final/electrical/enclosure_layout.pdf", "exports/final/electrical/cable_routing.pdf",
        ) and csv_has("exports/final/electrical/wire_schedule.csv", {"wire_id", "from", "to", "voltage", "maximum_current", "wire_gauge", "colour", "connector", "terminal", "fuse", "routing", "shield_ground", "strain_relief"}, 10) and csv_has("exports/final/electrical/connector_schedule.csv", {"connector_id", "wire_id", "from", "to", "terminal", "retention", "rating"}) and csv_has("exports/final/electrical/fuse_schedule.csv", {"fuse_id", "branch", "rating", "maximum_current", "dc_interrupt_rating", "basis"}),
        "final_manual_set": pdfs(
            "docs/final/complete_build_manual_ko.pdf", "docs/final/exploded_views_ko.pdf",
            "docs/final/tolerance_and_fit_guide_ko.pdf", "docs/final/electrical_assembly_ko.pdf",
            "docs/final/firmware_and_calibration_ko.pdf", "docs/final/maintenance_manual_ko.pdf",
        ),
        "commissioning_set": pdfs(
            "docs/final/pre_power_checklist_ko.pdf", "docs/final/first_power_on_ko.pdf", "docs/final/dry_run_ko.pdf",
            "docs/final/heater_commissioning_ko.pdf", "docs/final/shredder_commissioning_ko.pdf",
            "docs/final/PLA_process_startup_ko.pdf", "docs/final/PET_process_startup_ko.pdf",
            "docs/final/material_change_purge_ko.pdf", "docs/final/physical_validation_plan_ko.pdf",
        ),
        "multimodal_review": present("validation/multimodal_final_review.json", "docs/final/multimodal_review_ko.md") and json.loads((ROOT / "validation/multimodal_final_review.json").read_text())["status"] == "PASS",
        "release_package": present(
            "release/build_fabrication_release.py", "release/verify_fabrication_release.py",
            "release/release_manifest.schema.json", "release/active_part_set.json", "release/package_layout.json",
        ) and release_zip_ok(),
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
