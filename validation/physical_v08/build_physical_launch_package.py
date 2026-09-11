#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHYS = ROOT / "validation/physical_v08"
DIST = ROOT / "dist"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_file(items: list[tuple[Path, str]], source: str, archive: str) -> None:
    path = ROOT / source
    if not path.is_file():
        raise FileNotFoundError(source)
    items.append((path, archive))


def main() -> None:
    subprocess.run(["python3", str(PHYS / "simulation_prerequisite.py")], cwd=ROOT, check=True)
    snapshot = json.loads((PHYS / "simulation_prerequisite.json").read_text(encoding="utf-8"))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if snapshot.get("status") != "PASS" or snapshot.get("head") != head:
        raise SystemExit("fresh P0 PASS snapshot required")

    registry = json.loads((PHYS / "physical_execution_registry.json").read_text(encoding="utf-8"))
    items: list[tuple[Path, str]] = []
    common = [
        "PHYSICAL_EXECUTION_INDEX_KO.md", "PHYSICAL_BUILD_READINESS_KO.md",
        "physical_gate_contract.json", "physical_execution_registry.json",
        "mvp_smoke_contract.json", "MVP_SMOKE_VALIDATION_KO.md",
        "stage_minimum_bom.csv", "fabrication_sequence.csv", "inventory_confirmation.csv",
        "measurement_equipment.csv", "p3_bench_bom.csv", "p3_fixture_contract.json",
        "p5_coupon_contract.json", "p5_supplier_inspection_requirements.csv",
    ]
    docs = {stage["doc"] for stage in registry["stages"] if stage.get("doc")}
    for name in sorted(set(common) | docs):
        add_file(items, f"validation/physical_v08/{name}", f"00_EXECUTION/{name}")

    for path in sorted((PHYS / "templates").iterdir()):
        if path.is_file():
            items.append((path, "01_TEMPLATES/" + path.name))
    for stage in registry["stages"]:
        for entry in stage.get("external_templates", []):
            source = entry.get("source", "")
            archive_name = entry.get("archive_name", "")
            if not source or not archive_name or Path(archive_name).name != archive_name:
                raise SystemExit(f"invalid external template declaration in {stage['id']}")
            add_file(items, source, "01_TEMPLATES/" + archive_name)

    tool_names = {"profile_nesting.py", "build_p5_inquiry_package.py", "build_physical_evidence_package.py", "validate_physical_evidence_package.py",
                  "validate_mvp_smoke_contract.py", "validate_thermal_barrier_tape_contract.py", "analyze_s4_thermal_barrier_tape.py"}
    for stage in registry["stages"]:
        for value in stage.values():
            if isinstance(value, str) and value.endswith(".py"):
                tool_names.add(value)
    for name in sorted(tool_names):
        add_file(items, f"validation/physical_v08/{name}", f"02_ANALYZERS/{name}")

    gate1 = [
        "assembly_ko.md", "bom.csv", "fastener_schedule.csv", "wiring_bom.csv",
        "wiring_24v_hardcut.svg", "test_procedure_ko.md", "preflight_inspection_template.csv",
        "gate1_results_template.csv", "jam_recovery_results_template.csv",
        "chip_size_results_template.csv", "drive_calibration_template.csv",
        "calibration_log_template.csv", "evidence_manifest_template.csv", "gate1_assembly.step",
    ]
    for name in gate1:
        add_file(items, f"exports/jigs/gate1/{name}", f"03_P4_GATE1/{name}")
    for part in ("CUT-01", "CUT-03", "CUT-04", "CUT-05", "CUT-05R", "CUT-08", "CUT-09", "CUT-10"):
        for extension in (".step", ".dxf"):
            add_file(items, f"exports/cnc/{part}/{part}{extension}", f"04_P4_CNC/{part}/{part}{extension}")
        add_file(items, f"exports/cnc/{part}/drawing_notes.md", f"04_P4_CNC/{part}/drawing_notes.md")
    for part in ("DRV-03", "DRV-03R"):
        for extension in (".step", ".dxf"):
            add_file(items, f"exports/drive_interface/parts/{part}/{part}{extension}", f"04_P4_CNC/{part}/{part}{extension}")
        add_file(items, f"exports/drive_interface/parts/{part}/drawing_notes.md", f"04_P4_CNC/{part}/drawing_notes.md")

    for name in ("EX-CPN_drawing.svg", "inspection_report_template.csv", "supplier_rfq_checklist_ko.md"):
        add_file(items, f"exports/cnc/extruder/{name}", f"05_P5_COUPONS/{name}")
    for part in ("EX-CPN-SCR", "EX-CPN-BAR"):
        for extension in (".step", ".dxf"):
            add_file(items, f"exports/cnc/extruder/parts/{part}/{part}{extension}", f"05_P5_COUPONS/{part}/{part}{extension}")
        add_file(items, f"exports/cnc/extruder/parts/{part}/drawing_notes.md", f"05_P5_COUPONS/{part}/drawing_notes.md")

    ggm_dir = ROOT / "exports/final/manufacturing/drive_ggm"
    for path in sorted(ggm_dir.iterdir()):
        if path.is_file() and (path.name.startswith("GGM_") or path.name in {"manifest.csv", "release_report.json"}) and path.suffix in {".step", ".dxf", ".csv", ".json"}:
            items.append((path, "06_P3_GGM/" + path.name))

    bindings = [
        "control/thermal_cutoff_contract.json", "control/thermal_barrier_tape_contract.json", "exports/thermal/thermal_cutoff_topology.json",
        "exports/thermal/manifest.csv", "exports/thermal/channel_schedule.csv",
        "exports/final/electrical/fuse_schedule.csv", "exports/final/electrical/wire_schedule.csv",
        "exports/final/electrical/pin_schedule.csv", "electronics/io_schedule.csv",
        "firmware/arduino_mega/src/generated_profiles.h", "firmware/arduino_mega/src/machine_supervisor.cpp",
        "exports/final/firmware/build_manifest.json",
    ]
    for source in bindings:
        add_file(items, source, "07_SOURCE_BINDINGS/" + source)

    status = {
        "package_state": "PREPARATION_ONLY_NOT_FABRICATION_AUTHORIZATION",
        "head": head, "P0": "PASS", "P1_P12": "NOT_RUN",
        "registry_stage_count": len(registry["stages"]), "source_binding_count": len(bindings),
        "procurement_authorized": False, "motor_energization_authorized": False,
        "heater_energization_authorized": False, "production_authorized": False,
        "production_parts_intentionally_excluded": [
            "EX-SCR-01", "EX-BAR-01", "remaining CUT-01 full stack", "legacy DRV-01 powered fixture"
        ],
    }
    readme = "PPR v0.8 physical validation launch package\n\n" + json.dumps(status, ensure_ascii=False, indent=2) + "\n"
    payload = {archive: sha(path) for path, archive in items}
    status_bytes = (json.dumps(status, ensure_ascii=False, indent=2) + "\n").encode()
    payload["00_READ_FIRST/STATUS.json"] = hashlib.sha256(status_bytes).hexdigest()
    payload["00_READ_FIRST/README.txt"] = hashlib.sha256(readme.encode()).hexdigest()
    manifest = "".join(f"{payload[name]}  {name}\n" for name in sorted(payload))

    DIST.mkdir(exist_ok=True)
    output = DIST / f"PPR-v08-PHYSICAL-VALIDATION-LAUNCH-{head[:8]}.zip"
    def info(name: str) -> zipfile.ZipInfo:
        return zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, name in sorted(items, key=lambda item: item[1]):
            archive.writestr(info(name), path.read_bytes())
        archive.writestr(info("00_READ_FIRST/STATUS.json"), status_bytes)
        archive.writestr(info("00_READ_FIRST/README.txt"), readme.encode())
        archive.writestr(info("MANIFEST.sha256"), manifest.encode())
    print(json.dumps({"path": str(output), "sha256": sha(output), "files": len(payload) + 1,
                      "head": head, "state": status["package_state"]}))


if __name__ == "__main__":
    main()
