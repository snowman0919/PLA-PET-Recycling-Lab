#!/usr/bin/env python3
"""조립체 검증 근거: solver benchmark PASS의 잘못된 승격을 차단한다.

입력: frame/torsion 모두 PASS인 benchmark 요약.
방법/합격기준: 요약 경로를 주입해도 조립체 두 gate는 미검증 상태를 유지한다.
실행: python3 validation/test_loaded_phase_evidence.py
"""

import json
import math
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis/final_validation"))
import run_phase_load_v08 as phase
from run_phase_section_sensitivity_v08 import torsion_cases
from run_load_checks import parse_frd, key_demands


def main():
    full, single = key_demands(34, 18), key_demands(34, 6)
    assert math.isclose(full["average_shear_mpa"], 31.48148148148148)
    assert math.isclose(single["average_hub_bearing_mpa"], 236.11111111111111)
    assert math.isclose(single["average_shear_mpa"], 3*full["average_shear_mpa"])
    for torque, length in ((-1,18), (22,0), (math.inf,18), (22,math.nan)):
        try:
            key_demands(torque,length)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid key load/length accepted")
    print("KEY_LOAD_SHARING_SCREEN_CHECK_PASS")
    structural = json.loads((phase.ROOT / "analysis/structural/results/structural_screening.json").read_text())
    key = next(row for row in structural["checks"] if row["component"] == "PH-KEY-01 phase gear key")
    assert key["shear_screen_status"] == "PASS" and key["status"] == "HOLD"
    assert structural["status"] != "PASS"
    assert structural["virtual_physics_state"] == "STRUCTURAL_SCREENING_INCOMPLETE"
    assert [row["engaged_length_mm"] for row in key["load_sharing_scenarios"]] == [18, 6, 4, 2]
    print("KEY_INCOMPLETE_QUALIFICATION_RELEASE_REJECTION_PASS")
    with tempfile.TemporaryDirectory() as folder:
        benchmark = Path(folder) / "qualification_summary.json"
        benchmark.write_text(json.dumps({"status": "PASS", "combined_worst_angle_deg": 0,
                                         "criterion_deg": 1, "source_sha256": {}}))
        with patch.object(phase, "QUALIFICATION", benchmark):
            checks = phase.load_loaded_phase_qualification()
        assert checks["frame_and_bearing_compliance_qualified"] is False
        assert checks["torsional_phase_compliance_qualified"] is False
    print("LOADED_PHASE_EVIDENCE_REGRESSION_PASS")
    # The central slave disc has two equally close neighbours: neither may vanish.
    stations = {"105": {"cutter_y_mm": [10, 30], "gear_y_mm": 100},
                "153": {"cutter_y_mm": [20, 40], "gear_y_mm": 100}}
    cases = torsion_cases(stations, 22, 20)
    assert len(cases) == 3
    assert {(c["jammed_slave_cutter_y_mm"], c["adjacent_driven_cutter_y_mm"]) for c in cases} == {(10, 20), (30, 20), (30, 40)}
    half = torsion_cases(stations, 11, 20)
    assert all(a["unkeyed_round_shaft_relative_twist_deg"] == 2*b["unkeyed_round_shaft_relative_twist_deg"] for a,b in zip(cases, half))
    print("TORSION_ADJACENT_INTERFACE_REGRESSION_PASS")
    with tempfile.TemporaryDirectory() as folder:
        frd = Path(folder) / "known.frd"
        frd.write_text(" -4 STRESS\n -1 7 1.0E8 0 0 0 0 0\n -1 42 0 0 0 6.0E7 0 0\n -3\n -4 DISP\n -1 7 0.001 0 0\n -3\n")
        parsed = parse_frd(frd)
        assert parsed["max_von_mises_node_id"] == 42
        assert math.isclose(parsed["max_von_mises_mpa"], math.sqrt(3)*60)
        assert parsed["max_displacement_mm"] == 1
    print("FRD_PEAK_STRESS_LOCATION_REGRESSION_PASS")
    with tempfile.TemporaryDirectory() as folder:
        frd = Path(folder) / "invalid.frd"
        valid = " -4 STRESS\n -1 7 0 0 0 0 0 0\n -3\n -4 DISP\n -1 7 0 0 0\n -3\n"
        frd.write_text(valid)
        assert parse_frd(frd)["max_von_mises_mpa"] == 0
        for text in ("", valid.split(" -4 DISP")[0], valid.replace(" -1 7 0 0 0\n", " -1 7 0 0\n"), valid.replace(" -1 7 0 0 0\n", " -1 7 1E999 0 0\n"), valid.rsplit(" -3", 1)[0]):
            frd.write_text(text)
            try:
                parse_frd(frd)
            except ValueError:
                pass
            else:
                raise AssertionError("incomplete/nonfinite FRD accepted")
    print("FRD_MISSING_INVALID_DATA_REGRESSION_PASS cases=5")


if __name__ == "__main__":
    main()
