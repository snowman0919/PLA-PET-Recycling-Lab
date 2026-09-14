#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

BANNED = ("EX-SCR-01", "EX-BAR-01", "gate1_powered_assembly", "DRV-01", "DRV-Axx", "DRV-F01")
FIXED_REQUIRED = {
    "00_READ_FIRST/STATUS.json", "00_EXECUTION/PHYSICAL_EXECUTION_INDEX_KO.md",
    "00_EXECUTION/physical_gate_contract.json", "00_EXECUTION/physical_execution_registry.json",
    "00_EXECUTION/mvp_smoke_contract.json", "00_EXECUTION/MVP_SMOKE_VALIDATION_KO.md",
    "02_ANALYZERS/validate_mvp_smoke_contract.py", "02_ANALYZERS/validate_thermal_barrier_tape_contract.py",
    "02_ANALYZERS/analyze_s4_thermal_barrier_tape.py", "01_TEMPLATES/s4_thermal_barrier_tape_smoke.csv",
    "03_P4_GATE1/gate1_assembly.step", "04_P4_CNC/CUT-01/CUT-01.step",
    "05_P5_COUPONS/EX-CPN-SCR/EX-CPN-SCR.step", "05_P5_COUPONS/EX-CPN-BAR/EX-CPN-BAR.step",
    "06_P3_GGM/manifest.csv", "MANIFEST.sha256",
}
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_physical_launch_package import SOURCE_BINDINGS


def require_registry_payload(archive: zipfile.ZipFile, names: set[str]) -> None:
    registry = json.loads(archive.read("00_EXECUTION/physical_execution_registry.json"))
    stages = registry.get("stages", [])
    if [stage.get("id") for stage in stages] != [f"P{i}" for i in range(13)]:
        raise SystemExit("registry must contain ordered P0-P12 stages")
    for stage in stages:
        stage_id = stage["id"]
        doc = stage.get("doc")
        if doc and f"00_EXECUTION/{doc}" not in names:
            raise SystemExit(f"missing {stage_id} doc {doc}")
        for template in stage.get("templates", []):
            archive_name = "01_TEMPLATES/" + Path(template).name
            if archive_name not in names:
                raise SystemExit(f"missing {stage_id} template {archive_name}")
        for entry in stage.get("external_templates", []):
            archive_name = "01_TEMPLATES/" + Path(entry.get("archive_name", "")).name
            if archive_name not in names:
                raise SystemExit(f"missing {stage_id} external template {archive_name}")
        for key, value in stage.items():
            if isinstance(value, str) and value.endswith(".py"):
                archive_name = "02_ANALYZERS/" + Path(value).name
                if archive_name not in names:
                    raise SystemExit(f"missing {stage_id} tool {key}={archive_name}")
    smoke = registry.get("smoke_contract", {})
    if smoke.get("checkpoints") != [f"S{i}" for i in range(6)]:
        raise SystemExit("smoke checkpoint registry drift")
    if "00_EXECUTION/" + Path(smoke.get("contract", "")).name not in names or "00_EXECUTION/" + Path(smoke.get("doc", "")).name not in names:
        raise SystemExit("missing MVP smoke contract/doc")
    for key in ("validator", "tape_validator"):
        archive_name = "02_ANALYZERS/" + Path(smoke.get(key, "")).name
        if archive_name not in names:
            raise SystemExit("missing smoke validator " + archive_name)


def validate_source_binding_payload(archive, names, status, root):
    expected = {'07_SOURCE_BINDINGS/' + source for source in SOURCE_BINDINGS}
    actual = {name for name in names if name.startswith('07_SOURCE_BINDINGS/')}
    if len(SOURCE_BINDINGS) != len(set(SOURCE_BINDINGS)) or actual != expected:
        raise SystemExit('source binding path coverage drift')
    count = status.get('source_binding_count')
    if type(count) is not int or count != len(SOURCE_BINDINGS):
        raise SystemExit('source binding count drift')
    for source in SOURCE_BINDINGS:
        local = root / source
        content = archive.read('07_SOURCE_BINDINGS/' + source)
        if not local.is_file() or hashlib.sha256(local.read_bytes()).digest() != hashlib.sha256(content).digest():
            raise SystemExit('source binding content drift: ' + source)


def validate_package(path: Path) -> dict:
    root = Path(__file__).resolve().parents[2]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    with zipfile.ZipFile(path) as archive:
        listed = archive.namelist(); names = set(listed)
        duplicates = [name for name in names if listed.count(name) > 1]
        if duplicates:
            raise SystemExit("duplicate zip paths")
        if any(any(token in name for token in BANNED) for name in names):
            raise SystemExit("banned production/legacy path present")
        missing = sorted(FIXED_REQUIRED - names)
        if missing:
            raise SystemExit("missing required paths: " + ", ".join(missing))
        require_registry_payload(archive, names)

        status = json.loads(archive.read("00_READ_FIRST/STATUS.json"))
        if status.get("package_state") != "PREPARATION_ONLY_NOT_FABRICATION_AUTHORIZATION":
            raise SystemExit("wrong package state")
        if status.get("head") != head:
            raise SystemExit("package HEAD is stale")
        validate_source_binding_payload(archive, names, status, root)
        if status.get("registry_stage_count") != 13:
            raise SystemExit("package coverage metadata drift")
        for key in ("procurement_authorized", "motor_energization_authorized", "heater_energization_authorized", "production_authorized"):
            if status.get(key) is not False:
                raise SystemExit(key + " must be false")

        manifest = {}
        for line in archive.read("MANIFEST.sha256").decode().splitlines():
            digest, name = line.split("  ", 1); manifest[name] = digest
        for name, digest in manifest.items():
            if name not in names:
                raise SystemExit("manifest path missing " + name)
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise SystemExit("hash mismatch " + name)
        if set(manifest) != names - {"MANIFEST.sha256"}:
            raise SystemExit("manifest coverage mismatch")
    return {"files": len(listed), "head": head, "stages": 13,
            "source_bindings": len(SOURCE_BINDINGS), "state": "PREPARATION_ONLY"}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("zip", type=Path); args = ap.parse_args()
    result = validate_package(args.zip)
    print(f"PHYSICAL_LAUNCH_PACKAGE_PASS files={result['files']} head={result['head'][:12]} "
          f"stages={result['stages']} bindings={result['source_bindings']} state={result['state']}")


if __name__ == "__main__":
    main()
