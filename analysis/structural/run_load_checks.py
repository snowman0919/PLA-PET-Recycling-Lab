#!/usr/bin/env python3
"""OpenModelica 동적 envelope에서 제작 전 구조 screening과 CalculiX deck를 생성한다."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "analysis" / "structural"
GEN = HERE / "generated"
RESULTS = HERE / "results"
ENVELOPE_PATH = ROOT / "analysis" / "load_cases" / "openmodelica_dynamic_envelope.json"


def vm_bending_torsion(moment_nm: float, torque_nm: float, diameter_mm: float) -> float:
    diameter_m = diameter_mm / 1000
    sigma = 32 * moment_nm / (math.pi * diameter_m**3)
    tau = 16 * torque_nm / (math.pi * diameter_m**3)
    return math.sqrt(sigma**2 + 3 * tau**2) / 1e6


def plate_deck(load_n: float) -> str:
    """120×100×12 mm steel plate; fixed side to bearing-load side screening mesh."""
    nx, ny, nz = 12, 10, 2
    dx, dy, dz = 0.01, 0.01, 0.006
    nodes: list[str] = []
    node_id: dict[tuple[int, int, int], int] = {}
    nid = 1
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                node_id[i, j, k] = nid
                nodes.append(f"{nid},{i*dx:.6f},{j*dy:.6f},{k*dz:.6f}")
                nid += 1
    elements: list[str] = []
    eid = 1
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                conn = [
                    node_id[i, j, k], node_id[i + 1, j, k], node_id[i + 1, j + 1, k], node_id[i, j + 1, k],
                    node_id[i, j, k + 1], node_id[i + 1, j, k + 1], node_id[i + 1, j + 1, k + 1], node_id[i, j + 1, k + 1],
                ]
                elements.append(f"{eid}," + ",".join(map(str, conn)))
                eid += 1
    fixed = [node_id[0, j, k] for k in range(nz + 1) for j in range(ny + 1)]
    loaded = [node_id[nx, j, k] for k in range(nz + 1) for j in range(4, 7)]
    per_node = -load_n / len(loaded)
    fixed_lines = [",".join(map(str, fixed[i:i + 16])) for i in range(0, len(fixed), 16)]
    loaded_lines = [",".join(map(str, loaded[i:i + 16])) for i in range(0, len(loaded), 16)]
    return "\n".join([
        "*HEADING", "PPR v0.4 bearing plate screening; SI units m N Pa",
        "*NODE", *nodes,
        "*ELEMENT,TYPE=C3D8,ELSET=EALL", *elements,
        "*NSET,NSET=FIXED", *fixed_lines,
        "*NSET,NSET=LOADED", *loaded_lines,
        "*SOLID SECTION,ELSET=EALL,MATERIAL=S275", "",
        "*MATERIAL,NAME=S275", "*ELASTIC", "2.05E11,0.30",
        "*BOUNDARY", "FIXED,1,3,0",
        "*STEP", "*STATIC", "0.1,1.0",
        "*CLOAD", f"LOADED,3,{per_node:.9f}",
        "*NODE FILE,NSET=LOADED", "U",
        "*EL FILE", "S",
        "*END STEP", "",
    ])


def shaft_deck(radial_load_n: float, torque_nm: float) -> str:
    """20 mm shaft 30 mm sprocket overhang screening, B31 elements."""
    nodes = [f"{i+1},{i*0.01:.6f},0,0" for i in range(4)]
    elements = [f"{i+1},{i+1},{i+2}" for i in range(3)]
    return "\n".join([
        "*HEADING", "PPR v0.4 cutter shaft screening; SI units m N Pa",
        "*NODE", *nodes,
        "*ELEMENT,TYPE=B31,ELSET=EALL", *elements,
        "*NSET,NSET=FIXED", "1",
        "*NSET,NSET=FREE", "4",
        "*BEAM SECTION,ELSET=EALL,MATERIAL=S45C,SECTION=RECT", "0.01772,0.01772", "0,0,1",
        "*MATERIAL,NAME=S45C", "*ELASTIC", "2.05E11,0.29",
        "*BOUNDARY", "FIXED,1,6,0",
        "*STEP", "*STATIC", "0.1,1.0",
        "*CLOAD", f"FREE,3,{-radial_load_n:.9f}", f"FREE,4,{torque_nm:.9f}",
        "*NODE FILE", "U",
        "*EL FILE", "S",
        "*END STEP", "",
    ])


def parse_frd(path: Path) -> dict:
    mode = ""
    max_displacement = 0.0
    max_vm = 0.0
    number_pattern = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            mode = "DISP" if "DISP" in line else "STRESS" if "STRESS" in line else ""
            continue
        if line.startswith(" -3"):
            mode = ""
            continue
        if not mode or not line.startswith(" -1"):
            continue
        values = [float(value) for value in number_pattern.findall(line)][2:]
        if mode == "DISP" and len(values) >= 3:
            max_displacement = max(max_displacement, math.sqrt(sum(value**2 for value in values[:3])))
        if mode == "STRESS" and len(values) >= 6:
            sx, sy, sz, txy, tyz, tzx = values[:6]
            vm = math.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(txy**2+tyz**2+tzx**2))
            max_vm = max(max_vm, vm)
    return {"max_displacement_mm": max_displacement * 1000, "max_von_mises_mpa": max_vm / 1e6}


def run_ccx(stem: str) -> dict:
    executable = shutil.which("ccx")
    if executable is None:
        return {"status": "NOT_RUN", "reason": "ccx not on PATH"}
    proc = subprocess.run([executable, stem], cwd=GEN, text=True, capture_output=True, timeout=120)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{stem}.log").write_text(log)
    frd = GEN / f"{stem}.frd"
    result = {
        "status": "PASS" if proc.returncode == 0 and frd.exists() else "FAIL",
        "returncode": proc.returncode,
        "frd_bytes": frd.stat().st_size if frd.exists() else 0,
        "converged": "Job finished" in log or "JOB FINISHED" in log.upper(),
    }
    if frd.exists():
        result.update(parse_frd(frd))
    return result


def check(name: str, stress_mpa: float, allowable_mpa: float, source: str, note: str) -> dict:
    sf = allowable_mpa / stress_mpa if stress_mpa > 0 else 999.0
    return {
        "component": name,
        "method": "closed-form screening",
        "source_load": source,
        "equivalent_stress_mpa": round(stress_mpa, 3),
        "allowable_mpa": allowable_mpa,
        "safety_factor": round(sf, 2),
        "criterion": "SF >= 2.0 before coupon; physical validation pending",
        "status": "PASS" if sf >= 2 else "FAIL",
        "note": note,
    }


def main() -> None:
    envelope = json.loads(ENVELOPE_PATH.read_text())
    loads = envelope["loads"]
    caps = envelope["design_caps"]
    radial = loads["peak_bearing_load_n"]
    chain = loads["peak_chain_force_n"]
    cutter_torque = caps["input_fuse_torque_nm"]
    phase_torque = caps["phase_allowable_torque_nm"]

    shaft_moment = radial * 0.030
    cutter_force = cutter_torque / 0.029
    cutter_root_stress = 6 * cutter_force * 0.011 / (0.006 * 0.012**2) / 1e6
    key_force = phase_torque / 0.010
    key_shear = key_force / (0.006 * 0.018) / 1e6
    plate_bending = 6 * radial * 0.030 / (0.012 * 0.075**2) / 1e6
    sprocket_stress = vm_bending_torsion(chain * 0.030, cutter_torque, 20)
    motor_plate = 6 * loads["peak_frame_reaction_n"] * 0.045 / (0.006 * 0.100**2) / 1e6
    screw_thrust = 6.0e6 * math.pi * 0.016**2 / 4
    screw_plate = 6 * screw_thrust * 0.025 / (0.012 * 0.070**2) / 1e6
    spool_load = 1.35 * 9.80665 + 8
    spool_shaft = 32 * spool_load * 0.085 / (math.pi * 0.008**3) / 1e6
    anchor_stress = envelope["full_system"]["peak_anchor_tension_n"] / (math.pi * 6.466e-3**2 / 4) / 1e6

    checks = [
        check("CUT-01 cutter tooth/root", cutter_root_stress, 350, "22 N·m cutter-equivalent DRV-F01 relief cap", "6 mm tool-steel coupon geometry; impact/notch factor is not physically calibrated"),
        check("SH-SHAFT-01 20 mm cutter shaft", vm_bending_torsion(shaft_moment, cutter_torque, 20), 177.5, "bearing envelope + fuse cap", "S45C normalized; allowable=0.5×355 MPa yield"),
        check("SH-PLATE-01 bearing plate", plate_bending, 137.5, "peak bearing load", "12 mm S275 ligament simplified as 75 mm strip"),
        check("PH-KEY-01 phase gear key", key_shear, 120, "34 N·m phase allowable", "6×6×18 mm key shear; hub bearing pressure separately inspect at RFQ"),
        check("CH-SPROCKET-01 overhang", sprocket_stress, 177.5, "chain envelope + fuse cap", "20 mm shaft, 30 mm overhang"),
        check("DRV-03 motor adapter plate", motor_plate, 75, "peak frame reaction", "6 mm 6061-T6/S275 equivalent bending strip; slot edge inspection required"),
        check("EX-THR-01 screw thrust plate", screw_plate, 137.5, "6 MPa conservative blocked-die thrust", f"calculated axial thrust {screw_thrust:.0f} N; open die and sacrificial relief remain mandatory"),
        check("SP-SHAFT-01 spool shaft", spool_shaft, 100, "1.35 kg spool + 8 N line tension", "8 mm steel shaft, 85 mm cantilever"),
        check("FR-ANCHOR-01 M8 table anchor", anchor_stress, 320, "FullMechanicalNominal anchor tension", "minor-diameter tensile area; four anchors required, one-anchor conservative screening"),
    ]

    GEN.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (GEN / "bearing_plate.inp").write_text(plate_deck(radial))
    (GEN / "cutter_shaft.inp").write_text(shaft_deck(radial, cutter_torque))
    fea = {"bearing_plate": run_ccx("bearing_plate"), "cutter_shaft": run_ccx("cutter_shaft")}

    failed = [item["component"] for item in checks if item["status"] != "PASS"]
    if any(item["status"] == "FAIL" for item in fea.values()):
        failed.append("CalculiX execution")
    result = {
        "revision": envelope["revision"],
        "release_state": "DIGITAL_FABRICATION_BASELINE",
        "physical_state": "PHYSICAL_NOT_RUN",
        "input": str(ENVELOPE_PATH.relative_to(ROOT)),
        "input_source": envelope["source"],
        "load_values": loads,
        "calculix": fea,
        "checks": checks,
        "status": "PASS" if not failed else "FAIL",
        "failures": failed,
        "limitations": [
            "OpenModelica cutter load is a pre-Gate-1 surrogate, not measured cutting torque.",
            "Closed-form checks are screening models; stress concentration, fatigue, impact, weld and fastener preload require drawing review and physical gates.",
            "CalculiX decks are linear-elastic decision checks for global shaft/plate response and do not certify the machine.",
        ],
    }
    (RESULTS / "structural_screening.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# 동적 하중 연계 구조 검토",
        "",
        f"- revision: `{envelope['revision']}`",
        f"- 판정: **{result['status']}**",
        "- 물리 상태: `PHYSICAL_NOT_RUN`",
        f"- 하중 원본: `{result['input']}`",
        "",
        "|부품|등가응력 MPa|허용 MPa|안전율|판정|",
        "|---|---:|---:|---:|---:|",
    ]
    lines += [f"|{c['component']}|{c['equivalent_stress_mpa']:.3f}|{c['allowable_mpa']:.1f}|{c['safety_factor']:.2f}|{c['status']}|" for c in checks]
    lines += [
        "",
        "## 해석 의미",
        "",
        "각 계산의 source_load는 동일 OpenModelica envelope 또는 그보다 낮은 것이 아니라 명시된 mechanical cap이다. 따라서 upstream 22 N·m torque fuse가 34 N·m phase drivetrain과 48 N·m shaft/cutter보다 먼저 작동해야 한다. Gate-1에서 토크 pulse와 jam 하중을 얻으면 이 파일을 다시 생성해야 한다.",
        "",
        "CalculiX deck는 `generated/bearing_plate.inp`, `generated/cutter_shaft.inp`이며 선형 탄성 global screening이다. 상세 notch/contact 검토 및 물리 coupon을 대체하지 않는다.",
        "",
    ]
    (HERE / "structural_validation_ko.md").write_text("\n".join(lines))
    if failed:
        raise SystemExit(f"STRUCTURAL_SCREENING_FAIL {failed}")
    print(f"STRUCTURAL_SCREENING_OK checks={len(checks)} radial_N={radial:.1f}")


if __name__ == "__main__":
    main()
