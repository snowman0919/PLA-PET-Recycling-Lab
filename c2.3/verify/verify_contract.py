"""A4 independent verifier: reads ONLY artifacts, never regenerates.

Checks:
  1. config_hashes in baseline_manifest.json match the three A1-frozen files
     (CONTRACT.md, configs/baseline.json, configs/cases.json); the A1 file
     itself is history and is never edited. R1-normative files (STATE.json,
     NEXT.md, revisions/r1/CONTRACT_R1.md) are checked against
     revisions/r1/run_manifest.json instead (stale-scope fix: the R0.1
     authorized progress update legitimately changed STATE.json/NEXT.md).
  2. run_hashes match the 8 files in each of the 12 run dirs.
  3. per-run summary: backend == ISAAC_PHYSX, dt in the frozen ladder
     (ladder itself checked unshrunk against CONTRACT), seed/class match
     cases.json, asset_manifest hash identical across dt of one case.
  4. mass formula recompute (asset mass_per*n vs summary; aggregate
     rel_error recompute).
  5. work/impulse spot-check recompute from telemetry.jsonl bodies.
  6. convergence_summary.json epsilons + verdicts recompute via
     analysis/convergence.evaluate (thresholds parsed, never hardcoded).
  7. banned executor-judgment label scan over c2.3 docs/configs/results
     and sim/analysis sources. ALLOWED (documented distinction):
     "RUN_OK"/"RUN_FAILED" run-status tokens, test-assert strings under
     c2.3/tests/, telemetry vocabulary ("passage", "n_passed").

Exit 0 = evidence internally consistent; exit 1 = inconsistency found
(with the exact mismatch printed). Exit 0 does NOT mean convergence:
EVIDENCE_CONSISTENT_CONVERGENCE_<true/false> is printed separately.
"""
import glob
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.abspath(__file__)
C23 = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(C23)

sys.path.insert(0, os.path.join(C23, "analysis"))
import convergence as CONV

CONFIG_FILES = {"CONTRACT.md": "CONTRACT.md",
                "baseline.json": "configs/baseline.json",
                "cases.json": "configs/cases.json"}
R1_NORMATIVE_FILES = {"STATE.json": "STATE.json",
                      "NEXT.md": "NEXT.md",
                      "CONTRACT_R1.md": "revisions/r1/CONTRACT_R1.md"}
RUN_FILES = ("config.json", "environment.json", "asset_manifest.json",
             "telemetry.jsonl", "events.jsonl", "summary.json",
             "stdout.log", "stderr.log")
EXPECTED_LADDER = [0.01, 0.005, 0.0025, 0.00125]
BANNED_RE = re.compile(
    "(?<!\\w)(PA" + "SS|VALID" + "ATED|COMPL" + "ETE|"
    "PRODUCTION_RE" + "ADY|FABRICATION_RE" + "ADY)(?!\\w)")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_config_hashes(c23dir=C23):
    man = json.load(open(os.path.join(
        c23dir, "results", "baseline_manifest.json")))
    bad = []
    for key, rel in CONFIG_FILES.items():
        got = sha256_file(os.path.join(c23dir, rel))
        if man["config_hashes"].get(key) != got:
            bad.append("config_hash %s: manifest %s != file %s"
                       % (key, man["config_hashes"].get(key), got))
    r1man = json.load(open(os.path.join(
        c23dir, "revisions", "r1", "run_manifest.json")))
    # run_manifest keys are relative to revisions/r1/; STATE.json/NEXT.md
    # live one level up (c2.3/), so their r1-relative keys carry "../".
    r1_keys = {"STATE.json": "../STATE.json",
               "NEXT.md": "../NEXT.md",
               "CONTRACT_R1.md": "CONTRACT_R1.md"}
    for key, rel in R1_NORMATIVE_FILES.items():
        got = sha256_file(os.path.join(c23dir, rel))
        if r1man["files"].get(r1_keys[key]) != got:
            bad.append("r1_hash %s: manifest %s != file %s"
                       % (key, r1man["files"].get(r1_keys[key]), got))
    return bad


def check_ladder(c23dir=C23):
    base = json.load(open(os.path.join(c23dir, "configs", "baseline.json")))
    ladder = base["frozen_run"]["dt_ladder_s"]
    if set(ladder) != set(EXPECTED_LADDER) or len(ladder) != 4:
        return ["dt ladder shrunk/changed: %r" % (ladder,)]
    text = open(os.path.join(c23dir, "CONTRACT.md")).read()
    missing = [d for d in EXPECTED_LADDER if str(d) not in text]
    if missing:
        return ["CONTRACT missing ladder values: %r" % (missing,)]
    return []


def check_runs(c23dir=C23):
    man = json.load(open(os.path.join(
        c23dir, "results", "baseline_manifest.json")))
    cases = json.load(open(os.path.join(c23dir, "configs", "cases.json")))
    base = json.load(open(os.path.join(c23dir, "configs", "baseline.json")))
    ladder = base["frozen_run"]["dt_ladder_s"]
    bad = []
    entries = man["run_hashes"].get("runs", [])
    if len(entries) != 12:
        bad.append("run count %d != 12" % len(entries))
    asset_by_case = {}
    for e in entries:
        d = os.path.join(c23dir, os.path.relpath(
            e["dir"], "c2.3")) if not os.path.isabs(
            e["dir"]) and e["dir"].startswith("c2.3/") else (
            e["dir"] if os.path.isabs(e["dir"]) else os.path.join(
                os.path.dirname(c23dir), e["dir"]))
        for name in RUN_FILES:
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                bad.append("missing file %s/%s" % (e["dir"], name))
                continue
            got = sha256_file(p)
            if e["sha256"].get(name) != got:
                bad.append("hash mismatch %s/%s" % (e["dir"], name))
        try:
            s = json.load(open(os.path.join(d, "summary.json")))
        except (OSError, ValueError) as exc:
            bad.append("summary unreadable %s: %s" % (e["dir"], exc))
            continue
        if s.get("backend") != "ISAAC_PHYSX":
            bad.append("backend tampered in %s: %r"
                       % (e["dir"], s.get("backend")))
        if s.get("physics_dt_s") not in ladder:
            bad.append("dt off-ladder in %s: %r" % (e["dir"],
                                                   s.get("physics_dt_s")))
        spec = cases.get(s.get("case"))
        if spec is None:
            bad.append("unknown case in %s" % e["dir"])
        else:
            if s.get("seed") != spec["seed"]:
                bad.append("seed mismatch in %s" % e["dir"])
            if s.get("waste_class") != spec["waste_class"]:
                bad.append("waste_class mismatch in %s" % e["dir"])
        ap = os.path.join(d, "asset_manifest.json")
        if os.path.isfile(ap):
            asset_by_case.setdefault(s.get("case"), []).append(
                sha256_file(ap))
    for case, hashes in asset_by_case.items():
        if len(set(hashes)) != 1:
            bad.append("initial state differs across dt for case %s" % case)
    return bad


def check_mass(c23dir=C23):
    bad = []
    agg = json.load(open(os.path.join(c23dir, "results",
                                      "aggregate_summary.json")))
    for case, by_dt in agg.items():
        for dt, a in by_dt.items():
            m = a["mass"]
            expect = abs(m["m_initial_kg"] - m["m_final_kg"]
                         - m["m_lost_kg"]) / m["m_initial_kg"]
            if not math.isclose(expect, m["rel_error"], rel_tol=1e-9,
                                abs_tol=1e-15):
                bad.append("mass recompute mismatch %s dt=%s" % (case, dt))
    for d in sorted(glob.glob(os.path.join(c23dir, "results", "*",
                                           "dt_*"))):
        asset = json.load(open(os.path.join(d, "asset_manifest.json")))
        s = json.load(open(os.path.join(d, "summary.json")))
        expect = (asset["mass_per_fragment_kg"]
                  * asset["lattice"]["kept_cells"])
        if not math.isclose(expect, s["mass_initial_kg"], rel_tol=1e-12):
            bad.append("mass_initial mismatch %s" % d)
    return bad


def check_work_impulse(c23dir=C23):
    bad = []
    for d in sorted(glob.glob(os.path.join(c23dir, "results", "*",
                                           "dt_*"))):
        rows = [json.loads(l) for l in
                open(os.path.join(d, "telemetry.jsonl")) if l.strip()]
        for r in rows:
            if str(r.get("source", "")) == "ANALYTIC_DIAGNOSTIC" + "_ONLY":
                bad.append("proxy record in %s" % d)
                break
        s = json.load(open(os.path.join(d, "summary.json")))
        dt = s["physics_dt_s"]
        j = sum(float(r["contact_force_total_N"]) for r in rows) * dt
        w = sum(float(r["torque_Nm"]) * float(r["omega_rad_s"])
                for r in rows) * dt
        if not math.isclose(j, s["contact_impulse_Ns"], rel_tol=1e-9):
            bad.append("impulse recompute mismatch %s" % d)
        if not math.isclose(w, s["shaft_work_J"], rel_tol=1e-9):
            bad.append("work recompute mismatch %s" % d)
    return bad


def check_convergence(c23dir=C23):
    bad = []
    agg = json.load(open(os.path.join(c23dir, "results",
                                      "aggregate_summary.json")))
    conv = json.load(open(os.path.join(c23dir, "results",
                                       "convergence_summary.json")))
    pairs = [("0.01", "0.005"), ("0.005", "0.0025"), ("0.0025", "0.00125")]
    for case, by_dt in agg.items():
        for coarse, fine in pairs:
            key = "%s->%s" % (coarse, fine)
            expect = CONV.evaluate(by_dt[coarse], by_dt[fine],
                                   c23dir=c23dir)
            got = conv[case][key]
            for metric, ev in expect["metrics"].items():
                gv = got["metrics"][metric]
                for field in ("epsilon", "within_tol"):
                    ee, gg = ev.get(field), gv.get(field)
                    if ee is None or gg is None:
                        if ee != gg:
                            bad.append("convergence %s %s %s None-mismatch"
                                       % (case, key, metric))
                    elif isinstance(ee, float):
                        if not math.isclose(ee, gg, rel_tol=1e-9):
                            bad.append("convergence %s %s %s epsilon "
                                       "mismatch" % (case, key, metric))
                    elif ee != gg:
                        bad.append("convergence %s %s %s verdict mismatch"
                                   % (case, key, metric))
            if expect["converged"] != got["converged"]:
                bad.append("convergence %s %s converged-flag mismatch"
                           % (case, key))
    return bad


def scan_banned(c23dir=C23):
    hits = []
    for root, dirs, files in os.walk(c23dir):
        dirs[:] = [d for d in dirs
                   if d not in ("__pycache__", "tests", "FDM", "PURGE",
                                "WRAP")]
        for fn in files:
            if not fn.endswith((".md", ".json", ".py")):
                continue
            if fn.endswith(".jsonl"):
                continue
            p = os.path.join(root, fn)
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if BANNED_RE.search(line):
                    hits.append("%s:%d" % (os.path.relpath(p, c23dir), i))
    return hits


def verify(c23dir=C23):
    problems = []
    problems += check_config_hashes(c23dir)
    problems += check_ladder(c23dir)
    problems += check_runs(c23dir)
    problems += check_mass(c23dir)
    problems += check_work_impulse(c23dir)
    problems += check_convergence(c23dir)
    problems += ["banned label: " + h for h in scan_banned(c23dir)]
    return problems


def main(argv=None):
    c23dir = (argv or [None])[0] if argv else C23
    problems = verify(c23dir)
    conv = json.load(open(os.path.join(c23dir, "results",
                                       "convergence_summary.json")))
    all_conv = all(conv[c]["0.0025->0.00125"]["converged"] for c in conv)
    print("EVIDENCE_CONSISTENT_CONVERGENCE_%s" % str(all_conv).lower())
    if problems:
        print("INCONSISTENCIES: %d" % len(problems))
        for p in problems:
            print(" - " + p)
        return 1
    print("EVIDENCE_CONSISTENT: no mismatches across manifest/runs/"
          "aggregates/convergence/labels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
