#!/usr/bin/env python3
"""Validate a P12-rooted physical evidence review bundle without granting authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

REQUIRED = {
    "00_READ_FIRST/STATUS.json",
    "00_READ_FIRST/P12_VALIDATION.json",
    "MANIFEST.sha256",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        listed = archive.namelist()
        names = set(listed)
        if len(listed) != len(names):
            raise ValueError("duplicate zip paths")
        missing = REQUIRED - names
        if missing:
            raise ValueError("missing required paths: " + ", ".join(sorted(missing)))

        manifest = {}
        for line in archive.read("MANIFEST.sha256").decode().splitlines():
            digest, name = line.split("  ", 1)
            manifest[name] = digest
        if set(manifest) != names - {"MANIFEST.sha256"}:
            raise ValueError("manifest coverage mismatch")
        for name, digest in manifest.items():
            if sha_bytes(archive.read(name)) != digest:
                raise ValueError("hash mismatch: " + name)

        status = json.loads(archive.read("00_READ_FIRST/STATUS.json"))
        if status.get("package_state") != "PHYSICAL_VALIDATION_REVIEW_CANDIDATE_ONLY":
            raise ValueError("wrong evidence package state")
        if status.get("physical_validation_complete_candidate") is not True:
            raise ValueError("completion-candidate flag missing")
        if status.get("evidence_package_review_allowed") is not True:
            raise ValueError("evidence review flag missing")
        for key in ("continuing_power_authority", "production_authorized", "safety_certification"):
            if status.get(key) is not False:
                raise ValueError(key + " must remain false")
        if status.get("machine_release") != "HOLD":
            raise ValueError("machine release must remain HOLD")

        p12 = json.loads(archive.read("00_READ_FIRST/P12_VALIDATION.json"))
        if p12.get("status") != "P12_STAGE_RELEASE_VALIDATED":
            raise ValueError("P12 validation snapshot is not validated")
        if p12.get("physical_validation_complete_candidate") is not True:
            raise ValueError("P12 completion flag missing")
        for key in ("continuing_power_authority", "production_authorized", "safety_certification"):
            if p12.get(key) is not False:
                raise ValueError("P12 validation authority drift: " + key)
        if p12.get("machine_release") != "HOLD":
            raise ValueError("P12 validation machine release drift")

        root_digest = status.get("p12_stage_release_sha256", "")
        evidence_names = [name for name in names if name.startswith("01_EVIDENCE/")]
        matching = [name for name in evidence_names if sha_bytes(archive.read(name)) == root_digest]
        if len(matching) != 1 or not matching[0].endswith("p12_stage_release.json"):
            raise ValueError("root P12 stage-release binding missing or ambiguous")
        if status.get("evidence_file_count") != len(evidence_names):
            raise ValueError("evidence file count drift")

    return {"status": "PHYSICAL_EVIDENCE_PACKAGE_PASS", "files": len(listed),
            "evidence_files": len(evidence_names), "head": status.get("head"),
            "machine_release": "HOLD"}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("zip", type=Path); args = ap.parse_args()
    try:
        result = validate(args.zip); code = 0
    except (ValueError, KeyError, FileNotFoundError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        result = {"status": "PHYSICAL_EVIDENCE_PACKAGE_REJECTED", "machine_release": "HOLD",
                  "reason": str(exc)}; code = 2
    print(json.dumps(result, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
