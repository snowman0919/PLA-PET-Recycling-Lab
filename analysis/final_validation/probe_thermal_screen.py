#!/usr/bin/env python3
"""프로브 접촉/스템 열손실의 정상상태 민감도. 제품 물성/정확도 인증 아님."""
import hashlib
import json
import math
import csv
import subprocess
import sys
import tempfile
from pathlib import Path


def trajectory_error(samples, equilibrium, rate, ambient=25.):
    if not all(math.isfinite(v) for v in (equilibrium, rate, ambient)) or rate <= 0:
        raise ValueError("Finite temperatures and positive finite thermal rate required")
    times = [float(row["time"]) for row in samples]
    values = [float(row["junctionC"]) for row in samples]
    if (not times or not all(math.isfinite(v) for v in times + values)
            or times[0] != 0 or times[-1] != 120
            or len(set(times)) < 1201
            or any(b < a or b-a > .100001 for a, b in zip(times, times[1:]))):
        raise ValueError("Incomplete or invalid 0..120 s trajectory")
    error = max(abs(value - (equilibrium + (ambient-equilibrium)*math.exp(-rate*time)))
                for time, value in zip(times, values))
    if error >= 1e-4:
        raise ValueError("Trajectory disagrees with analytic solution")
    return error


def main():
    # Gc(Twall-Tj) = Gs(Tj-Tambient); ratio = Gc/Gs.
    wall, ambient = 270., 25.
    rows = []
    for allowed_bias in (1., 2., 5., 10.):
        ratio = (wall - ambient) / allowed_bias - 1
        junction = (ratio * wall + ambient) / (ratio + 1)
        assert math.isclose(wall - junction, allowed_bias, abs_tol=1e-12)
        assert math.isclose(ratio * (wall - junction), junction - ambient, abs_tol=1e-10)
        rows.append({"illustrative_bias_budget_c": allowed_bias, "minimum_contact_to_stem_conductance_ratio": ratio})
    root = Path(__file__).resolve().parents[2]
    output = root / "analysis/final_validation/results/v0.8/probe_thermal_screen.json"
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN",
              "model": "Single isothermal junction; constant positive conductances to wall and ambient; steady state, no radiation or transient model.",
              "wall_c": wall, "ambient_c": ambient, "scenarios": rows,
              "scope": "Illustrative budgets, not allocated system requirements. Gc, Gs, junction position and heat capacity are unknown; no product accuracy or response-time PASS.",
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if len(sys.argv) == 2:
        omc = sys.argv[1]
        model = root / "analysis/final_validation/input/ProbeThermalContact.mo"
        raw = Path(tempfile.mkdtemp(prefix="probe-thermal-", dir=root / "analysis/final_validation/results/v0.8"))
        commands = ['setCompiler("gcc");', 'setCXXCompiler("g++");', f'loadFile("{model}");', 'getErrorString();']
        for i, conductance in enumerate((.1, 1.215, 2.44)):
            commands.append(f'simulate(ProbeThermalContact, stopTime=120, numberOfIntervals=1200, tolerance=1e-9, outputFormat="csv", fileNamePrefix="case{i}", simflags="-override=contactConductance={conductance}");')
            commands.append('getErrorString();')
        mos = raw / "run.mos"
        mos.write_text("\n".join(commands) + "\n")
        result["openmodelica_comparison"] = {"status": "INCOMPLETE", "raw_directory": str(raw.relative_to(root))}
        output.write_text(json.dumps(result, indent=2) + "\n")
        try:
            proc = subprocess.run([omc, str(mos)], cwd=raw, text=True, capture_output=True, timeout=180)
        except (subprocess.TimeoutExpired, OSError) as exc:
            chunks = [getattr(exc, name, None) or "" for name in ("stdout", "stderr")]
            log = "".join(c.decode(errors="replace") if isinstance(c, bytes) else c for c in chunks)
            (raw / "solver.log").write_text(log + "\n" + type(exc).__name__ + "\n")
            result["openmodelica_comparison"].update(status="FAIL", error=type(exc).__name__)
            output.write_text(json.dumps(result, indent=2) + "\n")
            raise
        (raw / "solver.log").write_text(proc.stdout + proc.stderr)
        assert proc.returncode == 0, proc.stderr
        comparisons = []
        for i, gc in enumerate((.1, 1.215, 2.44)):
            path = raw / f"case{i}_res.csv"
            with path.open() as stream:
                samples = list(csv.DictReader(stream))
            equilibrium = (gc * wall + .01 * ambient) / (gc + .01)
            error = trajectory_error(samples, equilibrium, gc+.01, ambient)
            comparisons.append({"contact_w_k": gc, "stem_w_k": .01, "heat_capacity_j_k": 1,
                                "analytic_max_error_c": error, "equilibrium_c": equilibrium,
                                "csv_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        result["openmodelica_comparison"] = {"status": "PASS", "cases": comparisons,
            "solver_version": subprocess.check_output([omc, "--version"], text=True).strip(),
            "raw_directory": str(raw.relative_to(root)), "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest()}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("PROBE_THERMAL_BALANCE_CHECK_PASS status=HOLD", json.dumps(rows))


if __name__ == "__main__":
    main()
