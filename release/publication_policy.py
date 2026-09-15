"""Publishing a design prerelease never authorizes physical operation."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def validate_policy(policy: dict) -> None:
    expected = {
        "schema_version": 1, "revision": "final-design-fabrication-closure-v0.8",
        "tag": "v1.0.0-rc1", "target_branch": "final-design-fabrication-closure-v0.8",
        "repository": "snowman0919/PLA-PET-Recycling-Lab",
        "publication_authorized": True, "publication_kind": "PRERELEASE",
        "release_state": "FABRICATION_CANDIDATE", "mvp_is_final_product": True,
        "physical_validation_state": "NOT_RUN", "safety_certification_state": "NOT_CERTIFIED",
        "procurement_authorized": False, "fabrication_authorized": False,
        "energization_authorized": False, "production_authorized": False, "merge_authorized": False,
    }
    for key, value in expected.items():
        if type(policy.get(key)) is not type(value) or policy[key] != value:
            raise ValueError("publication policy mismatch: " + key)
    if not policy.get("authorization_date") or not policy.get("authorization_basis"):
        raise ValueError("missing publication authorization provenance")

def publication_policy_current(root: Path = ROOT) -> bool:
    try:
        validate_policy(json.loads((root/"release/publication_policy.json").read_text()))
        return True
    except (OSError, ValueError, TypeError):
        return False
