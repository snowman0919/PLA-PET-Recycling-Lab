#!/usr/bin/env python3
"""Validate source pins, mirrors and numeric bounds; HOLD cannot pass release."""

from __future__ import annotations

import csv
import hashlib
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    module = runpy.run_path(str(ROOT / "calculations/tolerance_stack_final.py"))
    evaluate = module["numeric_status"]
    assert evaluate([.1524, .3576], .15, .35) == "FAIL"
    assert evaluate([-.001, .20], 0, .30) == "FAIL"
    assert evaluate([0, .101], 0, .10) == "FAIL"
    assert evaluate([None, None], 0, .10) == "NOT_EVALUATED"
    assert evaluate([.15, .35], .15, .35) == "PASS"
    assert evaluate([.1338, None], 0, None) == "PASS"
    assert evaluate([float("nan"), .20], 0, .30) == "FAIL"
    final = ROOT / "exports/final/interface_catalog.csv"
    assert final.read_bytes() == (ROOT / "exports/fabrication/interface_catalog.csv").read_bytes(), "divergent authority"
    rows = list(csv.DictReader(final.open(encoding="utf-8")))
    report = json.loads((ROOT / "calculations/tolerance_stack_final.json").read_text())
    expected_rows = module["rows"]()
    assert report["interfaces"] == expected_rows, "stale generated interface data"
    assert len(rows) == len(expected_rows) == len({r["interface_id"] for r in rows})
    for actual, expected in zip(rows, expected_rows):
        assert actual == {k: "" if v is None else str(v) for k, v in expected.items()}, expected["interface_id"]
        assert expected["revision"] == module["REV"] and expected["physical_validation_state"] == "NOT_RUN"
        numerical = evaluate([expected["minimum"], expected["maximum"]], expected["required_minimum"], expected["required_maximum"])
        assert expected["numeric_status"] == numerical, expected["interface_id"]
        assert expected["status"] in {"PASS", "HOLD", "FAIL"}
        if expected["status"] == "PASS":
            assert numerical == "PASS" and not expected["blockers"], expected["interface_id"]
        if expected["status"] == "HOLD":
            assert expected["blockers"], expected["interface_id"]
        for ref in json.loads(expected["source_refs"]):
            text = module["source_text"](ref["path"], ref["commit"])
            assert hashlib.sha256(text.encode()).hexdigest() == ref["sha256"], ref["path"]
            assert text.splitlines()[ref["line"]-1] == ref["excerpt"], ref["path"]
    by_id = {r["interface_id"]: r for r in expected_rows}
    assert by_id["TS-08"]["assembly_method"].startswith("machine specified flat-bottom")
    assert "no generic drill-cone substitution" in by_id["TS-08"]["assembly_method"]
    assert (by_id["TS-03"]["required_minimum"], by_id["TS-03"]["required_maximum"]) == (0, .35)
    assert (by_id["TS-03"]["minimum"], by_id["TS-03"]["maximum"]) == (.100681, .159024)
    assert by_id["TS-03"]["status"] == "PASS" and by_id["TS-03"]["assessment_kind"] == "RELEASED_BREP_AND_LOADED_FEA"
    assert (by_id["TS-04"]["minimum"], by_id["TS-04"]["maximum"]) == (0, .05)
    assert by_id["TS-04"]["status"] == "PASS"
    assert by_id["TS-01"]["assessment_kind"] == "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
    assert (by_id["TS-01"]["minimum"], by_id["TS-01"]["maximum"]) == (.25, .50)
    assert by_id["TS-02"]["assessment_kind"] == "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
    assert (by_id["TS-02"]["minimum"], by_id["TS-02"]["maximum"]) == (.05, .20)
    assert by_id["TS-06"]["assessment_kind"] == "GD_AND_ISO286_WORST_CASE"
    assert (by_id["TS-06"]["minimum"], by_id["TS-06"]["maximum"]) == (0, .024)
    assert by_id["TS-07"]["status"] == "PASS" and by_id["TS-07"]["minimum"] == .277434
    assert by_id["TS-07"]["assessment_kind"] == "FREE_STATE_ID_AND_CLAMP_TRAVEL_WORST_CASE"
    assert by_id["IF-023"]["status"] == "PASS" and by_id["IF-023"]["minimum"] == .277434
    assert by_id["TS-08"]["status"] == "PASS" and by_id["TS-08"]["minimum"] > 3.32
    assert by_id["TS-11"]["assessment_kind"] == "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
    assert by_id["IF-003"]["status"] == "PASS" and by_id["IF-003"]["maximum"] == .20
    assert (by_id["TS-10"]["minimum"], by_id["TS-10"]["maximum"]) == (1.6, 1.9)
    assert by_id["TS-10"]["status"] == "PASS" and "FM-EB-01" in by_id["TS-10"]["part_b"]
    assert by_id["IF-010"]["part_a"] == "FM-GA-01"
    assert all(by_id[i]["status"] == "PASS" for i in ("IF-001", "IF-002", "IF-003", "IF-004", "IF-005", "IF-009", "IF-010", "IF-011", "IF-014", "IF-016", "IF-017", "IF-032"))
    assert (by_id["IF-011"]["minimum"], by_id["IF-011"]["maximum"]) == (0, .096)
    assert "outer-ring overlap≥0.44" in by_id["IF-011"]["criterion"]
    assert (by_id["IF-017"]["minimum"], by_id["IF-017"]["maximum"]) == (0, .030)
    assert "axial clearance0.05–0.22" in by_id["IF-017"]["criterion"]
    assert (by_id["IF-025"]["minimum"], by_id["IF-025"]["maximum"]) == (.17, .28)
    assert by_id["IF-025"]["status"] == "PASS" and by_id["IF-025"]["assessment_kind"] == "MTA1_PROBE_AND_STOP_COLLAR_CONTRACT"
    assert (by_id["IF-026"]["minimum"], by_id["IF-026"]["maximum"]) == (.17, .28)
    assert by_id["IF-026"]["status"] == "PASS" and by_id["IF-026"]["assessment_kind"] == "MTA1_PROBE_AND_STOP_COLLAR_CONTRACT"
    assert (by_id['IF-024']['minimum'],by_id['IF-024']['maximum']) == (.037,.078)
    assert by_id['IF-024']['required_maximum'] == .09 and by_id['IF-024']['status']=='PASS'
    assert (by_id["IF-012"]["minimum"], by_id["IF-012"]["maximum"]) == (.200, .408)
    assert by_id["IF-012"]["status"] == "PASS" and by_id["IF-012"]["assessment_kind"] == "COMPLETE_ASSEMBLY_FUNCTIONAL_ACCEPTANCE"
    assert (by_id["IF-018"]["minimum"], by_id["IF-018"]["maximum"]) == (.200, .411)
    assert by_id["IF-018"]["status"] == "PASS" and by_id["IF-018"]["assessment_kind"] == "DRAWING_OPPOSITE_LIMITS_AND_CLAMP"
    assert (by_id["IF-028"]["minimum"], by_id["IF-028"]["maximum"]) == (.40, .50)
    assert by_id["IF-028"]["status"] == "PASS" and by_id["IF-028"]["assessment_kind"] == "SELECTED_THROUGH_BOLT_CLEARANCE"
    assert (by_id["IF-029"]["minimum"], by_id["IF-029"]["maximum"]) == (.50, .70)
    assert by_id["IF-029"]["status"] == "PASS" and by_id["IF-029"]["assessment_kind"] == "SELECTED_THROUGH_BOLT_CLEARANCE"
    assert (by_id["IF-030"]["minimum"], by_id["IF-030"]["maximum"]) == (30, 30)
    assert by_id["IF-030"]["status"] == "PASS" and by_id["IF-030"]["assessment_kind"] == "INSTANCE_JOINT_CONTRACT_COVERAGE"
    assert (by_id["IF-015"]["minimum"], by_id["IF-015"]["maximum"]) == (.200, .509)
    assert by_id["IF-015"]["status"] == "PASS" and by_id["IF-015"]["assessment_kind"] == "DRAWING_OPPOSITE_LIMITS_AND_PAIR_ALIGNMENT"
    assert (by_id["IF-006"]["minimum"], by_id["IF-006"]["maximum"]) == (0, .10)
    assert by_id["IF-006"]["status"] == "PASS" and by_id["IF-006"]["assessment_kind"] == "MATCH_DRILLED_ASSEMBLY_AND_TIR_ACCEPTANCE"
    assert (by_id["IF-007"]["minimum"], by_id["IF-007"]["maximum"]) == (86.167, 86.167)
    assert by_id["IF-007"]["status"] == "PASS" and "C=86.167" in by_id["IF-007"]["calculation"]
    assert (by_id["IF-008"]["minimum"], by_id["IF-008"]["maximum"]) == (.02, .15)
    assert by_id["IF-008"]["status"] == "PASS" and by_id["IF-008"]["assessment_kind"] == "OFFICIAL_REFERENCE_DRAWING_AND_RECEIPT_LIMIT_CONTRACT"
    assert by_id["TS-15"]["part_a"] == "ExtruderFrontSlidingGuide" and by_id["TS-15"]["maximum"] is None
    assert not any(i.startswith("IF-") and len(i) != 6 for i in by_id), "ad-hoc interface IDs"
    print(f"INTERFACE_CATALOG_INTEGRITY_PASS rows={len(rows)} numerical_negative_tests=7 sources_pinned=True mirror_identical=True")
    if "--self-test" in sys.argv:
        return
    unresolved = [r["interface_id"] for r in expected_rows if r["status"] != "PASS"]
    if unresolved or report["coverage"]["status"] != "PASS" or report["status"] != "PASS":
        raise SystemExit("FABRICATION_INTERFACE_CATALOG_HOLD: " + ", ".join(unresolved) + "; exhaustive mating coverage not demonstrated")
    print(f"FABRICATION_INTERFACE_CATALOG_VALIDATED_OK rows={len(rows)}")


if __name__ == "__main__":
    main()
