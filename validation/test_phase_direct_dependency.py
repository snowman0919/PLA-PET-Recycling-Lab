import json, hashlib, tempfile, importlib.util, contextlib, io
from pathlib import Path

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fixture_check(source):
    with tempfile.TemporaryDirectory(prefix="ppr-phase-regression-") as directory:
        root = Path(directory)
        script = root / "validation/check_phase_path_25_evidence.py"
        script.parent.mkdir()
        script.write_text(source)
        out = root / "analysis/final_validation/results/v0.8"
        out.mkdir(parents=True)
        common = root / "common_fixture.txt"
        common.write_text("synthetic fixed contract")
        phase_basis = root / "phase_basis.txt"
        phase_basis.write_text("synthetic phase basis")
        bindings = {common.name: digest(common)}
        geometry = dict(status="PASS", nominal_geometry_check="PASS",
            cutter_matched_keyway_width_mm=6.0075, gear_matched_keyway_width_mm=8.0075,
            gear_key_nominal_mm=[8.0,7.0], gear_root_fillet_mm=1.0,
            cad_pair_backlash_target_mm=.125,
            bearing=dict(static_rating_ratio=3, two_shaft_worst_relative_clearance_mm=.005))
        twist = dict(rotation_within_5_percent=True, meshes=[dict(tip_rotation_deg=.04)])
        gear = dict(torque_nm=34, gear_piece_count=1, face_width_mm=18, status="HOLD",
            conditional_sf_at_355_mpa=2.5, peak_stress_relative_mesh_change=.02,
            conditional_strength_screen="PASS", two_gear_elastic_angle_deg=.04)
        pair = dict(cad_pair_backlash_bound_mm=[.12,.14])
        for name, data in [("phase_path_25_candidate.json",geometry),
                ("torsion_load_path_25_153.json",twist), ("torsion_load_path_25_105.json",twist),
                ("phase_gear_elastic_candidate.json",gear), ("phase_pair_backlash_candidate.json",pair)]:
            (out/name).write_text(json.dumps(dict(data, source_sha256=bindings)))
        section = out / "phase_section_sensitivity.json"
        section_data = dict(source_sha256={phase_basis.name:digest(phase_basis)},
            diameter25_candidate=dict(meshes=[dict(backlash_angle_deg=.3)],
                four_matched_key_interfaces_peak_to_peak_deg=.25, criterion_deg=1.0))
        section.write_text(json.dumps(section_data))
        spec = importlib.util.spec_from_file_location("phase_under_test", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with contextlib.redirect_stdout(io.StringIO()): module.main()
        result_path = out / "phase_path_25_qualification.json"
        result = json.loads(result_path.read_text())
        def current():
            return bool(result["source_sha256"]) and all((root/p).is_file()
                and digest(root/p)==h for p,h in result["source_sha256"].items())
        baseline = result["status"]=="PASS" and current()
        section_data["diameter25_candidate"]["four_matched_key_interfaces_peak_to_peak_deg"] = .26
        section.write_text(json.dumps(section_data))
        stale_result_accepted = current()
        section_data["diameter25_candidate"]["four_matched_key_interfaces_peak_to_peak_deg"] = .25
        section.write_text(json.dumps(section_data))
        phase_basis.write_text("changed unqualified phase basis")
        result_path.unlink()
        try:
            with contextlib.redirect_stdout(io.StringIO()): module.main()
        except AssertionError:
            stale_basis_rejected = True
        else:
            stale_basis_rejected = False
        return dict(baseline_pass=baseline, stale_result_accepted=stale_result_accepted,
            stale_basis_rejected=stale_basis_rejected,
            emitted_result_after_bad_basis=result_path.exists())

def test_phase_direct_dependency():
    source = Path(__file__).with_name("check_phase_path_25_evidence.py").read_text()
    result = fixture_check(source)
    assert result["baseline_pass"]
    assert not result["stale_result_accepted"]
    assert result["stale_basis_rejected"]
    assert not result["emitted_result_after_bad_basis"]

if __name__ == "__main__":
    test_phase_direct_dependency()
    print("PHASE_DIRECT_DEPENDENCY_REGRESSION_PASS scope=SYNTHETIC_CONTRACT")
