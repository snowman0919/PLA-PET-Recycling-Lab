#!/usr/bin/env python3
"""Fail-closed digital prerequisite for starting v0.8 physical validation.

This module never authorizes, energizes, fabricates, or purchases hardware. It
refreshes the existing full-compliance report and distinguishes the 23 technical
engineering gates from the two release-distribution gates (ZIP + remote policy).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "release"))
from source_identity import source_identity
COMPLIANCE = ROOT / "validation/results/v08_full_compliance.json"
VALIDATOR = ROOT / "validation/v08_full_compliance.py"
EXCLUDED_RELEASE_ONLY = {"20_release_package", "21_release_policy"}
BINDINGS = (
    "cad/parameters/final_v08.json",
    "analysis/final_validation/results/v0.8/summary.json",
    "simulation/openmodelica/results_v0.8/summary.json",
    "validation/results/final_v08_cad.json",
    "calculations/tolerance_stack_final.json",
    "exports/final/firmware/build_manifest.json",
    "control/ggm_drive_contract.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_compliance() -> dict[str, object]:
    COMPLIANCE.unlink(missing_ok=True)
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), "--technical-only"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180,
    )
    # v08_full_compliance intentionally returns non-zero while only packaging or
    # remote-release gates are open. The JSON is the authoritative result.
    if proc.returncode not in (0, 1) or not COMPLIANCE.is_file():
        raise RuntimeError("full compliance report was not produced")
    data = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
    if not isinstance(data.get("checks"), dict):
        raise RuntimeError("malformed full compliance report")
    return {"data": data, "validator_rc": proc.returncode, "validator_output": proc.stdout.strip()}


def evaluate(refresh: bool = True) -> dict[str, object]:
    refreshed = refresh_compliance() if refresh else {
        "data": json.loads(COMPLIANCE.read_text(encoding="utf-8")),
        "validator_rc": None,
        "validator_output": "NOT_REFRESHED",
    }
    data = refreshed["data"]
    checks: dict[str, dict[str, object]] = data["checks"]  # type: ignore[assignment]
    unknown_exclusions = EXCLUDED_RELEASE_ONLY - set(checks)
    if unknown_exclusions:
        raise RuntimeError(f"expected release-only gates missing: {sorted(unknown_exclusions)}")
    required = sorted(set(checks) - EXCLUDED_RELEASE_ONLY)
    failed = [name for name in required if checks[name].get("status") != "PASS"]
    binding_hashes: dict[str, str] = {}
    missing_bindings: list[str] = []
    for rel in BINDINGS:
        path = ROOT / rel
        if path.is_file():
            binding_hashes[rel] = sha(path)
        else:
            missing_bindings.append(rel)
    head, branch = source_identity(ROOT)
    passed = not failed and not missing_bindings and len(required) == 23
    return {
        "schema_version": 1,
        "status": "PASS" if passed else "BLOCKED",
        "meaning": "ALL_TECHNICAL_DIGITAL_GATES_PASS" if passed else "TECHNICAL_DIGITAL_GATE_OPEN",
        "physical_action_authorized": False,
        "purchase_authorized": False,
        "fabrication_authorized": False,
        "energization_authorized": False,
        "branch": branch,
        "head": head,
        "compliance_report": str(COMPLIANCE.relative_to(ROOT)),
        "compliance_sha256": sha(COMPLIANCE),
        "required_technical_gate_count": len(required),
        "required_technical_gates": {name: checks[name].get("status") for name in required},
        "failed_technical_gates": failed,
        "excluded_release_only_gates": {name: checks[name].get("status") for name in sorted(EXCLUDED_RELEASE_ONLY)},
        "source_bindings_sha256": binding_hashes,
        "missing_source_bindings": missing_bindings,
        "validator_returncode": refreshed["validator_rc"],
        "validator_tail": "\n".join(str(refreshed["validator_output"]).splitlines()[-6:]),
        "note": "PASS permits planning/record preparation only. Each physical stage still requires explicit user approval and its own prerequisite checks.",
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=ROOT / "validation/physical_v08/simulation_prerequisite.json")
    ap.add_argument("--no-refresh", action="store_true")
    args = ap.parse_args()
    result = evaluate(refresh=not args.no_refresh)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PHYSICAL_V08_DIGITAL_PREREQUISITE_{result['status']} technical={result['required_technical_gate_count']} failed={len(result['failed_technical_gates'])}")
    raise SystemExit(0 if result["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
