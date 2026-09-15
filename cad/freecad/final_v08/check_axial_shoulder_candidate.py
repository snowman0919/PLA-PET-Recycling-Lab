#!/usr/bin/env python3
"""일체형 후단 어깨 후보의 축방향 stop 및 조립 간섭 검사. 제작 승인 아님."""

import hashlib
import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from generate import final_objects, one_solid

# Candidate drawing allocations, not measured or released part tolerances.
SPACER_LENGTH_MM = 4.20
LENGTH_TOLERANCE_MM = .02
FACE_FLATNESS_MM = .01
RETAINER_THICKNESS_MM = 4
REAR_RIB_MM = 8


def main():
    objects = final_objects()
    shapes = {item["name"]: item["shape"] for item in objects}
    barrel = shapes["Barrel"].copy()
    collar = shapes["ExtruderFixedCollar"].copy()
    datum = shapes["ExtruderRearFixedDatum"].copy()
    cap = shapes["ExtruderRearRetainer"].copy()
    cap_x = 363 + SPACER_LENGTH_MM + REAR_RIB_MM
    candidates = {name: shapes[name].copy() for name in (
        "Barrel", "ExtruderFixedCollar", "ExtruderRearFixedDatum", "ExtruderRearRetainer",
        "ExtruderRearRetainerSpacer318", "ExtruderRearRetainerSpacer376",
        "RearRetainerM4_318", "RearRetainerM4_376")}
    bolt_centres = [(318, 382), (376, 382)]
    allowed_threads = set()
    for y, _z in bolt_centres:
        bolt_name = f"RearRetainerM4_{y}"
        allowed_threads.update({
            frozenset((bolt_name, "ExtruderRearRetainer")),
            frozenset((bolt_name, "ExtruderRearFixedDatum")),
            frozenset((bolt_name, f"ExtruderRearRetainerSpacer{y}")),
        })
    allowed_threads.update(frozenset(("Barrel", f"TemperatureProbeRetainerT{zone}")) for zone in range(1, 4))
    step_path = ROOT / "analysis/final_validation/input/retainer_candidate.step"
    candidates["ExtruderRearRetainer"].exportStep(str(step_path))
    imported = Part.read(str(step_path))
    assert imported.isValid() and len(imported.Solids) == 1
    assert abs(imported.Volume - cap.Volume) / cap.Volume < 1e-6
    collisions = []
    for name, shape in candidates.items():
        assert shape.isValid() and len(shape.Solids) == 1
        for other, original in (shapes | candidates).items():
            if other == name or other in candidates and other < name:
                continue
            volume = shape.common(candidates.get(other, original)).Volume
            if volume > .01 and frozenset((name, other)) not in allowed_threads:
                collisions.append({"a": name, "b": other, "volume_mm3": volume})
    shifted = barrel.copy()
    shifted.translate(App.Vector(-.01, 0, 0))
    stop_volume = shifted.common(collar).Volume
    contact_gap = barrel.distToShape(collar)[0]
    assert contact_gap < 1e-6 and stop_volume > .01
    motions = []
    for moving_group in ("barrel_only", "barrel_and_collar"):
        for direction, vector in (("positive_x", (1, 0, 0)), ("negative_x", (-1, 0, 0)), ("uplift_z", (0, 0, 1))):
            for distance in (.01, .1, 1.0):
                moved = barrel.copy()
                moved.translate(App.Vector(*(distance * v for v in vector)))
                overlap = moved.common(datum).Volume + moved.common(cap).Volume
                if moving_group == "barrel_only":
                    overlap += moved.common(collar).Volume
                else:
                    moved_collar = collar.copy()
                    moved_collar.translate(App.Vector(*(distance * v for v in vector)))
                    overlap += moved_collar.common(datum).Volume + moved_collar.common(cap).Volume
                motions.append({"moving_group": moving_group, "direction": direction,
                                "distance_mm": distance, "mount_overlap_mm3": overlap,
                                "interference_at_sample": overlap > .01})
    retention_at_1mm = all(row["interference_at_sample"] for row in motions if row["distance_mm"] == 1.0)
    cold_endplay = cap_x - datum.BoundBox.XMax - collar.BoundBox.XLength
    assert abs(cold_endplay - .20) < 1e-6, "candidate endplay differs from allocation"
    cold_endplay_range = [cold_endplay - 3 * LENGTH_TOLERANCE_MM - 2 * FACE_FLATNESS_MM,
                          cold_endplay + 3 * LENGTH_TOLERANCE_MM + 2 * FACE_FLATNESS_MM]
    thermal_strain_bound = 17e-6 * (300 - 20)
    hot_endplay_range = [cold_endplay_range[0] - collar.BoundBox.XLength * thermal_strain_bound,
                         cold_endplay_range[1] + (SPACER_LENGTH_MM + REAR_RIB_MM) * thermal_strain_bound]
    assert hot_endplay_range[0] >= 0 and hot_endplay_range[1] <= .35
    result = {
        "status": "HOLD", "geometry_check": "PASS" if not collisions and retention_at_1mm else "FAIL",
        "sampled_retention_at_1mm": retention_at_1mm,
        "candidate": "ADOPTED_RELEASE_GEOMETRY: integral rear shoulder OD44 x8 flattened at global Z398; collar counterbore OD44.25 x8; shoulder at global X367",
        "barrel_collar_gap_mm": contact_gap, "negative_x_0_01mm_stop_overlap_mm3": stop_volume,
        "unexpected_collisions": collisions,
        "retainer_candidate": "ADOPTED_RELEASE_GEOMETRY: 4 mm web X375.20..379.20 with integral8 mm rear ribs at Y312..322/372..382; two M4x25; OD8/ID4.5 x4.20 spacers; minimum full thread engagement8 mm",
        "retainer_thickness_mm": RETAINER_THICKNESS_MM,
        "minimum_full_thread_engagement_mm": 8.0,
        "retainer_material_requirement": "certified yield >=177.5 MPa at maximum measured service temperature",
        "retainer_front_x_mm": cap_x,
        "retainer_bolt_centres_yz_mm": bolt_centres,
        "axial_tolerance_stack": {
            "datum_back_x_mm": datum.BoundBox.XMax,
            "retainer_front_x_mm": cap_x,
            "capture_span_mm": cap_x - datum.BoundBox.XMax,
            "collar_length_mm": collar.BoundBox.XLength,
            "nominal_collar_endplay_mm": cold_endplay,
            "nominal_flange_retainer_gap_mm": cap_x - barrel.BoundBox.XMax,
            "candidate_length_tolerance_mm": LENGTH_TOLERANCE_MM,
            "candidate_face_flatness_mm": FACE_FLATNESS_MM,
            "worst_case_cold_endplay_mm": cold_endplay_range,
            "cold_stack_basis": "Candidate spacer4.20±0.02 plus integral rib8.00±0.02 minus collar12.00±0.02; two0.01 face/seat allowances. Unadopted, not measured.",
            "worst_case_hot_endplay_mm": hot_endplay_range,
            "thermal_bound": "alpha<=17e-6/K, 20..300 C; independently heat collar-only for minimum and spacer+rib-only for maximum",
            "status": "PASS_RELEASE_DIGITAL",
            "missing_inputs": ["released spacer/collar/flange allocations must be physically inspected"],
            "criterion": "0.00 <= worst-case endplay <= 0.35 mm",
        },
        "retention_motion_samples": motions,
        "retainer_step_sha256": hashlib.sha256(step_path.read_bytes()).hexdigest(),
        "motion_scope": "Sampled translations against rear datum/collar/retainer; not a continuous escape-path proof or a force analysis. Other machine parts cannot be credited as mount restraints.",
        "limitations": ["Release geometry is digitally checked; thread strength is screened separately, while physical preload/contact and tool access remain NOT_RUN.",
                        "Shoulder stress and actual thermal contact require the specified material certificate and physical inspection."],
        "physical_validation_state": "NOT_RUN",
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            Path(__file__).resolve(), HERE / "generate.py", ROOT / "cad/freecad/compact/geometry.py",
            ROOT / "cad/freecad/compact/manufacturing.py", ROOT / "cad/parameters/final_v08.json")},
    }
    out = ROOT / "analysis/final_validation/results/v0.8/axial_shoulder_candidate.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"AXIAL_SHOULDER_CANDIDATE_{result['geometry_check']} collisions={len(collisions)} stop_mm3={stop_volume:.6f}")


if __name__ == "__main__":
    main()
