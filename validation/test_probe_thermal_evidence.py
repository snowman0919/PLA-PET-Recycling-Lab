#!/usr/bin/env python3
"""프로브 해석의 시간영역 누락/순서 오류와 틀린 온도 궤적을 거부한다."""
import math
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis/final_validation"))
from probe_thermal_screen import trajectory_error
import probe_thermal_screen as probe

samples = [{"time": i/10, "junctionC": 250-225*math.exp(-.1*i/10)} for i in range(1201)]
assert trajectory_error(samples, 250, .1) < 1e-12
invalid = [[], samples[1:], samples[:-1], [samples[-1]]*1201,
           samples[:20]+samples[21:]+[samples[-1]],
           samples[:20]+[samples[21], samples[20]]+samples[22:],
           [dict(samples[0], junctionC=math.nan)]+samples[1:],
           [dict(samples[0], junctionC=26)]+samples[1:]]
for rows in invalid:
    try:
        trajectory_error(rows, 250, .1)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid thermal evidence accepted")
print(f"PROBE_THERMAL_EVIDENCE_PASS negative_cases={len(invalid)}")
for equilibrium, rate, ambient in ((math.nan, .1, 25), (250, math.nan, 25),
                                   (250, math.inf, 25), (250, 0, 25),
                                   (250, -.1, 25), (250, .1, math.nan)):
    try:
        trajectory_error(samples, equilibrium, rate, ambient)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid analytic thermal parameters accepted")
print("PROBE_THERMAL_PARAMETER_REJECTION_PASS cases=6")
for failure in (FileNotFoundError(), subprocess.TimeoutExpired("omc", 180, output=b"partial output")):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        script = root / "analysis/final_validation/probe_thermal_screen.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(probe.__file__, script)
        output = script.parent / "results/v0.8/probe_thermal_screen.json"
        output.parent.mkdir(parents=True)
        output.write_text('{"openmodelica_comparison":{"status":"PASS"}}')
        with patch.object(probe, "__file__", str(script)), patch.object(sys, "argv", [str(script), "omc"]), patch.object(probe.subprocess, "run", side_effect=failure):
            try:
                probe.main()
            except type(failure):
                pass
            else:
                raise AssertionError("Solver failure suppressed")
        result = json.loads(output.read_text())["openmodelica_comparison"]
        assert result["status"] == "FAIL"
        assert type(failure).__name__ in (root / result["raw_directory"] / "solver.log").read_text()
print("PROBE_FAILED_RERUN_REJECTS_STALE_PASS cases=2")
