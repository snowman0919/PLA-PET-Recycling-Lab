#!/usr/bin/env python3
"""활성 v0.8 파일만 deterministic fabrication ZIP으로 묶는다."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION"
OUT = ROOT / "dist" / f"{NAME}.zip"
REV = "final-design-fabrication-closure-v0.8"
FORBIDDEN = (".env", ".FCBak", "__pycache__", "/archive/", ".tmp", ".bak", ".pem", ".key", ".p12", "credential", "secret", "token", "analysis/final_validation/results/v0.8/raw", "simulation/openmodelica/results_v0.8/raw")
SOURCE_PATHS = (
    "bom/bom.csv", "cad/parameters/final_v08.json", "cad/freecad/final_v08", "cad/freecad/compact",
    "cad/generation/draw_v08.py", "cad/generation/generate_interface_catalog.py",
    "cad/generation/generate_manufacturing.py", "cad/generation/render_v08.py",
    "cad/generation/render_v08_closeups.py", "calculations/tolerance_stack_final.py",
    "analysis/process_feed/feed_parameters.json", "analysis/process_feed/run_feed_surrogate.py",
    "analysis/final_validation/run_calculix_v08.py", "analysis/final_validation/run_qualification_v08.py",
    "simulation/openmodelica/v0.8", "firmware/arduino_mega", "electronics/controller_wiring_v0.6.md",
    "electronics/io_schedule.csv", "electronics/safety_power_topology.md", "electronics/shredder_drive_wiring.md", "release",
    "validation/run_v08_solver_validation.py", "validation/solid_topology.py",
    "validation/assembly_collision_audit.py", "validation/v08_release_inventory.py",
    "validation/v08_full_compliance.py",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zi(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
    return info


def validate_inputs() -> None:
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", *SOURCE_PATHS], cwd=ROOT, text=True)
    assert not dirty, f"uncommitted release source:\n{dirty}"
    active = json.loads((ROOT / "release/active_part_set.json").read_text())
    active_parts = {p["part_id"]: p["quantity"] for p in active["parts"]}
    assert active["revision"] == REV and len(active_parts) == len(active["parts"])
    assert all(isinstance(quantity, int) and quantity > 0 for quantity in active_parts.values())
    print_rows = list(csv.DictReader((ROOT / "exports/final/print/print_manifest.csv").open()))
    step_rows = list(csv.DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
    draw_rows = list(csv.DictReader((ROOT / "docs/drawings/drawing_register.csv").open()))
    rfq_rows = list(csv.DictReader((ROOT / "exports/final/manufacturing/RFQ/manifest.csv").open()))
    expected_parts = {r["part_id"]: int(r["quantity"]) for r in print_rows + rfq_rows}
    expected_parts.update({f"PPR-{name}-ASM": 1 for name in ("FULL", "SHREDDER", "FEEDER", "EXTRUDER", "FORMING", "FRAME")})
    assert active_parts == expected_parts, "active part set differs from print/RFQ/assembly manifests"
    assert len(print_rows) == 12 and all(r["revision"] == REV and r["slicer_status"] == "PASS" and r["status"] == "PASS" and int(r["quantity"]) > 0 for r in print_rows)
    assert len(step_rows) >= 20 and all(r["revision"] == REV and r["status"] == "PASS" for r in step_rows)
    assert len(draw_rows) == 20 and all(r["revision"] == "v0.8" and r["status"] == "PASS" for r in draw_rows)
    build = json.loads((ROOT / "exports/final/firmware/build_manifest.json").read_text())
    binary = ROOT / "exports/final/firmware/binaries/filament_recycler_atmega2560.hex"
    assert build["status"] == "PASS" and sha(binary.read_bytes()) == build["binary_sha256"]
    assert json.loads((ROOT / "validation/results/v08_release_inventory.json").read_text())["status"] == "PASS"
    compliance = json.loads((ROOT / "validation/results/v08_full_compliance.json").read_text())
    assert all(value["status"] == "PASS" for key, value in compliance["checks"].items() if key != "20_release_package")


def collect() -> dict[str, tuple[Path, str]]:
    layout = json.loads((ROOT / "release/package_layout.json").read_text())
    found: dict[str, tuple[Path, str]] = {}
    for section, patterns in layout["sections"].items():
        for pattern in patterns:
            matches = sorted(p for p in ROOT.glob(pattern) if p.is_file())
            assert matches, f"missing source pattern: {pattern}"
            for src in matches:
                rel = src.relative_to(ROOT).as_posix()
                assert not any(token in rel for token in FORBIDDEN), f"forbidden: {rel}"
                dest = f"{section}/{rel}"
                assert dest not in found, f"orphan/duplicate mapping: {dest}"
                found[dest] = (src, rel)
    return found


def main() -> None:
    validate_inputs(); files = collect()
    commit = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", *SOURCE_PATHS],
        cwd=ROOT, text=True,
    ).strip()
    payload = []
    for path, (src, source) in sorted(files.items()):
        data = src.read_bytes(); payload.append({"path": path, "source": source, "size": len(data), "sha256": sha(data)})
    manifest = {
        "release": NAME, "revision": REV, "release_state": "FABRICATION_CANDIDATE", "source_commit": commit,
        "physical_validation_state": "NOT_RUN", "safety_certification_state": "NOT_CERTIFIED",
        "procurement_gate": "USER_APPROVAL_REQUIRED", "commissioning_gate": "USER_APPROVAL_REQUIRED",
        "fabrication_release_approval": "USER_APPROVAL_REQUIRED", "files": payload,
    }
    manifest_data = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    sums = [(item["sha256"], item["path"]) for item in payload] + [(sha(manifest_data), "00_START_HERE/release_manifest.json")]
    sums_data = "".join(f"{digest}  {path}\n" for digest, path in sorted(sums, key=lambda x: x[1])).encode()
    readme = ("PLA/PET Recycling Lab v1.0.0-rc1 FABRICATION CANDIDATE\n"
              "Digital design evidence only. Physical validation NOT_RUN; safety NOT_CERTIFIED.\n"
              "Do not purchase, fabricate, energize, or commission without explicit user approval and exact donor verification.\n").encode()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compresslevel=9) as zf:
        for path, (src, _) in sorted(files.items()): zf.writestr(zi(path), src.read_bytes())
        zf.writestr(zi("00_START_HERE/README.txt"), readme)
        zf.writestr(zi("00_START_HERE/release_manifest.json"), manifest_data)
        zf.writestr(zi("00_START_HERE/SHA256SUMS"), sums_data)
    print(f"V08_FABRICATION_PACKAGE_OK files={len(payload)} sha256={sha(OUT.read_bytes())}")


if __name__ == "__main__":
    main()
