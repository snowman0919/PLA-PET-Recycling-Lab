#!/usr/bin/env python3
"""Fabrication ZIP을 새 디렉터리에 추출하고 schema·경로·해시를 검증한다."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
NAME = "PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION"
ZIP = ROOT / "dist" / f"{NAME}.zip"
SECTIONS = {"00_START_HERE", "01_3D_PRINT", "02_CNC_AND_METAL", "03_FRAME", "04_BOM", "05_ELECTRICAL", "06_FIRMWARE", "07_ASSEMBLY_MANUAL", "08_COMMISSIONING", "09_VALIDATION", "10_DESIGN_SOURCE", "LICENSES"}
FORBIDDEN = (".env", ".FCBak", "__pycache__", "/archive/", ".git/")
SOURCE_PATHS = ("cad", "analysis/final_validation/run_calculix_v08.py", "simulation/openmodelica/v0.8",
                "firmware/arduino_mega", "electronics", "release", "validation/run_v08_solver_validation.py",
                "validation/v08_release_inventory.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert ZIP.is_file() and ZIP.stat().st_size > 1000
    with tempfile.TemporaryDirectory(prefix="ppr-v08-release-") as td, zipfile.ZipFile(ZIP) as zf:
        names = zf.namelist(); assert len(names) == len(set(names))
        for name in names:
            p = PurePosixPath(name)
            assert not p.is_absolute() and ".." not in p.parts and not any(token in name for token in FORBIDDEN), name
        zf.extractall(td); base = Path(td)
        assert {PurePosixPath(n).parts[0] for n in names} == SECTIONS
        manifest = json.loads((base / "00_START_HERE/release_manifest.json").read_text())
        schema = json.loads((ROOT / "release/release_manifest.schema.json").read_text())
        assert all(key in manifest for key in schema["required"])
        for key, rule in schema["properties"].items():
            if "const" in rule:
                assert manifest[key] == rule["const"], f"schema const: {key}"
        assert set(manifest) == set(schema["properties"]), "manifest has missing or unknown fields"
        assert re.fullmatch(r"[0-9a-f]{40}", manifest["source_commit"])
        expected_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", *SOURCE_PATHS], cwd=ROOT, text=True
        ).strip()
        assert manifest["source_commit"] == expected_commit, "package was built from stale design source"
        assert manifest["release"] == NAME and manifest["revision"].endswith("v0.8")
        assert manifest["release_state"] == "FABRICATION_CANDIDATE" and manifest["physical_validation_state"] == "NOT_RUN"
        assert manifest["safety_certification_state"] == "NOT_CERTIFIED"
        listed = {f["path"]: f for f in manifest["files"]}
        assert len(listed) == len(manifest["files"]), "duplicate manifest paths"
        expected = set(names) - {"00_START_HERE/README.txt", "00_START_HERE/release_manifest.json", "00_START_HERE/SHA256SUMS"}
        assert set(listed) == expected
        for rel, item in listed.items():
            assert set(item) == {"path", "source", "size", "sha256"}
            assert item["path"] == rel and isinstance(item["source"], str) and item["source"]
            assert isinstance(item["size"], int) and item["size"] > 0
            assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
            source = PurePosixPath(item["source"])
            assert not source.is_absolute() and ".." not in source.parts
            path = base / rel; assert path.stat().st_size == item["size"] and digest(path) == item["sha256"]
        sums = {}
        for line in (base / "00_START_HERE/SHA256SUMS").read_text().splitlines():
            value, rel = line.split("  ", 1); sums[rel] = value
        assert set(sums) == expected | {"00_START_HERE/release_manifest.json"}
        assert all(digest(base / rel) == value for rel, value in sums.items())
    print(f"V08_FABRICATION_VERIFY_PASS files={len(listed)} zip_sha256={digest(ZIP)}")


if __name__ == "__main__":
    main()
