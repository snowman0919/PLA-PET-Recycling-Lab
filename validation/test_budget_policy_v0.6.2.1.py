#!/usr/bin/env python3
"""Price mutations must never become a v0.6.2.1 technical failure."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bom"))
from build_budget_views import price_policy  # noqa: E402


def main() -> None:
    cases = [0, 199999, 200000, 200001, 500000]
    results = []
    for amount in cases:
        policy = price_policy(amount)
        passed = (
            policy["price_status"] == "INFORMATIONAL"
            and policy["price_release_blocking"] is False
            and policy["technical_release_blocked"] is False
            and policy["procurement_approval_gate"] == "USER_APPROVAL_REQUIRED"
        )
        results.append({"absolute_total_krw": amount, "technical_gate_pass": passed})
    payload = {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "mutation": "budget_above_200000_treated_as_technical_failure",
        "status": "PASS" if all(row["technical_gate_pass"] for row in results) else "FAIL",
        "cases": results,
    }
    out = ROOT / "validation" / "results" / "budget_policy_v0.6.2.1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    if payload["status"] != "PASS":
        raise SystemExit(1)
    print("V0621_PRICE_INFORMATIONAL_MUTATION_PASS")


if __name__ == "__main__":
    main()
