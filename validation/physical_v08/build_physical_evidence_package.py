#!/usr/bin/env python3
"""Build a review-only evidence bundle rooted at a validated P12 stage release."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHYS = ROOT / "validation/physical_v08"
P12_VALIDATOR = PHYS / "validate_p12_stage_release.py"
DIST = ROOT / "dist"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repo_file(value: str | Path, base: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else base.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to a repository file")
    return path


def discover_from_json(path: Path, found: set[Path]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    stack = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, str) and item.strip():
            candidate = Path(item)
            resolved = candidate if candidate.is_absolute() else path.parent / candidate
            resolved = resolved.resolve()
            if resolved.is_relative_to(ROOT) and resolved.is_file() and resolved not in found:
                found.add(resolved)
                if resolved.suffix.lower() == ".json":
                    discover_from_json(resolved, found)
                elif resolved.suffix.lower() == ".csv":
                    discover_from_csv(resolved, found)


def discover_from_csv(path: Path, found: set[Path]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for key, value in row.items():
                if not value or not isinstance(value, str):
                    continue
                if not (key.endswith("_path") or key in {"evidence_path", "raw_evidence_path", "drying_record"}):
                    continue
                candidate = Path(value)
                resolved = candidate if candidate.is_absolute() else ROOT / candidate
                resolved = resolved.resolve()
                if resolved.is_relative_to(ROOT) and resolved.is_file() and resolved not in found:
                    found.add(resolved)
                    if resolved.suffix.lower() == ".json":
                        discover_from_json(resolved, found)


def zip_info(name: str) -> zipfile.ZipInfo:
    return zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))


def build(p12_release: Path, output: Path | None = None) -> dict:
    p12_release = repo_file(p12_release, ROOT / "_", "P12 stage release")
    validated = load(P12_VALIDATOR, "ppr_evidence_p12").validate(p12_release)
    if validated.get("status") != "P12_STAGE_RELEASE_VALIDATED":
        raise ValueError("validated P12 stage release required")
    if validated.get("physical_validation_complete_candidate") is not True:
        raise ValueError("P12 completion candidate flag missing")
    if any(validated.get(key) is not False for key in
           ("continuing_power_authority", "production_authorized", "safety_certification")):
        raise ValueError("P12 completion safety semantics drift")

    found = {p12_release}
    discover_from_json(p12_release, found)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = {
        "package_state": "PHYSICAL_VALIDATION_REVIEW_CANDIDATE_ONLY",
        "head": head,
        "p12_stage_release_sha256": sha(p12_release),
        "physical_validation_complete_candidate": True,
        "evidence_package_review_allowed": True,
        "continuing_power_authority": False,
        "production_authorized": False,
        "safety_certification": False,
        "machine_release": "HOLD",
        "evidence_file_count": len(found),
    }
    payload: dict[str, bytes] = {}
    for path in sorted(found):
        rel = path.relative_to(ROOT).as_posix()
        payload["01_EVIDENCE/" + rel] = path.read_bytes()
    payload["00_READ_FIRST/STATUS.json"] = (json.dumps(status, indent=2) + "\n").encode()
    payload["00_READ_FIRST/P12_VALIDATION.json"] = (json.dumps(validated, indent=2) + "\n").encode()
    manifest = "".join(
        f"{hashlib.sha256(payload[name]).hexdigest()}  {name}\n" for name in sorted(payload)
    ).encode()
    payload["MANIFEST.sha256"] = manifest
    if output is None:
        DIST.mkdir(exist_ok=True)
        output = DIST / f"PPR-v08-PHYSICAL-EVIDENCE-{head[:8]}.zip"
    else:
        output = output.resolve()
        if not output.is_relative_to(ROOT):
            raise ValueError("output must remain inside repository")
        output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(payload):
            archive.writestr(zip_info(name), payload[name])
    return {"path": str(output), "sha256": sha(output), "files": len(payload), **status}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("p12_release", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = build(args.p12_release, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
