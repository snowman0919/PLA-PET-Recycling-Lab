#!/usr/bin/env python3
"""Generate and validate the complete compact v0.3 release package."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(cmd, marker):
    result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    output=result.stdout+result.stderr
    if result.returncode or marker not in output:
        print(output,file=sys.stderr); raise SystemExit(f"FAIL {marker}: {' '.join(cmd)}")
    print(f"PASS {marker}")


def nix_shell(command):
    return ["nix","develop","--command","bash","-lc",command]


def main():
    run([sys.executable,"calculations/run_engineering.py"],"ENGINEERING_CALCULATIONS_OK")
    run(["make","-C","firmware/arduino_mega","test"],"MATERIAL_PROFILE_STATE_MACHINE_OK")
    gen='FreeCADCmd -c \'import runpy; runpy.run_path("cad/generation/generate_all.py", run_name="__main__")\''
    render='FreeCADCmd -c \'import runpy; runpy.run_path("cad/generation/render_views.py", run_name="__main__")\''
    run(["bash","-lc",gen] if shutil.which("FreeCADCmd") else nix_shell(gen),"COMPACT_CAD_GENERATION_OK")
    freecad_check='FreeCADCmd -c \'import runpy; runpy.run_path("validation/freecad_checks.py", run_name="__main__")\''
    run(["bash","-lc",freecad_check] if shutil.which("FreeCADCmd") else nix_shell(freecad_check),"FREECAD_COLLISION_LOAD_PATH_OK")
    render_probe=ROOT/"renders/assembly/compact_full_assembly_isometric.png"
    if "--regenerate-renders" in sys.argv or not render_probe.exists():
        run(["bash","-lc",render] if shutil.which("FreeCADCmd") else nix_shell(render),"COMPACT_RENDER_GENERATION_OK")
    else:
        print("PASS COMPACT_RENDER_PACKAGE_PRESENT (use --regenerate-renders to rebuild)")
    typst='typst compile --root . docs/build_manual_ko.typ docs/build_manual_ko.pdf && typst compile --root . docs/design_report_ko.typ docs/design_report_ko.pdf && echo COMPACT_PDF_BUILD_OK'
    run(["bash","-lc",typst] if shutil.which("typst") else nix_shell(typst),"COMPACT_PDF_BUILD_OK")
    run([sys.executable,"artifacts/build_manifest.py"],"ARTIFACT_MANIFEST_OK")
    run([sys.executable,"validation/test_release.py"],"COMPACT_RELEASE_VALIDATION_OK")
    print("ALL_AUTOMATED_VALIDATIONS_OK (8 orchestrated gates)")


if __name__ == "__main__": main()
