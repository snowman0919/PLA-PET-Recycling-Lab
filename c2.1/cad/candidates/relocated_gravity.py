"""Independent, non-release relocated S2 gravity-handoff alternative.

Runs against the active source solids; writes only next to this script.  The
manifest separates geometric checks from unqualified transport/drive ratings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import cadquery as cq

HERE = Path(__file__).resolve()
C21 = HERE.parents[2]
REPO = C21.parent
sys.path.insert(0, str(C21 / "src"))
import build_machine_integration as integration
import drive_teeth
import drive_kinematics
import chute
import guards
import winder
import electrical_bay
import hopper_panels
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

V = cq.Vector
S2_AXIS = (308.0746286057215, 299.0, 215.0)
DX = S2_AXIS[0] - 308.56946468906176
DROP = -65.0
M1_UP = 95.60611928920366
S1_FEED = ("S1_BELT", "S1_BELT_DRIVE", "S1_BELT_IDLER",
           "S1_BELT_BEARINGS", "S1_BELT_FOLLOWER", "S1_BELT_CHAIN",
           "S1_SWEEP_SOUTH", "S1_SWEEP_NORTH", "S1_SWEEP_GEAR_DRUM_S",
           "S1_SWEEP_GEAR_S", "S1_SWEEP_GEAR_DRUM_N", "S1_SWEEP_GEAR_N",
           "S1_SWEEP_BEARINGS")
SELECTED_RELIEFS = ("S1-ROOF-R_001", "S1-STUD_001", "DRV-B12_001",
                    "DRV-DECK_001", "DRV-JACK_001", "KEY-6-16_002")
REPLACED_LEGS = {"S2-LEG-L_001", "S2-LEG-L_002",
                 "S2-LEG-R_001", "S2-LEG-R_002"}
REPLACED_EX_STAND = "EX-STAND_001"
M1_SUPPORTS = {"DRV-DECK_001", "DRV-M1-FOOT_001",
               "DRV-RISER12_001", "DRV-RISER20_001", "DRV_M1_FACE_PLATE"}
STATIONARY_DRIVE = {"DRV-SP24-B25_001", "KEY-8-16_001",
                    "DRV-SP12-B12_001", "KEY-4-16_002"}
FUNNEL_NAMES = ("ALT_S1_CATCH", "ALT_S1_S2_GRAVITY_FLOOR",
                "ALT_S1_S2_SIDE_SOUTH", "ALT_S1_S2_SIDE_NORTH")
# Deliberately named contacts are interfaces, not unexplained collisions.
FUNCTIONAL = {frozenset(p) for p in drive_teeth.FUNCTIONAL_PAIRS}


def rec(name, shape, group, provenance, transform=None, part=None):
    if not shape.isValid() or not shape.Solids():
        raise RuntimeError(f"invalid candidate part {name}")
    return dict(name=name, part=part or name, group=group, shape=shape,
                provenance=provenance, transform=transform or {})


def at_box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, V(x0,y0,z0))


def loft_section(stations):
    """Ruled quad surface through (x, south, north, floor-z) stations."""
    wires = []
    for x, south, north, z in stations:
        pts = [V(x,south,z), V(x,north,z), V(x,north,z+2), V(x,south,z+2)]
        wires.append(cq.Wire.makePolygon(pts, close=True))
    return cq.Solid.makeLoft(wires, ruled=True).clean()


def gravity_parts():
    # The legacy S1 belt and two opposed sweep flights are the only retained
    # assisted delivery.  After their central exit a 30-degree chute slopes
    # toward the relocated, right/upper S2 mouth; no screw or transfer belt.
    selected = cq.importers.importStep(str(C21/"cad/parts_stage1/CHUTE_BODY.step")).val()
    catch = selected.intersect(at_box(50,239.0,100,340,300,520)).clean()
    # The former screw-specific x236..237 side-lane stop blocked every
    # off-centre S1 flake before the narrow candidate receiver. Open the
    # full S1 discharge width onto the new, broad ruled steel catch.
    catch = catch.cut(at_box(235.3,239.0,163.4,323.6,333.0,353.0)).clean()
    if len(catch.Solids()) != 1:
        raise RuntimeError("S1 catch pan split after removing old auger path")
    # Wide at the S1 outlet, converging only along the descending ramp.
    # The terminal edge is above/outside the S2 shell's upper-right open arc;
    # a falling Ø3 envelope must still enter the real bore in Isaac.
    stations = [(237.4,163.4,323.6,332.0),
                (260.0,190.0,298.0,319.0),
                (310.0,244.0,287.0,290.0),
                (342.0,263.0,287.0,275.0)]
    floor = loft_section(stations)
    # Thin upright steel side guides, with a continuous open top.
    sides = []
    for side in (1,2):
        wall_segments=[]
        for a,b in zip(stations[:-1],stations[1:]):
            def wall_wire(st):
                x,ys,yn,z=st; y=ys if side==1 else yn
                return cq.Wire.makePolygon([V(x,y,z+1),V(x,y+1.5,z+1),
                                            V(x,y+1.5,z+17),V(x,y,z+17)],close=True)
            wall_segments.append(cq.Solid.makeLoft([wall_wire(a),wall_wire(b)],ruled=True))
        sides.append(cq.Compound.makeCompound(wall_segments))
    source = "active c2.1/cad/parts_stage1/CHUTE_BODY.step trimmed at x239"
    # Overlapped joints become one welded steel receiver. Retain the raw
    # segment geometry above so the seam and proposed fabrication remain
    # inspectable; the union, not coincident separate solids, enters STEP.
    receiver=catch.fuse(floor,*sides).clean()
    return [rec("ALT_S1_S2_RECEIVER",receiver,"feed",
                source+" + ruled steel floor and two welded side guides")]


def supports():
    # The C2.1 plates lie at y203..211 (output), y351..359 (input),
    # bottom edge z130. Floor rails touch FR-BASE at z0, four posts contact
    # the full-width plate undersides rather than its bores/upper chamfer.
    result=[]
    for tag,y0 in (("OUTPUT",203.0),("INPUT",351.0)):
        rail=at_box(266,371,y0-4,y0+8,0,16)
        result.append(rec(f"ALT_S2_FOOT_RAIL_{tag}",rail,"frame_mount",
                          "new S355 foot rail face-mounted to frame base"))
        for side,x0 in (("L",270.0),("R",350.0)):
            post=at_box(x0,x0+16,y0,y0+8,16,130)
            result.append(rec(f"ALT_S2_STANCHION_{tag}_{side}",post,
                              "frame_mount","new S355 stanchion to plate lower face"))
    # Raised M1 keeps the original coaxial motor, pinion, jack and bearing
    # cartridge; only its original deck position changes. Four real posts
    # span the old base-to-deck gap, away from the lowered M2 envelope.
    for side,x0 in (("L",30.0),("R",190.0)):
        for end,y0 in (("F",210.0),("B",380.0)):
            post=at_box(x0,x0+16,y0,y0+16,20,20+M1_UP)
            result.append(rec(f"ALT_M1_POST_{side}_{end}",post,"frame_mount",
                              "new S355 deck stanchion, frame top to relocated deck"))
    result.append(rec("ALT_M1_FRONT_CROSS_RAIL",
                      at_box(40,220,210,226,16,20),"frame_mount",
                      "S355 cross rail bearing front posts, end faces on existing frame"))
    # EX-STAND's original 79mm column cannot extend below z0 when its
    # cartridge descends 65mm. Replace it by a lower thrust foot on the
    # existing x220..260 frame rail, plus a concave independent barrel rest.
    result.append(rec("ALT_EX_THRUST_FOOT",at_box(221,260,245,305,20,25),
                      "frame_mount","new steel thrust support face-to-face at z25"))
    barrel_rest=at_box(432,442,257,293,0,60)
    bore=cq.Solid.makeCylinder(15.2,12,V(431,275,60),V(1,0,0))
    barrel_rest=barrel_rest.cut(bore).clean()
    result.append(rec("ALT_EX_BARREL_REST",barrel_rest,"frame_mount",
                      "new open S355 cold-barrel rest with 0.2mm nominal radial gap"))
    return result


def translated_selected():
    config=json.loads((C21/"design/machine_integration.json").read_text())
    master=json.loads((REPO/config["legacy_master"]).read_text())
    legacy=integration.legacy_parts(master,config)
    kept=[]
    shifted=[]
    for item in legacy:
        name=item["name"]
        if name in REPLACED_LEGS or name == REPLACED_EX_STAND:
            continue
        shape=item["shape"]
        if name in SELECTED_RELIEFS:
            path=C21/"cad/parts_stage1"/(name+".step")
            shape=cq.importers.importStep(str(path)).val()
        translation=(0.0,0.0,0.0)
        if item["group"] in ("extruder","feed","cooling") and name!="HOP-LID_001":
            translation=(DX,0,DROP)
        elif name in ("DRV-SP12-B12_001","KEY-4-16_002"):
            translation=(DX,0,DROP)
        elif item["group"]=="drive" and name not in STATIONARY_DRIVE:
            translation=(0,0,M1_UP)
        elif name in M1_SUPPORTS:
            translation=(0,0,M1_UP)
        elif name=="DRV_M2_FACE_PLATE":
            translation=(DX,0,DROP)
        if any(translation):
            shape=shape.translate(translation); shifted.append(name)
        kept.append(rec(name,shape,item["group"],
                        "master source, selected integration replacement/relief where present",
                        {"translate_mm":list(translation)},part=item["part"]))
    c21=integration.c21_parts(config)
    for item in c21:
        kept.append(rec(item["name"],item["shape"].translate((DX,0,DROP)),
                        "S2-C2.1","active 40-part cycloid/shell/screen/saddle geometry",
                        {"rotation_axis":[0,0,1],"rotation_deg":180,
                         "translation_mm":list(S2_AXIS)}))
    return kept,shifted


def other_parts():
    out=[]
    for name in S1_FEED:
        shape=cq.importers.importStep(str(C21/"cad/parts_stage1"/(name+".step"))).val()
        out.append(rec(name,shape,"feed","selected actual S1 belt/sweep/chain STEP"))
    chain_a=dict(drive_kinematics.CHAIN_A,
                 p1=(drive_kinematics.CHAIN_A["p1"][0],65+M1_UP),links=74)
    chain=dict(drive_kinematics.CHAIN_B,
               p1=(drive_kinematics.CHAIN_B["p1"][0],65+M1_UP),
               p2=(S2_AXIS[0],S2_AXIS[2]),links=56)
    out.append(rec("DRV-CHAIN-A",drive_teeth._chain_loop(chain_a),
                   "drive","new #35 74-link chain A, raised jack to unchanged S1 shaft"))
    out.append(rec("DRV-CHAIN-B",drive_teeth._chain_loop(chain),
                   "drive","new #35 56-link chain B, raised jack to lowered S2 input"))
    # Existing guard construction references this module-level datum;
    # override it only in this one process, not in selected source files.
    drive_teeth.CHAIN_A=chain_a
    drive_teeth.CHAIN_B=chain
    receiver=gravity_parts()[0]["shape"]
    for name,shape in guards.components():
        if name=="GUARD_S2_RING":
            shape=shape.translate((DX,0,DROP))
            original=shape.Volume()
            # The source nominally mates to this cut face; real clearance
            # and attachment require a fabrication detail, not CAD PASS.
            shape=shape.cut(receiver).clean()
            if len(shape.Solids())!=1 or shape.Volume()<.9*original:
                raise RuntimeError("S2 guard receiver window destroys guard")
        elif name=="GUARD_CHAIN_B":
            shape=shape.translate((0,0,3))
        out.append(rec(name,shape,"guard","active guard; S2 ring window follows welded receiver"))
    for name,shape,group in winder.components():
        out.append(rec(name,shape.translate((DX,0,DROP)),group,
                       "active actual puller/spool, shifted with extrudate line",
                       {"translate_mm":[DX,0,DROP]}))
    for name,shape in electrical_bay.components():
        out.append(rec(name,shape,"electrical","active selected electrical envelope"))
    for name,shape in hopper_panels.components():
        out.append(rec(name,shape,"feed","active split hopper shell/steel seam"))
    return out,chain


def pairs(a,b,same=False):
    """Exact OCCT BRep nonzero overlaps, filtered only by bbox."""
    hits=[]; candidate=0; checked=0
    for i,u in enumerate(a):
        for v in (b[i+1:] if same else b):
            if u is v: continue
            checked+=1
            if not integration.bbox_overlap(u["shape"],v["shape"]): continue
            candidate+=1
            volume=u["shape"].intersect(v["shape"]).Volume()
            if volume>0.05:
                pair=frozenset((u["name"],v["name"]))
                hits.append({"a":u["name"],"b":v["name"],
                             "volume_mm3":round(volume,4),
                             "intentional_existing_drive_fit":pair in FUNCTIONAL})
    return {"checked_pairs":checked,"bbox_candidates":candidate,"exact_hits":hits}


def shape_gap(a,b):
    return BRepExtrema_DistShapeShape(a.wrapped,b.wrapped).Value()


def nominal_mass(records,master):
    materials=master["parts"]
    rows=[]
    for p in records:
        material=materials.get(p["part"],{}).get("material", "new S355 steel" if p["name"].startswith("ALT_") else "candidate/model envelope")
        if "Al " in material:
            density=2.70
        elif "PC" in material and "steel" not in material:
            density=1.20
        elif "TPU" in material:
            density=1.20
        else:
            density=7.85
        mm3=sum(s.Volume() for s in p["shape"].Solids())
        rows.append({"name":p["name"],"material_label":material,
                     "density_g_cm3":density,"nominal_mass_g":round(mm3*density/1000,2),
                     "assumption":"nominal Al 2.70, polymer 1.20, steel/equipment proxy 7.85 g/cm3; not weighed"})
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=HERE.with_name("relocated_gravity.step"))
    parser.add_argument("--diagnostic",action="store_true",
                        help="write HOLD manifest/STEP despite non-qualified contacts")
    args=parser.parse_args()
    output=args.out.resolve()
    if output.parent != HERE.parent:
        raise SystemExit("candidate outputs must remain beside this script")
    legacy,shifted=translated_selected()
    additions,chain=other_parts()
    novel=gravity_parts()+supports()
    records=legacy+additions+novel
    if len({p["name"] for p in records})!=len(records):
        raise RuntimeError("duplicate assembly label")
    moving=[p for p in records if p["name"] in shifted or p["group"] in
            ("S2-C2.1","cooling","puller","spool") or p["name"] in
            ("DRV-CHAIN-A","DRV-CHAIN-B","GUARD_CHAIN_B","GUARD_S2_RING") or
            p["name"].startswith("ALT_")]
    stationary=[p for p in records if p not in moving]
    audit=pairs(moving,stationary)
    internal=pairs(moving,moving,same=True)
    names={p["name"]:p["shape"] for p in records}
    bbox=integration.extent(records)
    body=integration.extent([p for p in records if p["group"] not in
                             ("cooling","puller","spool")])
    body["limit_mm"]=[700,420,520]
    body["passed"]=all(a<=b+1e-6 for a,b in zip(body["size_mm"],body["limit_mm"]))
    chain_length=drive_kinematics.chain_length_mm(chain)
    pitch_delta=chain_length-chain["links"]*drive_kinematics.CHAIN_PITCH
    supports_by_name={n: names[n] for n in names if n.startswith("ALT_S2_STANCHION")}
    support_gaps={n:round(shape_gap(shape,names["FRONT_INPUT_SUPPORT" if "INPUT" in n
                                    else "REAR_OUTPUT_SUPPORT"]),4)
                  for n,shape in supports_by_name.items()}
    chain_a=dict(drive_kinematics.CHAIN_A,
                 p1=(drive_kinematics.CHAIN_A["p1"][0],65+M1_UP),links=74)
    chain_a_len=drive_kinematics.chain_length_mm(chain_a)
    mouth=(342.0,275.0)
    radial=math.hypot(mouth[0]-S2_AXIS[0],mouth[1]-S2_AXIS[2])
    diagnostics={"stationary_vs_changed":audit,"changed_internal":internal,
                 "support_plate_to_stanchion_gaps_mm":support_gaps,
                 "floor_to_s2_fixed_shell_gap_mm":round(min(shape_gap(names["ALT_S1_S2_RECEIVER"],names[n])
                       for n in ("C2_LEFT_WEAR_SHELL","C2_RIGHT_WEAR_SHELL_1",
                                 "C2_RIGHT_WEAR_SHELL_2")),4),
                 "mouth_lip_r_mm":round(radial,3),
                 "mouth_clearance_to_shell_ro_mm":round(radial-65.8,3),
                 "funnel_drop_mm":57.0,"gravity_path":"S1 belt/sweep delivery to ruled floor, then free fall through upper-right S2 shell gap",
                 "same_input_flow_qualified":False,
                 "chain_pitch_delta_mm":round(pitch_delta,4),
                 "chain_A_pitch_delta_mm":round(chain_a_len-74*drive_kinematics.CHAIN_PITCH,4),
                 "m1_deck_to_post_gaps_mm":{n:round(shape_gap(names[n],names["DRV-DECK_001"]),4)
                                             for n in names if n.startswith("ALT_M1_POST")},
                 "extruder_thrust_to_new_foot_gap_mm":round(shape_gap(names["ALT_EX_THRUST_FOOT"],names["EX-THRUST_001"]),4),
                 "extruder_barrel_to_new_rest_gap_mm":round(shape_gap(names["ALT_EX_BARREL_REST"],names["EX-BARREL_001"]),4),
                 "feed_buffer_to_saddle_gap_mm":round(shape_gap(names["FEED-BUF_001"],names["FEED-BUF-SADDLE_001"]),4),
                 "feed_saddle_to_cold_barrel_gap_mm":round(shape_gap(names["FEED-BUF-SADDLE_001"],names["EX-BARREL_001"]),4),
                 "feed_throat_world_mm":[round(299+DX,4),275,80],
                 "barrel_feed_hole_world_mm":[round(299+DX,4),275,80]}
    # Exact contacts are NEVER suppressed as pass. Interfaces between
    # intended mated parts are listed and need review/qualification.
    unexpected=[h for section in (audit,internal) for h in section["exact_hits"]
                if not h["intentional_existing_drive_fit"]]
    passed=(body["passed"] and not unexpected and
            abs(pitch_delta)<0.05 and abs(chain_a_len-74*drive_kinematics.CHAIN_PITCH)<0.05 and
            all(g<=0.05 for g in support_gaps.values()) and radial>65.8)
    manifest={"revision":"C2.1-ALT-RELOCATED-GRAVITY",
              "geometry_passed":passed,"status":"GEOMETRY_PASS_FLOW_HOLD" if passed else "GEOMETRY_HOLD",
              "source_sha256":hashlib.sha256(HERE.read_bytes()).hexdigest(),
              "selected_reference_sha256":hashlib.sha256((C21/"cad/PPR_VP1.step").read_bytes()).hexdigest(),
              "transform":{"s2_rotation_axis":[0,0,1],"s2_rotation_deg":180,
                           "s2_translation_mm":list(S2_AXIS),
                           "m1_motor_jack_deck_shift_mm":[0,0,M1_UP],
                           "downstream_shift_mm":[DX,0,DROP]},
              "chain_A":{"driver_center_xz_mm":list(chain_a["p1"]),
                          "driven_center_xz_mm":list(chain_a["p2"]),
                          "teeth":[24,24],"plane_y0_mm":chain_a["y0"],
                          "computed_pitch_length_mm":round(chain_a_len,4),
                          "links":74,"nominal_mm":round(74*drive_kinematics.CHAIN_PITCH,4)},
              "chain_B":{"driver_center_xz_mm":list(chain["p1"]),
                          "driven_center_xz_mm":list(chain["p2"]),
                          "teeth":[24,12],"plane_y0_mm":chain["y0"],
                          "computed_pitch_length_mm":round(chain_length,4),
                          "links":56,"nominal_mm":round(56*drive_kinematics.CHAIN_PITCH,4),
                          "pitch_difference_mm":round(pitch_delta,4),
                          "rating_and_tension":"HOLD"},
              "object_count":len(records),
              "solid_count":sum(len(p["shape"].Solids()) for p in records),
              "body":body,"operating_envelope":bbox,
              "diagnostics":diagnostics,
              "parts":[{"name":p["name"],"group":p["group"],
                        "solid_count":len(p["shape"].Solids()),
                        "bounds_mm":[round(v,3) for v in integration.bounds(p["shape"])],
                        "transform":p["transform"],"source":p["provenance"]}
                       for p in records],
              "mass_estimate":{"basis":"BRep volumes x nominal proxy density; motors/bearings and polymer compound not measured",
                               "parts":nominal_mass(records,json.loads((REPO/"design/assembly.json").read_text()))},
              "holds":["No same-input PhysX connected-flow claim; passive fragment bridging, rebound and pickup unqualified",
                       "Both 74/56-link chains require real tension/tolerance/chain load verification",
                       "Guard cutouts, welded mounts, fasteners and material credentials unqualified",
                       "Power 500W cap and 100k KRW target not re-qualified by this CAD export"]}
    manifest["mass_estimate"]["total_nominal_kg"]=round(sum(p["nominal_mass_g"] for p in manifest["mass_estimate"]["parts"])/1000,3)
    if passed or args.diagnostic:
        cq.exporters.export(cq.Compound.makeCompound([p["shape"] for p in records]),str(output))
        integration.normalize_step_timestamp(output)
        imported=cq.importers.importStep(str(output)).solids().vals()
        manifest["step"]={"path":str(output.relative_to(REPO)),
                          "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                          "reimported_solids":len(imported),
                          "all_valid":all(s.isValid() for s in imported)}
        if len(imported)!=manifest["solid_count"] or not manifest["step"]["all_valid"]:
            manifest["geometry_passed"]=False
            manifest["status"]="GEOMETRY_HOLD_EXPORT_ROUNDTRIP"
    output.with_suffix(".json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({k:manifest[k] for k in ("status","geometry_passed","object_count","solid_count","body","operating_envelope","chain_B","diagnostics")},indent=2))
    if not manifest["geometry_passed"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
