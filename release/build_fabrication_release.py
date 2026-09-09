#!/usr/bin/env python3
"""활성 v0.8 파일만 deterministic fabrication ZIP으로 묶는다."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from firmware_evidence import firmware_evidence_current

ROOT = Path(__file__).resolve().parents[1]
NAME = "PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION"
OUT = ROOT / "dist" / f"{NAME}.zip"
REV = "final-design-fabrication-closure-v0.8"
FORBIDDEN = (".env", ".FCBak", "__pycache__", "/archive/", ".git/", ".tmp", ".bak", ".pem", ".key", ".p12", "credential", "secret", "token", "analysis/final_validation/results/v0.8/raw", "simulation/openmodelica/results_v0.8/raw")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zi(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_STORED; info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


def validate_gate_reports(inventory: dict, compliance: dict) -> None:
    inventory_required = set("baseline_and_archive solver_evidence final_step print_package hot_zone_manufacturing hot_zone_bom firmware_binary drawing_register electrical_final_package final_manual_set commissioning_set multimodal_review".split())
    compliance_required = set("00_authoritative_baseline 02_v07_archive 03_calculix_core 03_hot_zone_mount 03_lc04_resolution 03_solver_qualification 05_loaded_phase_centre 05_v08_motion_dynamics 06_interface_catalog 06_tolerance_stacks 07_freecad_source 08_step_package 09_print_package 10_manufacturing_package 11_dimensioned_drawings 12_electrical_package 13_firmware_release 14_authoritative_bom 15_assembly_manual 16_commissioning_handoff 17_multimodal_review 18_electrical_firmware_tests 19_independent_reviews 21_release_policy".split())
    assert inventory.get("revision") == compliance.get("revision") == REV, "gate revision mismatch"
    inv = inventory.get("checks", {})
    comp = compliance.get("checks", {})
    sections = compliance.get("section_coverage", {})
    assert set(inv) == inventory_required | {"release_package"}, "missing/unknown inventory gate"
    assert set(comp) == compliance_required | {"20_release_package"}, "missing/unknown compliance gate"
    assert set(sections) == {f"{number:02d}" for number in range(26)}, "missing/unknown goal section"
    assert all(row.get("covered") is True for row in sections.values()), "goal section not covered"
    assert all(sections[name].get("status") == "PASS" for name in ("01", "04")), "scope/architecture gate unresolved"
    assert all(inv[key] is True for key in inventory_required), "inventory gate unresolved"
    assert all(comp[key].get("status") == "PASS" for key in compliance_required), "compliance gate unresolved"


def validate_payload_git_state(files: dict[str, tuple[Path, str]]) -> None:
    sources = sorted({source for _, source in files.values()})
    tracked = set(subprocess.check_output(["git", "ls-files", "--cached", "--", *sources], cwd=ROOT, text=True).splitlines())
    assert tracked == set(sources), f"untracked/ignored release payload: {sorted(set(sources)-tracked)[:20]}"
    assert subprocess.run(["git", "diff", "--quiet", "--", *sources], cwd=ROOT).returncode == 0, "modified release payload"
    assert subprocess.run(["git", "diff", "--cached", "--quiet", "--", *sources], cwd=ROOT).returncode == 0, "staged release payload"


def validate_inputs(files: dict[str, tuple[Path, str]]) -> None:
    validate_payload_git_state(files)
    active = json.loads((ROOT / "release/active_part_set.json").read_text())
    active_parts = {p["part_id"]: p["quantity"] for p in active["parts"]}
    assert active["revision"] == REV and len(active_parts) == len(active["parts"])
    assert all(isinstance(quantity, int) and quantity > 0 for quantity in active_parts.values())
    print_rows = list(csv.DictReader((ROOT / "exports/final/print/print_manifest.csv").open()))
    step_rows = list(csv.DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
    draw_rows = list(csv.DictReader((ROOT / "docs/drawings/drawing_register.csv").open()))
    rfq_rows = list(csv.DictReader((ROOT / "exports/final/manufacturing/RFQ/manifest.csv").open(encoding="utf-8")))
    ggm_rows = list(csv.DictReader((ROOT / "exports/final/manufacturing/drive_ggm/manifest.csv").open(encoding="utf-8")))
    expected_parts = {}
    for r in print_rows + rfq_rows + ggm_rows:
        pid,qty=r["part_id"],int(r["quantity"])
        if pid in expected_parts and expected_parts[pid] != qty: raise AssertionError(f"active quantity conflict: {pid}")
        expected_parts[pid]=qty
    expected_parts.update({f"PPR-{name}-ASM": 1 for name in ("FULL", "SHREDDER", "FEEDER", "EXTRUDER", "FORMING", "FRAME")})
    assert active_parts == expected_parts, "active part set differs from print/RFQ/assembly manifests"
    assert len(print_rows) == 12 and all(r["revision"] == REV and r["slicer_status"] == "PASS" and r["status"] == "PASS" and int(r["quantity"]) > 0 for r in print_rows)
    assert len(step_rows) >= 20 and all(r["revision"] == REV and r["status"] == "PASS" for r in step_rows)
    assert len(draw_rows) == 20 and all(r["revision"] == "v0.8" and r["status"] == "PASS" for r in draw_rows)
    assert firmware_evidence_current(ROOT), "firmware source/binary evidence stale"
    inventory = json.loads((ROOT / "validation/results/v08_release_inventory.json").read_text())
    compliance = json.loads((ROOT / "validation/results/v08_full_compliance.json").read_text())
    validate_gate_reports(inventory, compliance)


def collect() -> dict[str, tuple[Path, str]]:
    layout = json.loads((ROOT / "release/package_layout.json").read_text())
    found: dict[str, tuple[Path, str]] = {}
    for section, patterns in layout["sections"].items():
        for pattern in patterns:
            matches = sorted(p for p in ROOT.glob(pattern) if p.is_file())
            assert matches, f"missing source pattern: {pattern}"
            for src in matches:
                rel = src.relative_to(ROOT).as_posix()
                assert src.resolve() == ROOT.resolve() / rel, f"symlinked package source: {rel}"
                assert not any(token in rel for token in FORBIDDEN), f"forbidden: {rel}"
                dest = f"{section}/{rel}"
                assert dest not in found, f"orphan/duplicate mapping: {dest}"
                found[dest] = (src, rel)
    return found


def main() -> None:
    files = collect(); validate_inputs(files)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
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
              "Replay instructions: 00_START_HERE/docs/final/package_replay_ko.md; run analysis from 10_DESIGN_SOURCE.\n"
              "Do not purchase, fabricate, energize, or commission without explicit user approval and exact donor verification.\n").encode()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w") as zf:
        for path, (src, _) in sorted(files.items()): zf.writestr(zi(path), src.read_bytes())
        zf.writestr(zi("00_START_HERE/README.txt"), readme)
        zf.writestr(zi("00_START_HERE/release_manifest.json"), manifest_data)
        zf.writestr(zi("00_START_HERE/SHA256SUMS"), sums_data)
    print(f"V08_FABRICATION_PACKAGE_OK files={len(payload)} sha256={sha(OUT.read_bytes())}")


if __name__ == "__main__":
    main()
