"""패키지에 수록된 소스만으로 출력·인벤토리 검증 모듈을 import한다."""
import shutil
import json
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "release"))
from build_fabrication_release import collect, ROOT
import build_fabrication_release as builder

with tempfile.TemporaryDirectory() as directory:
    fixture = Path(directory)
    (fixture / "release").mkdir()
    (fixture / "release/package_layout.json").write_text(json.dumps({"sections": {"test": ["input.txt"]}}))
    target = fixture / "input.txt"
    target.write_text("allowed source")
    with patch.object(builder, "ROOT", fixture):
        assert len(collect()) == 1
        target.rename(fixture / "other.txt")
        target.symlink_to(fixture / "other.txt")
        try:
            collect()
        except AssertionError as error:
            assert "symlinked package source" in str(error)
        else:
            raise AssertionError("Symlink source accepted into release")

files = collect()
sources = {rel for src, rel in files.values()}
assert {
    'analysis/final_validation/hot_zone_revision_review.py',
    'analysis/final_validation/results/v0.8/hot_zone_revision_review.json',
    'analysis/thermal_revision_v08/README_KO.md',
    'analysis/thermal_revision_v08/compare.py',
    'analysis/thermal_revision_v08/model.py',
    'analysis/thermal_revision_v08/model_inputs.json',
    'analysis/thermal_revision_v08/reference_geometry.json',
    'cad/generation/export_modelica_properties.py',
    'release/plain_shaft_drawing.py',
    'validation/integrated_assembly_clearance.py',
    'validation/integrated_motion_clearance.py',
    'validation/shaft_retention_clearance.py',
} <= sources, "missing current geometry/thermal dependencies"
assert "docs/final/package_replay_ko.md" in sources
assert {"docs/final/v08_closure_report_ko.md", "docs/final/v08_full_compliance_ko.md",
        "validation/results/v08_release_inventory.json", "validation/results/v08_full_compliance.json"}.isdisjoint(sources)
assert {"flake.nix", "flake.lock", "nix/openmodelica.nix"} <= sources
assert {"exports/final/interface_catalog.csv", "calculations/tolerance_stack_final.json",
        "analysis/final_validation/results/v0.8/loaded_phase.json",
        "validation/results/final_v08_cad.json", "validation/results/cutter_phase_sweep.json"} <= sources
step_rows = list(csv.DictReader((ROOT / "exports/final/step/step_manifest.csv").open()))
assert all("exports/final/step/" + row["file"] in sources for row in step_rows), "STEP manifest references unpackaged file"
print_rows = list(csv.DictReader((ROOT / "exports/final/print/print_manifest.csv").open()))
assert all("exports/final/print/" + row[field] in sources for row in print_rows
           for field in ("stl_file", "three_mf_file", "step_reference_file", "plate_layout_file", "orientation_render")), "print manifest references unpackaged file"
assert {"release/firmware_evidence.py", "validation/mesh_checks.py"} <= sources
assert {"validation/final_v08_cad.py", "validation/cutter_phase_sweep.py"} <= sources
assert {"cad/parameters/baseline.json", "analysis/final_validation/run_phase_load_v08.py",
        "analysis/structural/run_load_checks.py", "analysis/load_cases/openmodelica_dynamic_envelope.json",
        "analysis/final_validation/run_sensor_bore_local_candidate.py",
        "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json"} <= sources
assert {"analysis/final_validation/run_phase_section_sensitivity_v08.py",
        "analysis/final_validation/run_phase_gear_elastic_candidate.py",
        "analysis/final_validation/run_keyed_shaft_torsion_candidate.py",
        "validation/check_phase_path_25_evidence.py",
        "analysis/final_validation/results/v0.8/phase_path_25_qualification.json",
        "analysis/final_validation/results/v0.8/phase_pair_backlash_candidate.json",
        "analysis/final_validation/results/v0.8/phase_path_25_solid_gear.step",
        "analysis/final_validation/input/geometry_manifest.json",
        "analysis/final_validation/input/bearing_plate.step"} <= sources
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for dest, (source, relative) in files.items():
        if dest.startswith("10_DESIGN_SOURCE/"):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    envelope = json.loads((root / "analysis/load_cases/openmodelica_dynamic_envelope.json").read_text())
    assert envelope["loads"]["peak_bearing_load_n"] > 0
    runner = (root / "simulation/openmodelica/scripts/run_v08_release.mos").read_text()
    inputs = re.search(r'system\("sha256sum ([^>]+)>', runner).group(1).split()
    expected_inputs = {
        'simulation/openmodelica/v0.8/V08ReleaseScenarios.mo',
        'simulation/openmodelica/PLA_PET_Recycler/Systems/DynamicSpoolSystem.mo',
        'simulation/openmodelica/PLA_PET_Recycler/Generated.mo',
        'simulation/openmodelica/PLA_PET_Recycler/GeneratedControl.mo',
        'cad/parameters/baseline.json',
        'control/drive_actuation_contract_v0.6.2.1.json',
        'control/process_contract.json',
        'control/fault_response_contract.json',
        'firmware/arduino_mega/src/spooler_control.h',
        'firmware/arduino_mega/src/machine_supervisor.cpp',
        'calculations/run_engineering.py',
        'cad/parameters/final_v08.json',
        'cad/generation/export_modelica_properties.py',
        'simulation/openmodelica/scripts/run_v08_release.mos',
        'simulation/openmodelica/postprocess/validate_v08_release.py',
    }
    assert len(inputs) == len(set(inputs)), "duplicate Modelica provenance input"
    assert set(inputs) == expected_inputs, "Modelica source contract drift"
    assert all((root / path).is_file() for path in inputs), "missing Modelica provenance input"
    assert (root / "simulation/openmodelica/PLA_PET_Recycler/package.mo").is_file()
    code = "import sys; from pathlib import Path; r=Path(sys.argv[1]); sys.path[:0]=[str(r),str(r/'release'),str(r/'validation')]; import build_print_release,v08_release_inventory,v08_full_compliance,build_bom_release,build_electrical_firmware_release,build_final_documents,build_fabrication_release,verify_fabrication_release"
    subprocess.run([sys.executable, "-I", "-c", code, str(root)], cwd=root, check=True)
    thermal_code = "import sys; from pathlib import Path; r=Path(sys.argv[1]); sys.path.insert(0,str(r)); from analysis.thermal_revision_v08.compare import configurations; from analysis.final_validation.hot_zone_revision_review import beam_screen; import release.plain_shaft_drawing; b,m,a,c=configurations(); assert set(c)=={'reference','width_only','support_only','combined'}; assert c['reference'][1][0]==[45,90]"
    subprocess.run([sys.executable, "-I", "-c", thermal_code, str(root)], cwd=root, check=True)
print("PACKAGE_ISOLATED_IMPORT_PASS release_modules=8 thermal_modules=3 modelica_inputs=15; FreeCAD/full runtime validation NOT_PROVEN")
