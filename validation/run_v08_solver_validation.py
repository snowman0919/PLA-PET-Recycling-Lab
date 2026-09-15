#!/usr/bin/env python3
"""v0.8 FreeCAD/CalculiX/OpenModelica/tolerance release-blocker gate."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], marker: str) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=900)
    output = result.stdout + result.stderr
    print(output, end="")
    if result.returncode or marker not in output:
        raise SystemExit(f"FAIL {marker}: {' '.join(command)}")


def freecad(script: str, marker: str) -> None:
    code = f'_result=__import__("runpy").run_path("{script}",run_name="__main__"); __import__("sys").stdout.flush(); __import__("os")._exit(0)'
    result = subprocess.run([shutil.which("FreeCADCmd") or "FreeCADCmd", "-c"], cwd=ROOT, text=True, input=code + "\n", capture_output=True, timeout=900)
    output = result.stdout + result.stderr
    print(output, end="")
    if result.returncode or marker not in output:
        raise SystemExit(f"FAIL {marker}: FreeCADCmd {script}")


def write_report() -> None:
    fea = json.loads((ROOT / "analysis/final_validation/results/v0.8/summary.json").read_text())
    modelica = json.loads((ROOT / "simulation/openmodelica/results_v0.8/summary.json").read_text())
    fine = fea["LC04"]["meshes"][-1]
    lc02 = fea["LC02"]["meshes"][-1]
    lc05 = fea["LC05"]["meshes"][-1]
    mount = fea["hot_zone_mount"]["cases"][2]
    step_rows = list(__import__("csv").DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
    required_step_ids = {
        "PPR-FULL-ASM", "PPR-SHREDDER-ASM", "PPR-FEEDER-ASM",
        "PPR-EXTRUDER-ASM", "PPR-FORMING-ASM", "PPR-FRAME-ASM",
        "ExtruderSupportRailRear", "ExtruderRearFixedDatum",
        "ExtruderFrontSlidingGuide", "ExtruderFixedCollar",
    }
    by_id = {row["part_id"]: row for row in step_rows}
    if not required_step_ids <= set(by_id) or any(by_id[pid]["status"] != "PASS" for pid in required_step_ids):
        raise SystemExit("FAIL final STEP manifest: missing/non-PASS solver-required release files")
    lines = [
        "# v0.8 solver 검증 보고", "",
        "이 결과는 디지털 해석이며 실제 물리 시험·안전 인증이 아니다.", "",
        "## 실행 환경", "",
        "- FreeCAD 1.1.3: controlling solid 생성과 STEP 재수입",
        "- Gmsh 4.15.2-git: 실제 CUT-03 STEP tetra mesh",
        "- CalculiX 2.23: `OMP_NUM_THREADS=1` 구조/열팽창 해석",
        "- OpenModelica 1.27.0 DASSL: mount travel와 LC09 scope 계약",
        "", "## 판정", "",
        f"- LC04 actual FreeCAD plate: {fine['result']['max_displacement_mm']:.6f} mm, medium→fine {fea['LC04']['medium_to_fine_delta_percent']:.3f}%, `{fea['LC04']['resolution']}`",
        f"- LC04 fine reaction force Y: {fine['result']['reaction']['force_n'][1]:.6f} N / applied {abs(fine['provenance']['net_force_n'][1]):.6f} N",
        f"- LC02 shaft: {lc02['result']['max_displacement_mm']:.6f} mm, {lc02['result']['max_von_mises_mpa']:.3f} MPa, SF {lc02['result']['regional_safety_factor']:.3f}; force/moment residual {max(map(abs, lc02['result']['equilibrium']['force_residual_n'])):.6f} N / {max(map(abs, lc02['result']['equilibrium']['moment_residual_nm'])):.6f} N·m",
        f"- LC05 shaft: {lc05['result']['max_displacement_mm']:.6f} mm, {lc05['result']['max_von_mises_mpa']:.3f} MPa, SF {lc05['result']['regional_safety_factor']:.3f}; force/moment residual {max(map(abs, lc05['result']['equilibrium']['force_residual_n'])):.6f} N / {max(map(abs, lc05['result']['equilibrium']['moment_residual_nm'])):.6f} N·m",
        f"- PET hot-zone free growth: {modelica['hot_zone']['axialGrowthMm']:.4f} mm, 1.3 mm travel margin {modelica['hot_zone']['travelMarginMm']:.4f} mm",
        f"- selected radial/sliding mount regional SF: {mount['safety_factor']:.3f}",
        f"- LC09 scope: spindle 143 mm, bearing spacing 88 mm, load at 40.5 mm, radial load {modelica['LC09']['radialLoadN']:.4f} N",
        f"- final STEP inventory: {len(step_rows)} files; solver-required 10 files are present and PASS",
        "", "## 경계와 보류", "",
        "- 축 moment residual은 출력된 절점 힘의 r×F만 포함한다. 회전 자유도 반력 couple은 추출하지 않았으므로 축방향 토크 평형의 독립 검증이 아니다.",
        "- BC04 완전 고정은 채택하지 않으며 rear axial datum + front radial sliding guide가 release mount다.",
        "- B31 mount 결과는 global axial restraint screen이다. 상세 sensor-bore/die-joint/thermal-fit closure는 별도 current digital qualification evidence를 따른다.",
        "- `physical_validation_state: NOT_RUN`; 가열·가압·회전 시험은 수행하지 않았다.", "",
    ]
    report_path = ROOT / "docs" / "final" / "solver_validation_ko.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"V08_SOLVER_REPORT_OK step_inventory={len(step_rows)} required={len(required_step_ids)}")


def main() -> None:
    required = ("FreeCADCmd", "gmsh", "ccx", "omc", "typst")
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        raise SystemExit(f"run inside `nix develop`: missing {', '.join(missing)}")
    run([sys.executable, "calculations/tolerance_stack_final.py"], "FINAL_TOLERANCE_STACK_OK")
    freecad("validation/final_v08_cad.py", "V08_FINAL_CAD_OK")
    freecad("cad/freecad/final_v08/generate.py", "V08_FINAL_STEP_OK")
    drawing = ROOT / "exports/final/manufacturing/hot_zone/hot_zone_mount_drawings.pdf"
    run(["typst", "compile", "--root", ".", "docs/final/hot_zone_mount_drawings.typ", str(drawing)], "")
    if not drawing.is_file() or drawing.stat().st_size < 10_000:
        raise SystemExit("FAIL hot-zone vector PDF drawing")
    run(["omc", "simulation/openmodelica/scripts/run_v08_release.mos"], "SimulationResult")
    run([sys.executable, "simulation/openmodelica/postprocess/validate_v08_release.py"], "V08_OPENMODELICA_VALIDATION_OK")
    run([sys.executable, "analysis/final_validation/run_calculix_v08.py"], "V08_CALCULIX_VALIDATION_OK")
    write_report()
    print("V08_SOLVER_VALIDATION_OK")


if __name__ == "__main__":
    if "--report-only" in sys.argv[1:]:
        write_report()
    else:
        main()
