"""미채택 Ø19 배럴 pilot 후보: 명목 간섭 검사, 열간 밀봉/강도 승인 아님."""
import hashlib
import json
import math
import sys
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
from geometry import down_die_body, down_die_copper_gasket, down_die_breaker_plate
from manufacturing import extruder_barrel


def main():
    pilot_length = .9
    axis = App.Vector(-1, 0, 0)
    barrel = extruder_barrel()
    barrel.rotate(App.Vector(), App.Vector(0, 1, 0), -90)
    barrel.translate(App.Vector(320.5, 0, 0))
    pilot = Part.makeCylinder(9.5, pilot_length, App.Vector(40.5, 0, 0), axis).cut(
        Part.makeCylinder(8.1, pilot_length, App.Vector(40.5, 0, 0), axis))
    barrel = barrel.fuse(pilot).removeSplitter()
    die = down_die_body().cut(Part.makeCylinder(9.525, .9, App.Vector(40, 0, 0), axis))
    gasket = down_die_copper_gasket().cut(Part.makeCylinder(9.6, .5, App.Vector(40.5, 0, 0), axis))
    shapes = {"barrel": barrel, "die": die, "gasket": gasket, "breaker": down_die_breaker_plate()}
    for shape in shapes.values():
        assert shape.isValid() and len(shape.Solids) == 1
    overlaps = {f"{a}/{b}": sa.common(sb).Volume for i, (a, sa) in enumerate(shapes.items())
                for b, sb in list(shapes.items())[i+1:]}
    assert max(overlaps.values()) < 1e-6, overlaps
    moved = die.copy()
    moved.translate(App.Vector(0, .1, 0))
    offset_overlap = moved.common(pilot).Volume
    assert offset_overlap > .001
    compression_cases = []
    # Sensitivity values, not an assumed copper compression specification.
    for thickness in (.53, .5, .4, .3, .25):
        compressed_barrel = barrel.copy()
        compressed_barrel.translate(App.Vector(thickness-.5, 0, 0))
        overlap = compressed_barrel.common(die).Volume
        bottom_gap = .9 + thickness - pilot_length
        engagement = pilot_length - thickness
        assert engagement > 0 and bottom_gap > 0
        assert (overlap < 1e-6) == (bottom_gap >= -1e-9)
        compression_cases.append({"compressed_gasket_thickness_mm":thickness,
                                  "nominal_pilot_bottom_gap_mm":bottom_gap,
                                  "nominal_engagement_mm":engagement,
                                  "barrel_die_overlap_mm3":overlap})
    folder = ROOT / "analysis/final_validation/results/v0.8"
    files = {}
    for name, shape in shapes.items():
        path = folder / f"die_pilot_L0p9_candidate_{name}.step"
        shape.exportStep(str(path))
        restored = Part.read(str(path))
        assert restored.isValid() and len(restored.Solids) == 1
        assert abs(restored.Volume-shape.Volume)/shape.Volume < 1e-6
        files[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    thermal_cases = []
    alpha = 12e-6  # Assumed equal constant alpha; not qualified hot material data.
    for barrel_c, die_c in ((20,20), (270,270), (270,245), (245,270), (270,20), (20,270)):
        gap = (19.05*(1+alpha*(die_c-20))-19*(1+alpha*(barrel_c-20)))/2
        thermal_cases.append({"barrel_c":barrel_c, "die_c":die_c, "radial_gap_mm":gap})
    assert abs(thermal_cases[0]["radial_gap_mm"]-.025) < 1e-12
    assert thermal_cases[4]["radial_gap_mm"] < 0
    original_gasket_area = down_die_copper_gasket().Volume/.5
    candidate_gasket_area = gasket.Volume/.5
    assert 0 < candidate_gasket_area < original_gasket_area
    pressure_n_per_mm2 = 6.0  # Existing blocked-die diagnostic load, not measured pressure.
    original_separation = pressure_n_per_mm2*math.pi*16.2**2/4
    candidate_separation = pressure_n_per_mm2*math.pi*19.2**2/4
    required_retained_clamp = 2*candidate_separation
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN",
              "nominal_mm": {"pilot_od":19, "pilot_length":pilot_length, "die_recess_od":19.05,
                             "die_recess_depth":.9, "gasket_id":19.2, "gasket_thickness":.5,
                             "radial_play":.025, "axial_bottom_gap":.9+.5-pilot_length, "pilot_to_breaker_gap":1.5-pilot_length},
              "overlap_mm3":overlaps, "offset_0_1_mm_pilot_overlap_mm3":offset_overlap,
              "gasket_compression_sensitivity":compression_cases,
              "thermal_fit_sensitivity":{"assumed_alpha_per_k":alpha, "reference_c":20,
                  "cases":thermal_cases,
                  "scope":"Nominal free expansion, no tolerances/constraints. Temperature pairs are diagnostic boundaries, not measured or simulated machine histories."},
              "die_joint_pressure_screen":{
                  "assumed_pressure_mpa":pressure_n_per_mm2,
                  "original_gasket_net_face_area_mm2":original_gasket_area,
                  "candidate_gasket_net_face_area_mm2":candidate_gasket_area,
                  "original_separation_force_n":original_separation,
                  "candidate_separation_force_n":candidate_separation,
                  "force_ratio":candidate_separation/original_separation,
                  "minimum_total_retained_clamp_n_for_pressure_sf_2":required_retained_clamp,
                  "minimum_per_bolt_retained_clamp_n_for_four_equal_bolts":required_retained_clamp/4,
                  "scope":"Conservative pressure penetration to gasket ID; net face area excludes bolt holes. Not gasket seating stress or bolt preload qualification. Do not scale rear mount load without a complete free-body model."},
              "step_sha256": files,
              "limitations":"Unadopted nominal geometry. Machining fit/runout, compressed gasket thickness, thermal differential, sealing land and pressure stress unqualified. No full-assembly or physical approval.",
              "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (Path(__file__).resolve(), ROOT/'cad/freecad/compact/geometry.py', ROOT/'cad/freecad/compact/manufacturing.py')}}
    (folder/'die_pilot_L0p9_candidate.json').write_text(json.dumps(result, indent=2)+'\n')
    print('DIE_PILOT_NOMINAL_GEOMETRY_HOLD', offset_overlap)


if __name__ == '__main__':
    main()
