"""Bounded, non-qualifying structural and thermal screen for VP1 hardware.

Run: python3 c2.1/src/structural_screen.py
All stresses use N/mm2 (MPa), E uses MPa, lengths use mm.  These are
transparent hand-calculation proxies, not a measured load case, FEA, guard
rating, supplier extrusion section, fastener approval or fabrication release.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "c2.1/results/structural_screen.json"


def source(path):
    data = (REPO / path).read_bytes()
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest()}


def source_dict(path):
    return json.loads((REPO / path).read_text(encoding="utf-8"))


def literal_dict_assignment(path, name):
    """Read dimension constants without importing CadQuery or regenerating CAD."""
    tree = ast.parse((REPO / path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "dict":
                return {kw.arg: ast.literal_eval(kw.value) for kw in node.value.keywords}
    raise ValueError(f"{path}: literal dict {name} not found; inspect changed geometry")

def flange_thickness(path):
    """Read the actual annulus thickness in _flange, failing on changed CAD."""
    tree = ast.parse((REPO / path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_flange":
            constants = {}
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    try:
                        constants[stmt.targets[0].id] = float(ast.literal_eval(stmt.value))
                    except (ValueError, TypeError):
                        pass
                if (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == "_cyl"):
                    arg = stmt.value.args[1]
                    if isinstance(arg, ast.Name) and arg.id in constants:
                        return constants[arg.id]
                    return float(ast.literal_eval(arg))
    raise ValueError(f"{path}: _flange thickness cannot be read; revise screen")



def bending_point(force, length, width, thickness, E, mode="cantilever"):
    I = width * thickness**3 / 12
    if mode == "cantilever":
        moment = force * length
        delta = force * length**3 / (3 * E * I)
    elif mode == "simple_midspan":
        moment = force * length / 4
        delta = force * length**3 / (48 * E * I)
    else:
        raise ValueError(mode)
    return {"I_mm4": I, "moment_Nmm": moment, "stress_MPa": moment * thickness / (2 * I),
            "deflection_mm": delta}


def strip_pressure(pressure_MPa, span, width, thickness, E, mode):
    # Equivalent uniform transverse line force on the whole width.
    force = pressure_MPa * span * width
    I = width * thickness**3 / 12
    if mode == "cantilever":
        moment, delta = force * span / 2, force * span**3 / (8 * E * I)
    else:
        moment, delta = force * span / 8, 5 * force * span**3 / (384 * E * I)
    return {"force_N": force, "I_mm4": I, "moment_Nmm": moment,
            "stress_MPa": moment * thickness / (2 * I), "deflection_mm": delta}


def margin(limit, demand):
    return None if demand <= 0 else round(limit / demand, 3)


def case(name, model, geometry, load, limits, computed, dependencies=(), decision="HOLD", note=""):
    return {"name": name, "model": model, "geometry": geometry, "load": load,
            "limits": limits, "computed": computed, "decision": decision,
            "unmeasured_dependencies": list(dependencies), "note": note}


def screen():
    assembly_path = "design/assembly.json"
    winder_path = "c2.1/src/winder.py"
    bom_path = "c2.1/bom/vp1_bom_delta.csv"
    assembly = source_dict(assembly_path)["parts"]
    params = source_dict("design/parameters.json")
    wind = literal_dict_assignment(winder_path, "WIND")
    pull = literal_dict_assignment(winder_path, "PULL")
    flange_actual_mm = flange_thickness(winder_path)
    lid = assembly["HOP-LID"]["adds"][0]["size"]
    deck = assembly["DRV-DECK"]["adds"][0]["size"]
    foot = assembly["DRV-M1-FOOT"]["adds"][0]["size"]
    # The lower 15 mm octagonal neck is straight; screen the separate
    # inclined neck-to-mouth span, not the full three-loop loft as one taper.
    buf = assembly["FEED-BUF"]["adds"][0]["loops"][-2:]
    hopper = assembly["HOPPER"]["adds"][0]["loops"]
    zbuf = buf[1][0][2] - buf[0][0][2]
    zhop = hopper[1][0][2] - hopper[0][0][2]
    top_buffer = max(p[0] for p in buf[1]) - min(p[0] for p in buf[1])
    hopper_top = max(p[0] for p in hopper[1]) - min(p[0] for p in hopper[1])
    if lid != [180, 140, 5] or deck != [240, 194, 5] or foot[0] != 70 or wind["flange_r"] != 100:
        raise ValueError("Structural model datums changed: revise load paths before screening")
    if zbuf <= 0 or zhop <= 0 or top_buffer <= 0:
        raise ValueError("Enclosure loops have invalid dimensions")

    # Screening values are assumptions at room temperature, NOT supplier
    # minimum design allowables. Long-term/temperature and printed Z values
    # are handled separately, never represented as certified strengths.
    E = {"steel": 210000., "aluminum": 69000., "PC": 2300., "ABS": 2000., "PLA": 3200.}
    allowable = {"steel": 120., "aluminum": 70., "PC": 18., "ABS": 13., "PLA": 16.}
    cases = []
    def add(*args, **kw):
        cases.append(case(*args, **kw))

    # Bulk pressure is a deliberately bounded process assumption, not a
    # measured arching/impact pressure. p = 0.5 kPa; 5 kPa upset sensitivity.
    buf_wall = 3.0  # mouth width difference; neck radius wall is 9-6.5=2.5
    inner_buf = assembly["FEED-BUF"]["cuts"][0]["loops"][-2:]
    if abs((top_buffer - (max(p[0] for p in inner_buf[1]) -
                               min(p[0] for p in inner_buf[1]))) / 2 - buf_wall) > 1e-6:
        raise ValueError("Buffer nominal wall thickness changed")
    # The long +/-Y panels incline slightly. The inner mouth extends 1 mm
    # above the outer mouth, reducing the same-z throat wall thickness.
    y_outer_bottom, y_outer_top = max(p[1] for p in buf[0]), max(p[1] for p in buf[1])
    y_inner_bottom, y_inner_top = max(p[1] for p in inner_buf[0]), max(p[1] for p in inner_buf[1])
    y_inner_slope = (y_inner_top-y_inner_bottom)/(inner_buf[1][0][2]-inner_buf[0][0][2])
    y_run = y_outer_top-y_outer_bottom
    y_slant = math.hypot(zbuf,y_run)
    y_projected_throat = y_outer_bottom - (y_inner_bottom+(buf[0][0][2]-inner_buf[0][0][2])*y_inner_slope)
    y_projected_top = y_outer_top - (y_inner_bottom+(buf[1][0][2]-inner_buf[0][0][2])*y_inner_slope)
    y_t_throat, y_t_top = (d*zbuf/y_slant for d in (y_projected_throat,y_projected_top))
    for p_kPa in (0.5, 5.0):
        v = strip_pressure(p_kPa / 1000, y_slant, top_buffer, y_t_throat, E["PC"], "cantilever")
        v["stress_margin_to_room_assumption"] = margin(allowable["PC"], v["stress_MPa"])
        v["deflection_margin_to_span_over_100"] = margin(y_slant / 100, v["deflection_mm"])
        add(f"FEED-BUF wall {p_kPa:g} kPa", "long near-vertical panel cantilever at uniform minimum throat normal thickness; top free/bottom fully fixed",
            {"part": "FEED-BUF", "vertical_height_mm":zbuf, "slant_span_mm":y_slant,
             "strip_width_mm":top_buffer, "nominal_wall_mm":buf_wall,
             "normal_thickness_throat_mm":y_t_throat, "normal_thickness_top_mm":y_t_top,
             "source": "design/assembly.json FEED-BUF outer/inner lofts"},
            {"pressure_kPa": p_kPa, "type": "assumed bulk static/upset envelope, excludes bridging and impacts"},
            {"stress_MPa": allowable["PC"], "deflection_mm": y_slant / 100}, v,
            ["actual feed mass/bridging/impact", "metal throat joint and wall fixture", "PC grade/process/temperature"],
            decision="REJECT_ASSUMED_DEFLECTION" if v["deflection_mm"] > y_slant/100 else "HOLD",
            note="Strip ignores corner restraint and is not a containment or burst calculation.")
    # The x-facing frustum panels incline from neck to mouth. The cut loft
    # over-runs the upper plane by 1 mm, so compare wall offsets at the
    # same z before projecting thickness normal to the outer panel.
    x_outer_bottom, x_outer_top = max(p[0] for p in buf[0]), max(p[0] for p in buf[1])
    x_inner_bottom, x_inner_top = max(p[0] for p in inner_buf[0]), max(p[0] for p in inner_buf[1])
    inner_slope = (x_inner_top-x_inner_bottom)/(inner_buf[1][0][2]-inner_buf[0][0][2])
    projected_throat = x_outer_bottom - (x_inner_bottom + (buf[0][0][2]-inner_buf[0][0][2])*inner_slope)
    projected_top = x_outer_top - (x_inner_bottom + (buf[1][0][2]-inner_buf[0][0][2])*inner_slope)
    slope_run = x_outer_top-x_outer_bottom
    slant = math.hypot(zbuf, slope_run)
    normal_factor = zbuf/slant
    t_throat, t_top, t_nominal = (v*normal_factor for v in (projected_throat, projected_top, buf_wall))
    if min(t_throat, t_top) <= 0:
        raise ValueError("Buffer inclined panel has no positive wall")
    for p_kPa in (0.5, 5.0):
        v = strip_pressure(p_kPa/1000, slant, 48., t_throat, E["PC"], "cantilever")
        nominal = strip_pressure(p_kPa/1000, slant, 48., t_nominal, E["PC"], "cantilever")
        v["nominal_3mm_projected_proxy"] = nominal
        v["stress_margin_to_room_assumption"] = margin(allowable["PC"], v["stress_MPa"])
        v["deflection_margin_to_slant_over_100"] = margin(slant/100, v["deflection_mm"])
        add(f"FEED-BUF inclined x-wall {p_kPa:g} kPa", "inclined-panel generator cantilever, worst throat normal thickness applied uniformly; deliberately pessimistic strip, no corner/membrane stiffness",
            {"part":"FEED-BUF", "slant_span_mm":slant, "vertical_height_mm":zbuf,
             "x_run_mm":slope_run, "nominal_panel_width_mm":48.,
             "horizontal_offset_at_throat_mm":projected_throat, "horizontal_offset_at_top_mm":projected_top,
             "normal_thickness_throat_mm":t_throat, "normal_thickness_top_mm":t_top,
             "source":"design/assembly.json FEED-BUF inclined outer neck z15..73 and cut z15..74"},
            {"pressure_kPa":p_kPa, "type":"assumed uniform normal bulk pressure, corner/membrane action omitted"},
            {"stress_MPa":allowable["PC"], "deflection_mm":slant/100}, v,
            ["real tapered-shell stiffness and corner joints", "bulk force/impact",
             "metal throat and any external rib anchors", "PC process/print direction"],
            decision="REJECT_ASSUMED_PRESSURE_WITHOUT_STIFFENING" if v["deflection_mm"] > slant/100 else "HOLD",
            note="Uniform minimum thickness is a conservative geometry bound, NOT an exact variable-section shell solution.")
    z80_limit = 55*.45*.35/3  # illustrative printed PC Z-axis at 80 C
    pressure_case = next(c for c in cases if c["name"] == "FEED-BUF inclined x-wall 5 kPa")
    worst = pressure_case["computed"]
    long_case = next(c for c in cases if c["name"] == "FEED-BUF wall 5 kPa")["computed"]
    def sizes(delta, stress, span, thickness):
        deflection_limit = span/100
        max_deflection_span = span*(deflection_limit/delta)**(1/3)
        max_creep_span = span*math.sqrt(z80_limit/stress)
        max_span = min(max_deflection_span, max_creep_span)
        return {"minimum_thickness_mm_for_deflection":thickness*(delta/deflection_limit)**(1/3),
                "minimum_thickness_mm_for_80C_Z_stress":thickness*math.sqrt(stress/z80_limit),
                "max_anchored_cantilever_span_mm_for_deflection":max_deflection_span,
                "max_anchored_cantilever_span_mm_for_80C_Z_stress":max_creep_span,
                "required_equal_spans_at_80C_Z":math.ceil(span/max_span)}
    x_worst_sizing = sizes(worst["deflection_mm"],worst["stress_MPa"],slant,t_throat)
    x_segments = x_worst_sizing["required_equal_spans_at_80C_Z"]
    steel_liner = strip_pressure(5/1000, slant, 48., 2., E["steel"], "cantilever")
    steel_liner["stress_margin_to_assumed_120MPa"] = margin(allowable["steel"],steel_liner["stress_MPa"])
    steel_liner["deflection_margin_to_slant_over_100"] = margin(slant/100,steel_liner["deflection_mm"])
    reinforcement = {
        "basis":"5 kPa pressure, E_PC=2300 MPa, deflection <= EACH unsupported span/100, illustrative 80C long-term PC Z screen limit; every ring must be radially anchored to metal frame and restore a fully fixed boundary, not a floating hoop",
        "80C_Z_stress_limit_MPa":z80_limit,
        "near_vertical_long_y_face":sizes(long_case["deflection_mm"],long_case["stress_MPa"],y_slant,y_t_throat),
        "inclined_x_face_uniform_nominal_3mm_horizontal_offset":sizes(
            worst["nominal_3mm_projected_proxy"]["deflection_mm"],
            worst["nominal_3mm_projected_proxy"]["stress_MPa"],slant,t_nominal),
        "inclined_x_face_uniform_minimum_throat_thickness_bound":x_worst_sizing,
        "inclined_x_face_required_horizontal_offset_at_all_heights_mm":
            max(x_worst_sizing["minimum_thickness_mm_for_deflection"],
                x_worst_sizing["minimum_thickness_mm_for_80C_Z_stress"])/normal_factor,
        "worst_bound_ideal_intermediate_ring_z_mm":[i*zbuf/x_segments for i in range(1,x_segments)],
        "alternative_continuous_2mm_steel_load_bearing_liner":{
            "source":"proposed, NOT present in current CAD/BOM",
            "strip_span_mm":slant, "thickness_mm":2., "pressure_kPa":5.,
            "computed":steel_liner, "decision":"HOLD metal-throat attachment, corrosion/thermal and enclosure joint qualification"},
        "caveat":"Real taper, perforation/metal rim, support stiffness, attachment pullout, thermal gradient and impact require physical coupons/structural validation. Thickening x faces reduces inner throat width and may block flow; 210-mm printer XY only bounds outer 190-mm mouth, not joint adequacy."}

    hopper_wall = 3.0  # outer/inset lofts, nominal 3 mm; inclined section not plate-supported
    v = strip_pressure(0.5 / 1000, hopper_top, zhop, hopper_wall, E["PC"], "simple")
    v["stress_margin_to_room_assumption"] = margin(allowable["PC"], v["stress_MPa"])
    v["deflection_margin_to_span_over_100"] = margin(hopper_top / 100, v["deflection_mm"])
    add("HOPPER broad wall", "simply-supported horizontal strip across 180-mm top mouth, uniform outward lateral pressure",
        {"part": "HOPPER", "top_span_mm": hopper_top, "strip_height_mm": zhop, "nominal_wall_mm": hopper_wall,
         "source": "design/assembly.json HOPPER loft; thickness near inclined faces is not uniform"},
        {"pressure_kPa": 0.5, "type": "assumed bulk pressure, NOT impact or reach-in load"},
        {"stress_MPa": allowable["PC"], "deflection_mm": hopper_top / 100}, v,
        ["inclined/split joint stiffness", "actual hopper charge and bridging", "liner attachment/impact", "PC print orientation"],
        note="The width is <=210 mm but the inclined/vertical wall span exceeds 210 mm; split panels, join and validate. No access safety conclusion.")
    for F in (25., 100.):
        v = bending_point(F, lid[1], lid[0], lid[2], E["PC"], "simple_midspan")
        v["stress_margin_to_room_assumption"] = margin(allowable["PC"], v["stress_MPa"])
        v["deflection_margin_to_span_over_100"] = margin(lid[1] / 100, v["deflection_mm"])
        add(f"HOP-LID {F:g} N", "full 180-mm strip simply supported on opposite edges, central point load (not a hand-force rating)",
            {"part": "HOP-LID", "width_mm": lid[0], "span_mm": lid[1], "thickness_mm": lid[2]},
            {"central_force_N": F, "type": "assumed incidental/process load; impact and deliberate human force excluded"},
            {"stress_MPa": allowable["PC"], "deflection_mm": lid[1] / 100}, v,
            ["hinge/latch spacing and metal strike", "PC Z-axis joint strength and creep", "guard interlock retention"],
            note="A point load on a full-width strip spreads load unrealistically; actual local plate bending can be worse.")

    # M1 reference 160 kgf cm = 15.69 N m; peak/stall and jam torque
    # are unknown, so all mounts remain HOLD.
    torque = params["M1"]["rated_kgf_cm"] * 9.80665 * 10  # N mm
    m1_force = torque / 45.0
    v = bending_point(m1_force, 30., foot[0], 6., E["steel"])
    v["stress_margin_to_room_assumption"] = margin(allowable["steel"], v["stress_MPa"])
    v["deflection_margin_to_L_over_200"] = margin(30 / 200, v["deflection_mm"])
    add("M1 motor foot", "70x6 steel full-width cantilever 30-mm lever; motor torque converted at 45-mm bolt circle",
        {"part": "DRV-M1-FOOT", "foot_width_mm": foot[0], "assumed_web_thickness_mm": 6,
         "lever_mm": 30, "source": "src/supports.py M1 foot; design/assembly.json"},
        {"rated_reference_torque_Nmm": round(torque, 2), "force_N": round(m1_force, 2),
         "type": "TT60 rated reference only, not locked-rotor/jam load"},
        {"stress_MPa": allowable["steel"], "deflection_mm": 30 / 200}, v,
        ["M1 actual selected motor stall torque", "foot weld/bend quality", "deck anchorage/bolt preload"],
        note="Not a motor torque limiter or fatigue analysis.")
    m2_torque = params["M2"]["rated_kgf_cm"] * 9.80665 * 10  # N mm
    m2_web_force = m2_torque / 45 / 2  # two steel webs share nominal couple
    v = bending_point(m2_web_force, 51., 60., 8., E["steel"])
    v["stress_margin_to_room_assumption"] = margin(allowable["steel"], v["stress_MPa"])
    add("M2 extruder thrust stand", "two 8x60-mm side webs, each cantilever 51 mm; equal share of motor torque at 45-mm couple",
        {"part":"EX-STAND", "web_count":2, "web_width_mm":60, "web_thickness_mm":8,
         "web_height_mm":51, "source":"src/supports.py EX-STAND side webs and src/design.py M2"},
        {"rated_reference_torque_Nmm":m2_torque, "force_per_web_N":m2_web_force,
         "type":"TT60 rated reference only; extruder pressure/thrust and stall torque omitted"},
        {"stress_MPa":allowable["steel"]}, v,
        ["M2 selected motor stall torque", "extrusion thrust/pressure and thermal gradient",
         "motor face M5 seating, weld and stand-to-deck M6 preload"],
        note="Motor torque screen does not qualify the 6202/51102 thrust carrier.")


    F_bearing = 500.0  # screening radial load only, not measured cutter reactions
    v = bending_point(F_bearing, 52., 20., 18., E["steel"])
    v["stress_margin_to_room_assumption"] = margin(allowable["steel"], v["stress_MPa"])
    add("front bearing carrier ligament", "20x18-mm proxy cantilever, 52-mm bolt-to-bore lever; local net section lower-bound requires drawing",
        {"part": "DRV-BFRONT", "proxy_web_width_mm": 20, "plate_thickness_mm": 18, "lever_mm": 52,
         "source": "src/design.py DRV-BFRONT 140x80x18 with 28/47 bores"},
        {"radial_force_N": F_bearing, "type": "assumed bearing reaction, not cutter load spectrum"},
        {"stress_MPa": allowable["steel"]}, v,
        ["bearing reactions and cycles", "net section around actual bore and deck pocket", "bearing seat fit/fatigue"],
        note="C2.1 rear 8-mm support after feed relief and S1/S2 bearing blocks are not equivalent to this C1 front proxy; separately HOLD.")
    for name, part, thick, force, lever, width in (
        ("S1 bearing carrier", "S1-BPL", 18., 500., 35., 25.),
        ("C2.1 rear output support", "REAR_OUTPUT_SUPPORT", 8., 300., 30., 40.),
    ):
        v = bending_point(force, lever, width, thick, E["steel"])
        v["stress_margin_to_room_assumption"] = margin(allowable["steel"], v["stress_MPa"])
        add(name, "local cantilever net-web proxy between bearing reaction and mount; not the full irregular plate",
            {"part":part, "plate_thickness_mm":thick, "assumed_local_width_mm":width,
             "assumed_lever_mm":lever,
             "source":"src/design.py S1-BPL 160x100x18" if part == "S1-BPL"
                      else "c2.1/src/build_cad.py support_plate(y=88), 8-mm plate with feed relief"},
            {"radial_force_N":force, "type":"assumed screening bearing reaction, not measured load"},
            {"stress_MPa":allowable["steel"]}, v,
            ["actual force, load direction and cycles", "machined bore/relief net-section and bolt pattern",
             "bearing fits and mount rigidity"], note="Proxy width and lever require drawing/FEM confirmation.")


    # Welded S2 legs: section dimensions from src/supports.py 30x16 web,
    # nominal 184 mm tall (right foot 20 + 6; top 210).
    L, b, t = 184., 30., 16.
    Iweak = b * t**3 / 12
    A = b * t
    Pcr_pin = math.pi**2 * E["steel"] * Iweak / L**2
    Pcr_fixed_free = Pcr_pin / 4
    P = 1000.
    add("S2 steel support column", "Euler weak-axis 30x16 web, pinned-pinned vs fixed-free sensitivity, one column loaded axially",
        {"part": "S2-LEG-R", "length_mm": L, "web_mm": [b, t], "weak_axis_I_mm4": Iweak,
         "source": "src/supports.py S2-LEG-R boxes and foot datums"},
        {"compressive_force_N": P, "type": "assumed screening reaction; impact/lateral bending omitted"},
        {"stress_MPa": allowable["steel"], "buckling_safety_factor": 3.0},
        {"axial_stress_MPa": P/A, "pinned_Pcr_N": Pcr_pin, "fixed_free_Pcr_N": Pcr_fixed_free,
         "weakest_buckling_margin_with_factor_3": margin(Pcr_fixed_free/3, P),
         "axial_stress_margin": margin(allowable["steel"], P/A)},
        ["weld/anchor geometry", "eccentric force and lateral bending", "actual S2 cutting force"],
        note="High ideal Euler margin does not assess weld, fatigue, lateral force or profile connection.")

    # Extrusion CAD shell is explicitly a non-slot placeholder. The following
    # solid and 2-mm perimeter/50%-slot-retention bounds are only geometric
    # sensitivity brackets: NOT allowable actual T-slot second moments.
    for profile, span, h, width, force in (("FR-2020-590", 590., 20., 20., 300.),
                                            ("FR-2040-320", 320., 20., 40., 500.)):
        I_solid = width * h**3 / 12
        I_skin = (I_solid - (width-4)*(h-4)**3/12) * 0.5
        y = {}
        for label, I in (("50pct_skin_proxy", I_skin), ("solid_upper_proxy", I_solid)):
            y[label] = {"I_mm4": I, "stress_MPa": force*span*h/(8*I),
                        "deflection_mm": force*span**3/(48*E["aluminum"]*I)}
        y["deflection_limit_mm"] = span / 200
        y["proxy_deflection_margin_range"] = [margin(span/200, y[k]["deflection_mm"])
                                                for k in ("50pct_skin_proxy", "solid_upper_proxy")]
        add(f"{profile} geometric proxy", "simply supported, center point load; 50% of 2-mm rectangular skin versus SOLID upper geometric proxy",
            {"part": profile, "span_mm": span, "nominal_section_mm": [width, h],
             "not_actual_T_slot_I": True, "source": "src/design.py profile placeholder; bom/profile_cut_plan.csv"},
            {"center_force_N": force, "type": "assumed machine reactions, joint slip excluded"},
            {"deflection_mm": span/200, "stress_MPa": allowable["aluminum"]}, y,
            ["manufacturer T-slot Ix/Iy and alloy/temper", "slot/fastener slip", "frame joints and actual reaction direction"],
            note="Bracket is not a proven lower/upper bound on the actual profile: slot metal topology is unmeasured.")

    # M6 8.8 is a candidate grade, not evidence for installed rods/nuts/T-nuts.
    As, proof, Fbolt = 20.1, 640., 1000.
    add("M6 candidate interface", "single M6 tensile-stress area and 5-mm steel bearing coupon; factor 3 on assumed grade-8.8 proof",
        {"thread": "M6x1", "stress_area_mm2": As, "hole_diameter_mm": 6.6,
         "metal_plate_mm": deck[2], "grade_assumption": "ISO 8.8 candidate, not installed grade"},
        {"per_bolt_tension_N": Fbolt, "separate_transverse_bearing_force_N": Fbolt,
         "type": "independent 1000-N axial and 1000-N transverse illustrative cases; combination and prying omitted"},
        {"proof_MPa": proof, "factor_on_proof": 3, "bearing_stress_MPa": allowable["steel"]},
        {"nominal_tension_stress_MPa": Fbolt/As, "proof_margin_with_factor_3": margin(proof*As/3,Fbolt),
         "plate_bearing_stress_MPa": Fbolt/(6.6*deck[2]),
         "plate_bearing_margin": margin(allowable["steel"],Fbolt/(6.6*deck[2]))},
        ["owned T-slot/tee-nut series and pull-out rating", "bolt count/positions/edge distance", "preload/slip and combined load", "proof certification"],
        note="Thread proof is not T-slot pull-out, thread stripping, bracket bending or weld strength.")

    alpha = {"PC": 65e-6, "steel": 12e-6, "aluminum": 23e-6}
    thermal = []
    for length, T, label in ((top_buffer, 60., "buffer-to-steel"), (lid[0], 80., "lid-to-steel"),
                             (deck[0], 90., "steel-deck-to-aluminum-frame")):
        a, b = ("steel", "aluminum") if label.startswith("steel-") else ("PC", "steel")
        deltaT = T - 20
        growth_a, growth_b = length*alpha[a]*deltaT, length*alpha[b]*deltaT
        thermal.append({"joint": label, "length_mm": length, "reference_C": 20, "assumed_max_C": T,
                        "alpha_1_per_K": {a: alpha[a], b: alpha[b]}, "free_growth_mm": {a: growth_a,b:growth_b},
                        "differential_mm": abs(growth_a-growth_b),
                        "decision": "HOLD", "required": "slotted/isolated interface and measured local service temperature; no rigid fully constrained expansion"})

    # Illustrative base strengths reduced by assumed print-axis and
    # long-term retention multipliers. No tested coupon or safety allowable.
    polymers = []
    for name, strength, axis_xy, axis_z, retained60, service in (
        ("PLA", 50., .65, .30, .20, 45.),
        ("ABS", 40., .55, .35, .55, 75.),
        ("PC", 55., .70, .45, .65, 95.),
    ):
        ambient = {"XY": strength*axis_xy/3, "Z": strength*axis_z/3}
        hot = {k:v*retained60 for k,v in ambient.items()}
        polymers.append({"material": name, "form": "dry, controlled FDM assumed; actual filament lot/nozzle/enclosure and layer bonds untested",
                         "illustrative_isotropic_short_term_strength_MPa": strength,
                         "axis_retention_assumption": {"XY":axis_xy,"Z":axis_z},
                         "long_term_60C_retention_assumption": retained60,
                         "assumed_continuous_service_ceiling_C": service,
                         "screen_limit_20C_MPa": ambient, "screen_limit_60C_MPa": hot,
                         "60C_decision": "REJECT" if 60 >= service else "HOLD",
                         "fabrication_decision": "REJECT hot/hard load path" if name == "PLA" else
                         "HOLD; PC conditional enclosure candidate" if name == "PC" else
                         "HOLD; cold outer panel candidate only",
                         "reason": "Layer-normal strength, elevated-temperature creep and process coupon data not measured; do not load printed support or safety retention."})
    # Compare the actual plate/beam stress proxies to assumed long-term PC
    # print-axis strengths; there is NO service-duration constitutive model.
    pc = next(p for p in polymers if p["material"] == "PC")
    creep = []
    for c in cases:
        if not c["name"].startswith(("FEED-BUF", "HOPPER", "HOP-LID")):
            continue
        stress = c["computed"]["stress_MPa"]
        for temp_C, retention in ((60., .65), (80., .35)):
            axis = {a:55 * factor * retention / 3 for a, factor in pc["axis_retention_assumption"].items()}
            creep.append({"part_scenario":c["name"], "temperature_C":temp_C,
                          "stress_proxy_MPa":stress, "long_term_retention_assumption":retention,
                          "screen_limit_MPa":axis,
                          "stress_margin_XY":margin(axis["XY"],stress),
                          "stress_margin_Z":margin(axis["Z"],stress),
                          "screen_decision":"REJECT assumed load/temperature/axis combination"
                            if stress > min(axis.values()) else "HOLD unmeasured duration/grade/layer data"})

    # Current annulus thickness is read from CAD source. Compare to the
    # other sheet option without assigning any unmodelled rim-stiffening credit.
    ro, ri = wind["flange_r"], wind["shaft_r"] + .5
    # Flange bore radius is 8.5 mm in c2.1/src/winder.py _flange().
    flange_span = ro - wind["drum_r"]
    density = 7.85e-6  # kg/mm3 steel
    flanges = []
    for thick in (flange_actual_mm, 6. if flange_actual_mm == 3. else 3.):
        one_mass = math.pi*(ro**2-ri**2)*thick*density
        rim = bending_point(20., flange_span, 20., thick, E["steel"])
        flanges.append({"thickness_mm": thick, "two_flange_mass_kg": 2*one_mass,
                        "one_flange_rim_strip": rim,
                        "stress_margin_to_room_assumption": margin(allowable["steel"],rim["stress_MPa"]),
                        "deflection_margin_to_L_over_100": margin(flange_span/100,rim["deflection_mm"]),
                        "decision": "HOLD"})
    shaft_span = 170 + 4 - (88 + 4)  # block centrelines y92/174, source c2.1/src/winder.py
    spool_force = 120.  # assumed weight + tension/dynamic envelope, not rated
    Ishaft = math.pi*wind["shaft_r"]**4/4
    shaft_stress = (spool_force*shaft_span/4)*wind["shaft_r"]/Ishaft
    shaft_delta = spool_force*shaft_span**3/(48*E["steel"]*Ishaft)
    add("WIND spool shaft", "simply supported solid dia16 shaft over both bearing-block centerlines; central resultant",
        {"part": "WIND_SPOOL_SHAFT", "diameter_mm": 2*wind["shaft_r"], "block_centerline_span_mm": shaft_span,
         "source": "c2.1/src/winder.py WIND and spool_bearing_blocks; bearing bores are envelopes only"},
        {"vertical_resultant_N": spool_force, "type": "assumed spool+filament+tension/dynamic envelope, no shock or selected motor"},
        {"stress_MPa": allowable["steel"], "deflection_mm": shaft_span/200},
        {"I_mm4":Ishaft, "stress_MPa":shaft_stress, "deflection_mm":shaft_delta,
         "stress_margin":margin(allowable["steel"],shaft_stress),
         "deflection_margin":margin(shaft_span/200,shaft_delta)},
        ["actual wound mass/tension and selected motor torque", "block attachment to frame", "bearing rating and shaft retention"],
        note="No grip, traversing, rotating balance or axle fatigue proof.")
    guide_force = pull["spring_rate_N_mm"] * .6
    guide_I = math.pi * 5.**4 / 64
    guide_stress = guide_force * 26 * 2.5 / guide_I
    guide = {"I_mm4":guide_I, "moment_Nmm":guide_force*26,
             "stress_MPa":guide_stress, "deflection_mm":guide_force*26**3/(3*E["steel"]*guide_I),
             "stress_margin":margin(allowable["steel"],guide_stress)}
    add("PULL guide-post screening", "one 5-mm circular steel post cantilever under half of two 8 N/mm springs at 0.6-mm deflection",
        {"part":"PULL_ROLLER_ADJ", "post_diameter_mm":5, "post_length_mm":26,
         "source":"c2.1/src/winder.py guide posts and PULL spring rate"},
        {"spring_force_total_N": 2*guide_force, "post_force_N":guide_force,
         "type":"assumed .6-mm compression, not measured nip normal force"},
        {"stress_MPa":allowable["steel"]}, guide,
        ["guide seat and post fatigue", "spring preload and cam load", "actual traction and tension"],
        note="Real post loading and carriage contact can dominate this ideal beam.")
    frame = bending_point(30., 10., 22., 4., E["steel"])
    frame["stress_margin_to_room_assumption"] = margin(allowable["steel"],frame["stress_MPa"])
    add("PULL frame base", "22x4-mm base strip with assumed 10-mm cantilever lever under transverse guide force",
        {"part":"PULL_FRAME", "proxy_strip_width_mm":22, "base_thickness_mm":4, "lever_mm":10,
         "source":"c2.1/src/winder.py pull_frame base x824..846, z100..104"},
        {"lateral_force_N":30, "type":"assumed lateral nip/actuator reaction"},
        {"stress_MPa":allowable["steel"]}, frame,
        ["actual nip/tension forces", "cam fastener and welded joint", "mount to frame and bearing seats"],
        note="Only the base strip, not 3-mm upright side sheets, is screened; whole frame remains HOLD.")

    report = {
        "schema": "VP1-structural-screen-1", "units": "mm, N, MPa=N/mm2, kg, C; deflection and free thermal expansion in mm",
        "status": "HOLD_NOT_STRUCTURALLY_QUALIFIED",
        "source_inputs": [source(p) for p in (assembly_path, "design/parameters.json", winder_path,
                          bom_path, "src/design.py", "src/supports.py", "bom/profile_cut_plan.csv")],
        "material_screen_assumptions": {"E_MPa": E, "ambient_stress_limits_MPa": allowable,
          "interpretation": "chosen conservative-ish screening thresholds, not tested material allowables or codes; no measured toughness, weld or layer strengths"},
        "cases": cases, "thermal_expansion": thermal, "printed_polymer_candidates": polymers,
        "PC_creep_orientation_screen": creep,
        "buffer_reinforcement_sizing":reinforcement,
        "spool_flange_review": {"current_CAD": f"two {flange_actual_mm:g}-mm steel annuli dia200 bore17, c2.1/src/winder.py; BOM material requires matching update",
            "current_thickness_mm":flange_actual_mm,
            "comparison": "current 3-mm sheet versus legacy 6-mm steel plate; no rolled-edge/rib stiffening credited",
            "rim_model": "one 20-mm-wide radial cantilever from drum radius35 to rim100 with 20 N point load; 20N and rigidity threshold are assumptions",
            "flanges": flanges, "two_flange_mass_saved_6mm_to_3mm_kg":abs(flanges[0]["two_flange_mass_kg"]-flanges[1]["two_flange_mass_kg"]),
            "decision": "HOLD: verify hub attachment, flange bend/rotating balance, guards and axial shaft retention; CAD and BOM must agree"},
        "manufacturing": {"PC_enclosure": "PC CANDIDATE for cold hopper/lid and redesigned buffer; CURRENT buffer inclined wall REJECTS assumed pressure strip, requiring metal load path or proven stiffening. Split hopper seams, metal throat/interlock strike, creep and guard signoffs HOLD",
           "PLA": "REJECT for hot enclosure or load-bearing supports; only cold non-safety prototypes",
           "ABS": "HOLD as cold outer panel option; no hot-zone or safety retainers without grade/temperature/creep proof",
           "motor_bearing_and_fastener_load_paths": "steel candidate; never substitute FDM for support columns, bearings, shafts, bolts, guard anchors",
           "owned_aluminum_profile": "HOLD actual T-slot moment of inertia, alloy, slot nut/bolt pullout and measured hole/slot pattern",
           "print_envelope_mm":210, "panel_note":"180-mm lid and 190-mm buffer mouth fit XY <=210; hopper wall >210 tall, so split into <=210-mm pieces and screen joint; orient primary flexural tension in XY, Z weak and creep-sensitive",
           "feedstocks_not_construction": "PLA/PET/TPU are incoming waste feedstocks; this screening's PLA/ABS/PC are candidate construction polymers, TPU only as possible puller tread after friction/wear proof"},
        "explicit_exclusions": ["no measured forces, impact energy, vibration or fatigue", "no bearing, chain, gear, weld, layer-bond, screw or slot-nut certification",
             "no local buckling, notch, fracture, thermal gradients, pressure vessel or guard containment rating",
             "no FEED-BUF straight-neck joint or metal-liner anchorage strength calculation",
             "no raw feedstock coupon or digital geometry used as printed-part proof", "no fabrication, procurement or energization authorization"],
        "decision": "HOLD; all cases provisional and unmeasured dependencies must be closed before physical release"
    }
    return report


if __name__ == "__main__":
    report = screen()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"file": str(OUT.relative_to(REPO)), "status":report["status"],
                      "cases":len(report["cases"]), "spool_mass_saved_kg":report["spool_flange_review"]["two_flange_mass_saved_6mm_to_3mm_kg"]}))
