#!/usr/bin/env python3
"""Current-revision CI; distribution and physical approval are separate gates."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release"))
from source_identity import source_identity
CAD_TESTS = {
    "test_assembly_refresh.py", "test_cad_retention_gate.py",
    "test_if031_registered_flange.py", "test_manufacturing_projection.py",
    "test_native_model_handoff.py", "test_shredder_manifest_regeneration.py",
    "test_frame_reduction_geometry.py", "test_integrated_assembly_clearance.py",
    "test_thermocouple_fastener_fit.py", "test_integrated_motion_clearance.py",
    "test_shaft_retention_geometry.py", "test_dancer_retention_geometry.py",
}
HISTORICAL_TESTS = {
    "test_release.py": "v0.6.1 release-state snapshot; superseded by v0.8 technical gates",
    "test_budget_policy_v0.6.2.1.py": "historical v0.6.2.1 budget snapshot",
    "test_fusion_policy_v0621.py": "historical Fusion lane; explicitly outside v0.8 scope",
    "test_retainer_support_evidence.py": "historical surrogate experiment; current axial-retainer qualification is audited transitively by P0",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(script: str, log: Path, env: dict, cad: bool = False) -> dict:
    command = [sys.executable, script]
    stdin = None
    if cad:
        exe = shutil.which("FreeCADCmd")
        if not exe:
            raise RuntimeError("CAD suite requires FreeCADCmd from nix develop")
        command = [exe, "-c"]
        code = ("import os,runpy,sys,traceback\nrc=0\n"
                f"sys.argv=[{script!r}]\nsys.path.insert(0,{str(ROOT/'validation')!r})\n"
                f"try:\n runpy.run_path({script!r},run_name='__main__')\n"
                "except SystemExit as e:\n rc=int(e.code or 0)\n"
                "except BaseException:\n traceback.print_exc();rc=1\n"
                "sys.stdout.flush();sys.stderr.flush();os._exit(rc)\n")
        stdin = "exec(" + repr(code) + ")\n"
    start = time.monotonic()
    with log.open("w", encoding="utf-8") as output:
        try:
            proc = subprocess.run(command, cwd=ROOT, env=env, input=stdin,
                                  text=True, stdout=output, stderr=output, timeout=900)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            output.write("\nCI timeout; not a passing result\n"); rc = 124
    return {"script": script, "returncode": rc, "seconds": round(time.monotonic()-start, 3),
            "source_sha256": digest(ROOT/script), "log_sha256": digest(log), "log": log.name}


def main() -> None:
    if not __debug__:
        raise SystemExit("Optimized Python disables assertions and is prohibited")
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("light", "cad"), default="light")
    parser.add_argument("--output", type=Path, default=ROOT/".build/ci-v08")
    args = parser.parse_args()
    output = args.output.resolve()/args.suite
    if not output.is_relative_to(ROOT):
        raise SystemExit("CI output must stay inside the repository")
    output.mkdir(parents=True, exist_ok=True)
    tmp = output/"tmp"; tmp.mkdir(exist_ok=True)
    env = dict(os.environ, TMPDIR=str(tmp), PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONOPTIMIZE", None)
    tests = sorted((ROOT/"validation").glob("test_*.py"))
    tests += sorted((ROOT/"validation/physical_v08").glob("test_*.py"))
    selected = [p for p in tests if p.name not in HISTORICAL_TESTS
                and ((p.name in CAD_TESTS) == (args.suite == "cad"))]
    scripts = [] if args.suite == "cad" else [
        "validation/runtime_supervisor.py",
        "validation/physical_v08/simulation_prerequisite.py",
        "validation/physical_v08/validate_readiness.py",
        "validation/physical_v08/validate_execution_registry.py",
    ]
    scripts += [str(p.relative_to(ROOT)) for p in selected]
    head, _ = source_identity(ROOT)
    records = []
    for index, script in enumerate(scripts):
        record = execute(script, output/f"{index:02d}-{Path(script).stem}.log", env,
                         cad=args.suite == "cad")
        records.append(record)
        print(f"{record['returncode']:3d} {script}", flush=True)
    failed = [r for r in records if r["returncode"] != 0]
    result = {"schema_version": 1, "revision": "final-design-fabrication-closure-v0.8",
              "suite": args.suite, "head": head, "status": "FAIL" if failed else "PASS",
              "commands": len(records), "test_modules": len(selected), "records": records,
              "historical_tests_not_current_release_gates": HISTORICAL_TESTS,
              "cad_tests_run_in_full_job": sorted(CAD_TESTS),
              "physical_validation_state": "NOT_RUN", "safety_certification": "NOT_CERTIFIED",
              "fabrication_authorized": False, "energization_authorized": False,
              "scope": "fresh software tests and current recorded-evidence integrity; not a new full-physics solve"}
    (output/"result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    summary = (f"# PPR v0.8 / {args.suite}\n\nCommit: `{head}`\n\n"
               f"Result: **{result['status']}**; commands: {len(records)}; test modules: {len(selected)}.\n\n"
               "Physical validation: NOT_RUN. No fabrication or energization authorization.\n")
    (output/"SUMMARY.md").write_text(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as handle: handle.write(summary)
    for record in failed:
        print((output/record["log"]).read_text(errors="replace")[-5000:])
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
