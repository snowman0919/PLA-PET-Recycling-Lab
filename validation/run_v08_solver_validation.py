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

    fea = json.loads((ROOT / "analysis/final_validation/results/v0.8/summary.json").read_text())
    modelica = json.loads((ROOT / "simulation/openmodelica/results_v0.8/summary.json").read_text())
    fine = fea["LC04"]["meshes"][-1]
    lc02 = fea["LC02"]["meshes"][-1]
    lc05 = fea["LC05"]["meshes"][-1]
    mount = fea["hot_zone_mount"]["cases"][2]
    step_rows = list(__import__("csv").DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
    if len(step_rows) != 10 or any(row["status"] != "PASS" for row in step_rows):
        raise SystemExit("FAIL final STEP manifest: expected 10 reimport-verified files")
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
        f"- final STEP: {len(step_rows)} files, all clean-document reimport PASS (AP214 fallback)",
        "", "## 경계와 보류", "",
        "- BC04 완전 고정은 SF 0.206으로 실패하며 실제 mount로 채택하지 않는다.",
        "- 선택 mount는 rear axial datum + front radial sliding guide이며 final assembly와 STEP/DXF/PDF에 반영됐다.",
        "- B31 mount 결과는 global axial restraint 검증이다. sensor-bore 83.5 MPa는 폐형식 local screen이며 3D notch FEA가 아니다.",
        "- `physical_validation_state: NOT_RUN`; 가열·가압·회전 시험은 수행하지 않았다.", "",
    ]
    report = ROOT / "docs" / "final" / "solver_validation_ko.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines))
    print("V08_SOLVER_VALIDATION_OK")


if __name__ == "__main__":
    main()
