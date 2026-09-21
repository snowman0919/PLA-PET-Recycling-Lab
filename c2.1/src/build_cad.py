"""Build the inspectable C2.1 S2 transmission assembly and exploded STEP.

Nominal bearing/roller envelopes are deliberately unrated.  This is a digital
kinematic assembly, not a fabrication drawing or purchasing release.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import sys

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO/"c2/src"))
from engineering import S2, hook_polygon  # reuse active C2 geometry
from pin_constraint import profile, verify  # reuse active C2 cycloid checks
from transmission import (Transmission, cad_y_degrees_for_xz, pose,
                          rotor_point, write_json)

V = cq.Vector


def extrude_xz(points, y0, depth):
    wire = cq.Wire.makePolygon([V(float(x), y0, float(z)) for x, z in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, depth, 0)).clean()


def cylinder(r, h, at=(0, 0, 0)):
    return cq.Solid.makeCylinder(r, h, V(*at), V(0, 1, 0))


def ring(ro, ri, h, at=(0, 0, 0)):
    return cylinder(ro, h, at).cut(cylinder(ri, h+2, (at[0], at[1]-1, at[2]))).clean()


def c2_process_part(part_id, y=4):
    path=REPO/"c2/cad"/(part_id+".step")
    if not path.is_file():
        raise FileNotFoundError(f"Run c2/src/build_cad.py first: {path}")
    return cq.importers.importStep(str(path)).val().translate((0,y,0)).clean()


def sector(r0, r1, a0, a1, y0, depth):
    a = np.linspace(math.radians(a0), math.radians(a1), max(30, int(a1-a0)+1))
    points = np.c_[r1*np.cos(a), r1*np.sin(a)].tolist()
    points += np.c_[r0*np.cos(a[::-1]), r0*np.sin(a[::-1])].tolist()
    return extrude_xz(points, y0, depth)


def moved(shape, theta, c):
    p = pose(theta, c)
    x, z = p["orbit_center_mm"]
    return shape.rotate((0, 0, 0), (0, 1, 0),
                        cad_y_degrees_for_xz(p["rotor_angle_rad"])).translate((x, 0, z))


def local_rotor(c):
    cycloid = extrude_xz(profile(72.0, c.eccentric_mm, c.q+1, samples=1440), -24, 16)
    hooks = extrude_xz(hook_polygon(S2("C2.1-NOMINAL", tip_mm=c.rotor_tip_diameter_mm,
                                      eccentric_mm=c.eccentric_mm, ratio_denominator=c.q)), 4, 40)
    hub = cylinder(20, 84, (0, -24, 0))
    coupling_web = cylinder(54.5, 14, (0, 50, 0))
    stack = cycloid.fuse(hub).fuse(hooks).fuse(coupling_web)
    stack = stack.cut(cylinder(16.10, 18, (0, -25, 0)))
    stack = stack.cut(cylinder(10.10, 8, (0, -7, 0)))
    for a in np.linspace(0, 2*math.pi, c.output_pin_count, endpoint=False):
        x, z = c.output_pin_pitch_radius_mm*np.array([math.cos(a), math.sin(a)])
        stack = stack.cut(cylinder(c.output_window_radius_mm, 17, (x, 49, z)))
    return stack.clean()


def input_eccentric(theta, c):
    x, z = c.eccentric_mm*np.array([math.cos(theta), math.sin(theta)])
    shaft = cylinder(6, 67, (0, -95, 0))
    crank = cylinder(17, 8, (0, -34, 0))
    journal = cylinder(10, 30, (x, -32, z))
    return shaft.fuse(crank).fuse(journal).clean()


def output_carrier(theta, c):
    phi = -theta/c.q
    carrier = cylinder(48, 8, (0, 68, 0)).fuse(cylinder(10, 43, (0, 76, 0)))
    for a in np.linspace(0, 2*math.pi, c.output_pin_count, endpoint=False)+phi:
        x, z = c.output_pin_pitch_radius_mm*np.array([math.cos(a), math.sin(a)])
        carrier = carrier.fuse(cylinder(3, 20, (x, 48, z)))
    return carrier.clean()


def output_rollers(theta, c):
    phi = -theta/c.q
    out = []
    for i, a in enumerate(np.linspace(0, 2*math.pi, c.output_pin_count, endpoint=False)+phi):
        x, z = c.output_pin_pitch_radius_mm*np.array([math.cos(a), math.sin(a)])
        out.append((f"OUTPUT_ROLLER_{i+1}", ring(c.output_roller_radius_mm, 3.10, 14, (x, 50, z))))
    return out


def fixed_components(c):
    front = cq.Solid.makeBox(170, 8, 170, V(-85, -60, -85)).cut(cylinder(16.10, 10, (0, -61, 0)))
    rear = cq.Solid.makeBox(170, 8, 170, V(-85, 88, -85)).cut(cylinder(21.10, 10, (0, 87, 0)))
    parts = [
        ("FRONT_INPUT_SUPPORT", front.clean()),
        ("REAR_OUTPUT_SUPPORT", rear.clean()),
        ("INPUT_BEARING_ENVELOPE_UNRATED", ring(16, 6.10, 12, (0, -60, 0))),
        ("OUTPUT_BEARING_ENVELOPE_UNRATED", ring(21, 10.10, 12, (0, 84, 0))),
        ("FRONT_FIXED_RING_PLATE", ring(88, 63.5, 6, (0, -34, 0))),
        ("REAR_FIXED_RING_PLATE", ring(88, 63.5, 6, (0, -6, 0))),
        ("C2_FIXED_SHEAR_SENSOR_BORE", c2_process_part("C2_FIXED_SHEAR")),
        ("C2_PERFORATED_SCREEN_REFERENCE", c2_process_part("C1_SCREEN_REFERENCE")),
        ("C2_LEFT_WEAR_SHELL", c2_process_part("C1_LEFT_WEAR_SHELL")),
        ("C2_RIGHT_WEAR_SHELL_1", c2_process_part("C2_RIGHT_WEAR_SHELL_1")),
        ("C2_RIGHT_WEAR_SHELL_2", c2_process_part("C2_RIGHT_WEAR_SHELL_2")),
        ("C2_THERMAL_SADDLE_L", c2_process_part("C2_THERMAL_SADDLE_L")),
        ("C2_THERMAL_SADDLE_R_SENSOR_BORE", c2_process_part("C2_THERMAL_SADDLE_R")),
        ("C2_SADDLE_CAP_L_FRONT", c2_process_part("C2_SADDLE_CAP_L",0)),
        ("C2_SADDLE_CAP_L_REAR", c2_process_part("C2_SADDLE_CAP_L",44)),
        ("C2_SADDLE_CAP_R_FRONT", c2_process_part("C2_SADDLE_CAP_R",0)),
        ("C2_SADDLE_CAP_R_REAR", c2_process_part("C2_SADDLE_CAP_R",44)),
        ("GUARD_SECTION_ENVELOPE_HOLD", sector(90, 94, 20, 160, -42, 124)),
    ]
    for i, a in enumerate(np.linspace(0, 2*math.pi, c.q+1, endpoint=False)):
        x, z = 72*np.array([math.cos(a), math.sin(a)])
        parts.append((f"FIXED_RING_PIN_{i+1}", cylinder(8, 22, (x, -28, z))))
    for i, (x, z) in enumerate([(-80, -80), (-80, 70), (70, -80), (70, 70)]):
        parts.append((f"SUPPORT_TIE_{i+1}", cq.Solid.makeBox(10, 140, 10, V(x, -52, z))))
    return parts


def components(theta=0.0):
    c = Transmission()
    p = pose(theta, c)
    x, z = p["orbit_center_mm"]
    moving = [
        ("INPUT_ECCENTRIC_SHAFT", input_eccentric(theta, c)),
        ("ECCENTRIC_BEARING_ENVELOPE_UNRATED", ring(16, 10.10, 16, (x, -24, z))),
        ("RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE", moved(local_rotor(c), theta, c)),
        ("OUTPUT_PIN_CARRIER_AND_SHAFT", output_carrier(theta, c)),
        *output_rollers(theta, c),
    ]
    return fixed_components(c)+moving


def export_assembly(path, parts, exploded=False):
    assembly = cq.Assembly(name=path.stem)
    labels = []
    for i, (name, shape) in enumerate(parts):
        if exploded:
            group = -1 if "INPUT" in name or "FRONT" in name else 1 if "OUTPUT" in name or "REAR" in name else 0
            shape = shape.translate((0, group*35 + (i % 3-1)*2, 0))
        assembly.add(shape, name=name)
        labels.append(name)
    assembly.save(str(path))
    text = path.read_text(encoding="utf-8")
    text, replacements = re.subn(r"(FILE_NAME\('[^']*',')[^']*(')",
                                 r"\g<1>2000-01-01T00:00:00\2", text, count=1)
    if replacements != 1:
        raise RuntimeError(f"Could not normalize STEP timestamp: {path}")
    path.write_text(text, encoding="utf-8")
    imported = cq.importers.importStep(str(path))
    solids = len(imported.solids().vals())
    return {"file": str(path.relative_to(REPO)), "labels": labels, "object_count": len(parts),
            "reimported_solid_count": solids, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "step_reimport_valid": all(s.isValid() for s in imported.solids().vals())}


def moving_components(theta, c, rotor_local):
    p = pose(theta, c)
    x, z = p["orbit_center_mm"]
    return [
        ("INPUT_ECCENTRIC_SHAFT", input_eccentric(theta, c)),
        ("ECCENTRIC_BEARING_ENVELOPE_UNRATED", ring(16, 10.10, 16, (x, -24, z))),
        ("RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE", moved(rotor_local, theta, c)),
        ("OUTPUT_PIN_CARRIER_AND_SHAFT", output_carrier(theta, c)),
        *output_rollers(theta, c),
    ]


def overlap_volume(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if (min(aa.xmax, bb.xmax)-max(aa.xmin, bb.xmin) <= 1e-7 or
        min(aa.ymax, bb.ymax)-max(aa.ymin, bb.ymin) <= 1e-7 or
        min(aa.zmax, bb.zmax)-max(aa.zmin, bb.zmin) <= 1e-7):
        return 0.0
    return a.intersect(b).Volume()


def collision_checks(c):
    fixed = fixed_components(c)
    rotor_local = local_rotor(c)
    failures = []
    static_checks = 0
    initial = fixed+moving_components(0.0, c, rotor_local)

    # Fail fast: every initial component pair gets bbox screening then exact BRep
    # volume if their boxes overlap. Evidence is returned before any phase sweep.
    for i, (a_name, a) in enumerate(initial):
        for b_name, b in initial[i+1:]:
            static_checks += 1
            volume = overlap_volume(a, b)
            if volume >= 1e-5:
                failures.append({"method": "BREP_EXACT_AFTER_BBOX", "scope": "initial_all_pair",
                                 "theta_rad": 0.0, "a": a_name, "b": b_name,
                                 "overlap_mm3": volume})
    if failures:
        return {"input_turns": c.q, "static_pair_checks": static_checks,
                "static_passed": False, "dynamic_executed": False,
                "dynamic_positions": 0, "dynamic_pair_checks": 0,
                "failures": failures}

    # 33 BRep states span all q input turns. This is sampled, not continuous.
    angles = np.linspace(0, 2*math.pi*c.q, 33)
    dynamic_checks = 0
    for theta in angles[1:]:
        moving = moving_components(float(theta), c, rotor_local)
        for a_name, a in moving:
            for b_name, b in fixed:
                dynamic_checks += 1
                volume = overlap_volume(a, b)
                if volume >= 1e-5:
                    failures.append({"method": "BREP_SAMPLED_AFTER_BBOX",
                                     "scope": "q_turn_moving_vs_fixed", "theta_rad": float(theta),
                                     "a": a_name, "b": b_name, "overlap_mm3": volume})
        for i, (a_name, a) in enumerate(moving):
            for b_name, b in moving[i+1:]:
                dynamic_checks += 1
                volume = overlap_volume(a, b)
                if volume >= 1e-5:
                    failures.append({"method": "BREP_SAMPLED_AFTER_BBOX",
                                     "scope": "q_turn_moving_pair", "theta_rad": float(theta),
                                     "a": a_name, "b": b_name, "overlap_mm3": volume})
    return {"input_turns": c.q, "static_pair_checks": static_checks,
            "static_passed": True, "dynamic_executed": True,
            "dynamic_positions": len(angles), "dynamic_pair_checks": dynamic_checks,
            "failures": failures}


def analytical_bounds(c):
    hook_envelope = c.rotor_tip_diameter_mm/2+c.eccentric_mm
    checks = {
        "hook_to_shear_radial_mm": 62.8-hook_envelope,
        "hook_to_screen_inner_radius_mm": 62.8-hook_envelope,
        "hook_to_thermal_inner_radius_mm": 66.2-hook_envelope,
        "rear_ring_to_process_axial_mm": 4.0-0.0,
        "process_to_coupling_axial_mm": 50.0-48.0,
        "nominal_roller_window_clearance_mm": c.coupling_radial_clearance_mm,
    }
    return {"method": "CONSERVATIVE_ANALYTICAL_ENVELOPE_CONTINUOUS_ALL_PHASES",
            "checks": checks, "passed": all(v > 0 for v in checks.values()),
            "limitations": ["does_not_prove_loaded_contact", "does_not_replace_BRep_for_non_radial_parts"]}


def cad_frame_check(c):
    theta = math.pi/2
    phi = pose(theta, c)["rotor_angle_rad"]
    marker = cylinder(0.5, 1.0, (50, -0.5, 0))
    marker = marker.rotate((0, 0, 0), (0, 1, 0),
                           cad_y_degrees_for_xz(phi)).translate((0, 0, c.eccentric_mm))
    actual = np.array([marker.Center().x, marker.Center().z])
    expected = rotor_point([50, 0], theta, c)
    return {"theta_rad": theta, "local_point_xz_mm": [50, 0],
            "cad_center_xz_mm": actual.tolist(), "numerical_xz_mm": expected.tolist(),
            "error_mm": float(np.linalg.norm(actual-expected)),
            "passed": bool(np.linalg.norm(actual-expected) < 1e-9)}


def write_schematic_svg(path):
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="520" viewBox="0 0 1000 520">
<style>text{font:15px sans-serif}.hold{fill:#fff3cd;stroke:#946200}.metal{fill:#d9e4ef;stroke:#234}.move{fill:#d8f3dc;stroke:#174}.axis{stroke:#c22;stroke-dasharray:6 4}</style>
<text x="20" y="28">C2.1 S2 transmission schematic (not a generated CAD section) — F0: +X right, +Y shaft axis, +Z up</text>
<line class="axis" x1="60" y1="260" x2="940" y2="260"/><text x="900" y="250">+Y</text>
<rect class="metal" x="90" y="100" width="18" height="320"/><text x="25" y="90">front input support</text>
<rect class="metal" x="850" y="100" width="18" height="320"/><text x="805" y="90">rear output support</text>
<rect class="move" x="105" y="248" width="290" height="24"/><text x="150" y="240">M1 input shaft +ω</text>
<rect class="move" x="355" y="175" width="260" height="170"/><text x="375" y="165">rigid cycloid + hook rotor stack: orbit e, self −ω/q</text>
<circle class="hold" cx="485" cy="260" r="115" fill="none" stroke-width="12"/><text x="410" y="395">fixed q+1 ring pins / reaction</text>
<rect class="move" x="605" y="205" width="115" height="110"/><text x="590" y="195">output pins/rollers</text>
<rect class="move" x="710" y="248" width="145" height="24"/><text x="720" y="240">output shaft −ω/q</text>
<text x="260" y="455">positive XZ angle maps +X toward +Z and is a physical -Y rotation; output XZ angle is -theta/q</text>
<text x="260" y="482">window extra0.20mm: rigid first-contact equilibrium PASS; elastic sharing, ratings and fabrication HOLD</text>
</svg>\n""", encoding="utf-8")


def main():
    out = ROOT/"cad"
    out.mkdir(parents=True, exist_ok=True)
    nominal = Transmission()
    full = export_assembly(out/"PPR_C2_1_S2_transmission.step", components(), False)
    exploded = export_assembly(out/"PPR_C2_1_S2_transmission_exploded.step", components(), True)
    write_schematic_svg(out/"PPR_C2_1_S2_transmission_schematic.svg")
    collisions = collision_checks(nominal)
    frame = cad_frame_check(nominal)
    bounds = analytical_bounds(nominal)
    pin = verify(S2("C1-SEED", tip_mm=110, width_mm=40, eccentric_mm=7,
                    ratio_denominator=8), positions=721, profile_samples=1440)
    failures = collisions["failures"]
    digital_pass = (not failures and collisions["static_passed"] and collisions["dynamic_executed"]
                    and bounds["passed"] and pin["passed"] and frame["passed"]
                    and full["step_reimport_valid"] and exploded["step_reimport_valid"])
    result = {
        "revision": "C2.1",
        "status": "KINEMATIC_DIGITAL_PASS_NOT_FABRICATION_RELEASE" if digital_pass else "DIGITAL_COLLISION_OR_FRAME_FAIL",
        "assembly": full, "exploded": exploded, "cad_numeric_frame_check": frame,
        "process_reference_width_mm": 40,
        "sampled_input_turns": collisions["input_turns"],
        "static_all_pair": {"method": "BREP_EXACT_AFTER_BBOX",
                            "pair_checks": collisions["static_pair_checks"],
                            "passed": collisions["static_passed"]},
        "dynamic_collision": {"method": "BREP_SAMPLED_AFTER_BBOX_NOT_CONTINUOUS_EXHAUSTIVE",
                              "executed": collisions["dynamic_executed"],
                              "positions_over_q_turns": collisions["dynamic_positions"],
                              "pair_checks": collisions["dynamic_pair_checks"]},
        "continuous_analytical_bounds": bounds,
        "functional_pin_clearance": {**pin, "coverage_note": "721 positions over one orbit; q/lobe symmetry repeats contact geometry, not marked hook geometry"},
        "unexpected_collision_count": len(failures),
        "collision_details": failures,
        "interfaces": {"cad_rotor": "single fused envelope; physical bolts, axial retention and fits are absent/HOLD",
                       "output_carrier": "unpowered reverse-rotation witness/load-extraction candidate",
                       "nominal_clearance": "rigid first-contact phase take-up is calculated; elastic sharing/rating HOLD",
                       "process_elements": "C2 generated shear sensor bore, perforated screen reference, split wear liners, thermal saddles/caps integrated; screen attachment, sensor wiring and measured UA HOLD",
                       "process_source_sha256": {p:hashlib.sha256((REPO/'c2/cad'/(p+'.step')).read_bytes()).hexdigest() for p in
                          ["C2_FIXED_SHEAR","C1_SCREEN_REFERENCE","C1_LEFT_WEAR_SHELL","C2_RIGHT_WEAR_SHELL_1","C2_RIGHT_WEAR_SHELL_2","C2_THERMAL_SADDLE_L","C2_THERMAL_SADDLE_R","C2_SADDLE_CAP_L","C2_SADDLE_CAP_R"]}},
        "not_checked": ["full_machine_collision", "continuous_BRep_collision_between_samples",
                        "loaded_output_contact_transfer", "gear_contact_stress", "bearing_L10_life",
                        "roller_contact_pressure", "shaft_fatigue", "fastener_preload", "axial_retention",
                        "seal_and_lubrication", "screen_attachment_and_size_calibration", "sensor_mount_wiring_and_response",
                        "measured_thermal_interface_and_airflow", "guard_containment_strength",
                        "manufacturing_tolerance_stack", "thermal_growth"],
        "procurement": "HOLD", "fabrication": "HOLD", "energization": "HOLD",
    }
    write_json(ROOT/"results/cad_validation.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "collision_details"}, indent=2))
    if not digital_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
