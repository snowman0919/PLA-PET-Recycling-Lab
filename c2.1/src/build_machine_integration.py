"""Build and verify the C2.1 S2 subassembly inside the complete C1 machine.

C1 is reused as an interface baseline, not as a release of its motors, gears,
screw, electrical system, guards, or procurement choices.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import sys

import cadquery as cq

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(C21/"src"))
from build_cad import components, local_rotor, moved
import drive_teeth
import chute as chute_mod
import guards as guards_mod
import winder as winder_mod
import electrical_bay as electrical_mod
import chain_relief
from transmission import Transmission

# VP1 Stage 2: legacy envelope instances replaced by real geometry.
EXCLUDED_LEGACY_INSTANCES = {"SPOOL-ENV_001", "PULL-ROLLER_001",
                             "PULL-ROLLER_002", "GUARD_SECTION_ENVELOPE_HOLD"}


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]


def bbox_overlap(a, b, tolerance=0.01):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    return all(min(getattr(aa, axis+"max"), getattr(bb, axis+"max"))
               - max(getattr(aa, axis+"min"), getattr(bb, axis+"min")) > tolerance
               for axis in "xyz")


def normalize_step_timestamp(path):
    text = path.read_text(encoding="utf-8")
    text, replacements = re.subn(r"(FILE_NAME\('[^']*',')[^']*(')",
                                 r"\g<1>2000-01-01T00:00:00\2", text, count=1)
    if replacements != 1:
        raise RuntimeError(f"Could not normalize STEP timestamp: {path}")
    path.write_text(text, encoding="utf-8")


def legacy_parts(master, config):
    excluded = config["excluded_legacy_group"]
    overrides = config["legacy_instance_y_overrides_mm"]
    y_moves = drive_teeth.INSTANCE_Y_MOVES
    deleted = drive_teeth.DELETED_INSTANCES
    placed = []
    for item in master["instances"]:
        if item["group"] == excluded or item["name"] in EXCLUDED_LEGACY_INSTANCES:
            continue
        if item["name"] in deleted:
            continue
        if item["name"] in drive_teeth.INSTANCE_PART:
            # Real toothed gears/sprockets retain the part-local placement path.
            shape = drive_teeth.replacement_local_solid(item["name"])
            replaced = True
        else:
            shape = cq.importers.importStep(str(REPO/"cad/parts"/(item["part"]+".step"))).val()
            replaced = False
        axis_angle = item["rotation"]
        if axis_angle[3]:
            shape = shape.rotate((0, 0, 0), tuple(axis_angle[:3]), axis_angle[3])
        at = list(item["at"])
        if item["name"] in overrides:
            at[1] = overrides[item["name"]]
        # Stage 4: relocated chain-B planes and lower mesh removal.
        if item["name"] in y_moves:
            at[1] = y_moves[item["name"]]
        shape = shape.translate(tuple(at))
        if item["name"] == "S1-SHAFT-B_001":
            # Extend S1B beyond the rear cap and frame beam; the integral
            # 24T driver at y401..409 clears the S1A chain-A sprocket.
            extension = cq.Solid.makeCylinder(
                12.5, 65.0, cq.Vector(190.0, 349.0, 398.30275184708404),
                cq.Vector(0, 1, 0))
            blank = drive_teeth._sprocket_local_solid(
                "DRV-SP24-B25", hub_len=1.0).translate(
                    (190.0, 401.0, 398.30275184708404))
            core = cq.Solid.makeCylinder(
                12.7, 8.0, cq.Vector(190.0, 401.0, 398.30275184708404),
                cq.Vector(0, 1, 0))
            shape = shape.fuse(extension).fuse(blank).fuse(core).clean()
            if len(shape.Solids()) != 1:
                raise RuntimeError("S1B integral belt sprocket split")
        keyseat_removed = 0.0
        if item["name"] == "DRV-JACK_001":
            # The added chain-B 24T driver has a second +Z key at y373..387.8.
            # Preserve the continuous shaft core and its existing first key.
            seat = cq.Solid.makeBox(
                6.2, 15.0, 3.7,
                cq.Vector(at[0] - 3.1, 372.9, at[2] + 6.5))
            original_volume = shape.Volume()
            shape = shape.cut(seat).clean()
            keyseat_removed = original_volume - shape.Volume()
            if len(shape.Solids()) != 1:
                raise RuntimeError("jackshaft split by second keyseat")
        placed.append({"name": item["name"], "part": item["part"],
                       "group": item["group"], "shape": shape,
                       "relocated": item["name"] in overrides or item["name"] in y_moves,
                       "replaced": replaced,
                       "keyseat_removed_mm3": round(keyseat_removed, 3)})
    name, at = drive_teeth.CHAIN_B_DRIVER_INSTANCE
    shape = drive_teeth.replacement_local_solid(name).translate(tuple(at))
    placed.append({"name": name, "part": "DRV-SP24-B20", "group": "drive",
                   "shape": shape, "relocated": True, "replaced": True})
    key_at = (at[0], 373.0, at[2])
    key = cq.importers.importStep(str(REPO/"cad/parts/KEY-6-16.step")).val()
    key = key.intersect(cq.Solid.makeBox(
        6.2, 14.8, 6.2, cq.Vector(-3.1, 0.0, 6.4))).clean()
    placed.append({"name": "KEY-6-16_002", "part": "KEY-6-16",
                   "group": "drive", "shape": key.translate(key_at),
                   "relocated": True, "replaced": False})
    return placed

def c21_parts(config):
    transform = config["c2_subassembly_transform"]
    axis = tuple(transform["rotation_axis"])
    angle = transform["rotation_deg"]
    translation = tuple(transform["translation_mm"])
    # VP1 Stage 2: the placeholder guard envelope is replaced by real guards
    return [{"name": name, "part": name, "group": "S2-C2.1",
             "shape": shape.rotate((0, 0, 0), axis, angle).translate(translation),
             "relocated": True}
            for name, shape in components()
            if name != "GUARD_SECTION_ENVELOPE_HOLD"]


def collision_audit(changed, stable, allowed=None, known=None):
    allowed = allowed or set()
    known = known or set()
    checks = 0
    candidates = 0
    failures = []
    known_hits = []
    for item in changed:
        for other in stable:
            if item is other:
                continue
            checks += 1
            pair = frozenset((item["name"], other["name"]))
            if not bbox_overlap(item["shape"], other["shape"]):
                continue
            candidates += 1
            volume = item["shape"].intersect(other["shape"]).Volume()
            if volume > 0.05:
                if pair in allowed:
                    continue
                if pair in known:
                    known_hits.append({"a": item["name"], "b": other["name"],
                                       "overlap_mm3": volume})
                    continue
                failures.append({"a": item["name"], "b": other["name"],
                                 "overlap_mm3": volume})
    return {"method": "BREP_EXACT_AFTER_BBOX", "pair_checks": checks,
            "bbox_candidates": candidates, "unexpected": failures,
            "functional_allowed": sorted("/".join(sorted(p)) for p in allowed),
            "known_contacts": known_hits,
            "passed": not failures}


def rotor_feed_phase_collision(chute_parts, transform):
    """Check the moving S2 rotor against fixed feed metal, not just theta=0.

    Five-degree samples cover q input turns; a separate axial/radial bound
    covers the entire rotor phase for these two feed parts. Neither proves
    material transport, loaded deflection, or the rest of the machine.
    """
    c = Transmission()
    rotor = local_rotor(c)
    feed = {item["name"]: item["shape"] for item in chute_parts}
    axis = tuple(transform["rotation_axis"])
    offset = tuple(transform["translation_mm"])
    # Axial separation of the wide receiving flight from the coupling web
    # plus radial separation of the narrow tail and outer shell from both
    # orbiting web and hooks gives a continuous conservative bound. The
    # cycloid slab starts only at global y307, beyond the feed.
    receiving_end = chute_mod._cross_feed_flight(
        chute_mod.CROSS_FLIGHT_Y0, chute_mod.CROSS_FLIGHT_Y1,
        chute_mod.CROSS_FLIGHT_RO).BoundingBox().ymax
    rotor_reach = max(c.rotor_tip_diameter_mm / 2.0, 54.5) + c.eccentric_mm
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    tail = chute_mod._cross_feed_flight(
        chute_mod.CROSS_FLIGHT_Y1, chute_mod.CROSS_TAIL_Y1,
        chute_mod.CROSS_TAIL_RO,
        phase_deg=360.0 * (chute_mod.CROSS_FLIGHT_Y1 -
                           chute_mod.CROSS_FLIGHT_Y0) / chute_mod.CROSS_PITCH)
    tb = tail.BoundingBox()
    radial_envelope = cq.Solid.makeCylinder(
        rotor_reach, tb.ymax - tb.ymin + 2.0,
        cq.Vector(offset[0], tb.ymin - 1.0, offset[2]), cq.Vector(0, 1, 0))
    tail_margin = BRepExtrema_DistShapeShape(
        tail.wrapped, radial_envelope.wrapped).Value()
    shell_margin = chute_mod.ROTOR_RADIAL_RELIEF_R - rotor_reach
    envelope_passed = (receiving_end < 235.0
                       and tail_margin >= 0.5 and shell_margin >= 1.0
                       and feed["CROSS_FEED_SHELL"].BoundingBox().ymax <= 260.01)
    hits = []
    for degrees in range(0, c.q * 360, 5):
        shape = moved(rotor, math.radians(degrees), c)
        shape = shape.rotate((0, 0, 0), axis, transform["rotation_deg"]).translate(offset)
        for name in ("CROSS_FEED_SHAFT", "CROSS_FEED_SHELL"):
            fixed = feed[name]
            if not bbox_overlap(shape, fixed):
                continue
            volume = shape.intersect(fixed).Volume()
            if volume > 1e-5:
                hits.append({"input_deg": degrees, "fixed": name,
                             "overlap_mm3": round(volume, 6)})
    return {"method": "BREP_EXACT_SAMPLED_5_DEG_PLUS_AXIAL_RADIAL_BOUND",
            "samples": c.q * 72,
            "checked_feed_parts": ["CROSS_FEED_SHAFT", "CROSS_FEED_SHELL"],
            "unexpected": hits, "passed": not hits and envelope_passed,
            "continuous_clearance_proven": envelope_passed,
            "receiving_flight_ymax_mm": round(receiving_end, 3),
            "tail_radial_margin_mm": round(tail_margin, 3),
            "shell_radial_margin_mm": round(shell_margin, 3)}


def extent(records):
    compound = cq.Compound.makeCompound([item["shape"] for item in records])
    b = bounds(compound)
    return {"bounds_mm": b, "size_mm": [b[i+3]-b[i] for i in range(3)]}


def assembly_geometry_checks(chute_parts, imported_solids):
    """Verify that the exported STEP retains the active chute and auger.

    This is deliberately measured on reimported solids rather than only on
    the construction shapes: a successful export call alone proves little.
    """
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    shapes = {item["name"]: item["shape"] for item in chute_parts}

    def imported(name, tolerance=0.25):
        expected = bounds(shapes[name])
        return next((solid for solid in imported_solids
                     if all(abs(a-b) < tolerance for a, b in
                            zip(bounds(solid), expected))), None)

    chute_matched = imported("CHUTE_BODY") is not None
    auger = imported("AUG_SHAFT")
    auger_matched = auger is not None
    belt = imported("S1_TRANSFER_BELT")
    old_ribs = any(
        any(lo - 0.3 <= b.xmin and b.xmax <= hi + 0.3
            and zlo - 0.3 <= b.zmin and b.zmax <= zhi + 0.3
            for b in (solid.BoundingBox(),))
        for lo, hi, zlo, zhi in ((172.0, 188.0, 335.0, 341.6),
                                (202.0, 210.0, 331.5, 338.2))
        for solid in imported_solids)
    floor_band = chute_mod.bypass_channel_floor().intersect(
        cq.Solid.makeBox(102.0, 30.0, 11.0, cq.Vector(260.0, 213.0, 334.0)))
    clearance = (BRepExtrema_DistShapeShape(auger.wrapped, floor_band.wrapped).Value()
                 if auger is not None else None)
    auger_zmin = bounds(auger)[2] if auger is not None else None
    # At the original east drum x239, the raised center belt shared only
    # 5 mm of screw-flight length; flakes fell below the flight at x242.
    # A longer powered coincidence is a necessary geometric opportunity,
    # not evidence of pickup under load or a substitute for a flow run.
    belt_overlap = (max(0.0, min(belt.BoundingBox().xmax, chute_mod.AUG_FLIGHT_X1)
                        - max(belt.BoundingBox().xmin, chute_mod.AUG_FLIGHT_X0))
                    if belt is not None else None)
    belt_gap = (BRepExtrema_DistShapeShape(belt.wrapped, auger.wrapped).Value()
                if belt is not None and auger is not None else None)
    cross_feed = imported("CROSS_FEED_SHAFT")
    cross_shell = imported("CROSS_FEED_SHELL")
    tail = chute_mod._cross_feed_flight(
        chute_mod.CROSS_FLIGHT_Y1, chute_mod.CROSS_TAIL_Y1,
        chute_mod.CROSS_TAIL_RO)
    powered_overlap = max(0.0, tail.BoundingBox().ymax - chute_mod.TROUGH_Y0)
    outer_support = (cross_shell.intersect(chute_mod._box(
        359.0, 369.2, 255.0, 258.0, 315.0, 335.0)).Volume()
        if cross_shell is not None else None)
    cross_gap = (BRepExtrema_DistShapeShape(
        cross_feed.wrapped, cross_shell.wrapped).Value()
        if cross_feed is not None and cross_shell is not None else None)
    checks = {
        "chute_body_matched": chute_matched,
        "aug_shaft_matched": auger_matched,
        "transfer_belt_matched": belt is not None,
        "transfer_belt_flight_overlap_mm": round(belt_overlap, 3) if belt_overlap is not None else None,
        "transfer_belt_auger_gap_mm": round(belt_gap, 3) if belt_gap is not None else None,
        "cross_feed_matched": cross_feed is not None,
        "cross_shell_matched": cross_shell is not None,
        "cross_feed_powered_mouth_overlap_mm": round(powered_overlap, 3),
        "cross_feed_outer_support_mm3": (
            round(outer_support, 3) if outer_support is not None else None),
        "cross_feed_shell_clearance_mm": (
            round(cross_gap, 3) if cross_gap is not None else None),
        "old_rib_solids_present": old_ribs,
        "aug_shaft_zmin": round(auger_zmin, 3) if auger_zmin is not None else None,
        "exact_min_distance_mm": round(clearance, 3) if clearance is not None else None,
        "passed": (chute_matched and auger_matched and belt is not None and not old_ribs
                   and auger_zmin is not None
                   and abs(auger_zmin - (chute_mod.AUG_AX_Z - chute_mod.AUG_FLIGHT_RO)) < 0.5
                   and clearance is not None and 1.0 <= clearance <= 2.0
                   and belt_overlap is not None
                   and belt_overlap >= 0.75 * chute_mod.AUG_FLIGHT_PITCH
                   and belt_gap is not None and 0.1 <= belt_gap <= 1.5
                   and cross_feed is not None and cross_shell is not None
                   and powered_overlap >= 4.0
                   and outer_support is not None and outer_support >= 30.0
                   and cross_gap is not None and 0.15 <= cross_gap <= 1.0),
    }
    return checks


def main():
    config_path = C21/"design/machine_integration.json"
    config = json.loads(config_path.read_text())
    master_path = REPO/config["legacy_master"]
    master = json.loads(master_path.read_text())
    legacy = legacy_parts(master, config)
    c21 = c21_parts(config)
    relocated_legs = [item for item in legacy if item["relocated"]]
    stable = [item for item in legacy if not item["relocated"]]

    interface = collision_audit(c21, legacy)
    relocated = collision_audit(
        relocated_legs, stable,
        allowed={frozenset(p) for p in drive_teeth._FUNCTIONAL_KEY_PAIRS})
    # --- VP1 Stage 1: real drivetrain + chute --------------------------------
    replaced = [item for item in legacy if item.get("replaced")]
    chain_parts = [{"name": name, "part": name, "group": "drive",
                    "shape": solid, "relocated": False, "replaced": True}
                   for name, solid in drive_teeth.chain_components()]
    chute_parts = [{"name": name, "part": name, "group": "feed",
                    "shape": solid, "relocated": False, "replaced": True}
                   for name, solid, group in chute_mod.components()]
    guard_parts = [{"name": name, "part": name, "group": "guard",
                    "shape": solid, "relocated": False, "replaced": True}
                   for name, solid in guards_mod.components()]
    winder_parts = [{"name": name, "part": name, "group": group,
                     "shape": solid, "relocated": False, "replaced": True}
                    for name, solid, group in winder_mod.components()]
    electrical_parts = [{"name": name, "part": name, "group": "electrical",
                         "shape": solid, "relocated": False, "replaced": True}
                        for name, solid in electrical_mod.components()]
    # --- VP1 Stage 3: chain/gear path reliefs into frozen legacy structure --
    new_solids = {r["name"]: r["shape"] for r in
                  legacy if r.get("replaced")}
    new_solids.update({r["name"]: r["shape"] for r in
                       chain_parts + chute_parts + guard_parts + winder_parts
                       + electrical_parts})
    relief_records, relieved = chain_relief.apply(legacy, new_solids)
    relieved.add("KEY-6-16_002")
    relief_records.append({
        "legacy": "KEY-6-16_002", "new": "BR-6204_002",
        "kind": "trim", "applied": True,
        "note": "second jack driver key cut to 14.8 mm; 0.2 mm axial clearance "
                "before bearing at y388"})
    relieved.add("DRV-JACK_001")
    relief_records.append({
        "legacy": "DRV-JACK_001", "new": "KEY-6-16_002",
        "kind": "keyseat", "applied": True,
        "removed_mm3": next(x["keyseat_removed_mm3"] for x in legacy
                            if x["name"] == "DRV-JACK_001"),
        "note": "second chain-B keyseat y372.9..387.9, continuous metal core"})
    allowed_pairs = {frozenset(p) for p in drive_teeth.FUNCTIONAL_PAIRS}
    known_pairs = set()  # Stage 3 reliefs resolved the former layout contacts
    vp1_parts = (replaced + chain_parts + chute_parts + guard_parts
                 + winder_parts + electrical_parts)
    vp1_against = collision_audit(vp1_parts, stable + c21,
                                  allowed=allowed_pairs, known=known_pairs)
    vp1_internal = collision_audit(vp1_parts, vp1_parts,
                                   allowed=allowed_pairs, known=known_pairs)
    all_parts = (legacy + c21 + chain_parts + chute_parts + guard_parts
                 + winder_parts + electrical_parts)
    # export relieved legacy solids so the native FreeCAD build consumes the
    # same geometry
    for name in sorted(relieved):
        item = next(x for x in all_parts if x["name"] == name)
        path = C21 / "cad/parts_stage1" / (name + ".step")
        path.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(cq.Compound.makeCompound([item["shape"]]), str(path))
    compound = cq.Compound.makeCompound([item["shape"] for item in all_parts])
    out = C21/"cad/PPR_VP1.step"
    cq.exporters.export(compound, str(out))
    normalize_step_timestamp(out)
    imported = cq.importers.importStep(str(out))
    imported_solids = imported.solids().vals()
    geometry_checks = assembly_geometry_checks(chute_parts, imported_solids)
    rotor_feed_audit = rotor_feed_phase_collision(chute_parts, config["c2_subassembly_transform"])

    body = [item for item in all_parts if item["group"] not in config["body_excluded_groups"]]
    body_extent = extent(body)
    operating_extent = extent(all_parts)
    body_extent["limit_mm"] = config["body_limit_mm"]
    body_extent["passed"] = all(actual <= limit+1e-6 for actual, limit in
                                  zip(body_extent["size_mm"], config["body_limit_mm"]))
    operating_extent["target_limit_mm"] = config["operating_envelope_limit_mm"]
    operating_extent["passed"] = all(actual <= limit+1e-6 for actual, limit in
                                       zip(operating_extent["size_mm"], config["operating_envelope_limit_mm"]))

    groups = sorted({item["group"] for item in all_parts})
    required = {"S1", "S2-C2.1", "feed", "extruder", "cooling", "puller",
                "spool", "electrical", "frame", "frame_mount", "drive"}
    ratio = drive_teeth.ratio_chain()
    result = {
        "revision": config["revision"] + "+VP1-STAGE1",
        "status": "DIGITAL_MACHINE_INTEGRATION_PASS_RELEASE_HOLD"
                  if interface["passed"] and relocated["passed"]
                  and body_extent["passed"] and operating_extent["passed"]
                  and vp1_against["passed"] and vp1_internal["passed"]
                  and geometry_checks["passed"] and rotor_feed_audit["passed"]
                  else "DIGITAL_MACHINE_INTEGRATION_HOLD",
        "source": {
            "config": str(config_path.relative_to(REPO)),
            "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
            "legacy_master": str(master_path.relative_to(REPO)),
            "legacy_master_sha256": hashlib.sha256(master_path.read_bytes()).hexdigest(),
            "c21_builder_sha256": hashlib.sha256((C21/"src/build_cad.py").read_bytes()).hexdigest(),
            "legacy_role": "C1 interface baseline; motors/gears/screw/electrical/procurement remain unqualified"
        },
        "transform": config["c2_subassembly_transform"],
        "legacy_s2_instances_excluded": sum(item["group"] == config["excluded_legacy_group"]
                                             for item in master["instances"]),
        "legacy_instances_retained": len(legacy),
        "c21_instances_inserted": len(c21),
        "assembly_objects": len(all_parts),
        "expected_solids": sum(len(item["shape"].Solids()) for item in all_parts),
        "reimported_solids": len(imported_solids),
        "step_reimport_valid": all(shape.isValid() for shape in imported_solids),
        "assembly_step": str(out.relative_to(REPO)),
        "assembly_geometry_checks": geometry_checks,
        "rotor_feed_phase_collision": rotor_feed_audit,
        "assembly_step_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "assembly_step_bytes": out.stat().st_size,
        "groups": groups,
        "required_groups_present": sorted(required.intersection(groups)),
        "missing_required_groups": sorted(required.difference(groups)),
        "body": body_extent,
        "operating_envelope": operating_extent,
        "interface_collision": interface,
        "relocated_support_collision": relocated,
        "relocated_supports": {name: y for name, y in config["legacy_instance_y_overrides_mm"].items()},
        "vp1_stage1": {
            "drive_replacements": sorted(drive_teeth.INSTANCE_PART),
            "chain_parts": ["DRV-CHAIN-A", "DRV-CHAIN-B"],
            "chute_parts": [it["name"] for it in chute_parts],
            "guard_parts": [it["name"] for it in guard_parts],
            "winder_parts": [it["name"] for it in winder_parts],
            "electrical_parts": [it["name"] for it in electrical_parts],
            "excluded_legacy_instances": sorted(EXCLUDED_LEGACY_INSTANCES),
            "deleted_drive_instances": sorted(drive_teeth.DELETED_INSTANCES),
            "chain_relief_adr": "c2.1/docs/ADR-002-CHAIN-ROUTING.md",
            "electrical_load": electrical_mod.load_inventory(),
            "vp1_stage3": {
                "adr": "c2.1/docs/ADR-002-CHAIN-ROUTING.md",
                "relief_records": relief_records,
                "relieved_instances": sorted(relieved),
            },
            "kinematic_chain": ratio,
            "vp1_against_retained": vp1_against,
            "vp1_internal": vp1_internal,
            "notes": [
                "gear mesh phase: pinion tooth centre on the line of centres, "
                "40T space centre at 180deg; helix hands opposed per mesh pair",
                "ADR-002 rev B (VP1 Stage 4): chain B is driven from the "
                "jackshaft 24T bore-10 sprocket DRV-SP24-B20_002 (y373) "
                "to S2 12T (y374), 76 links; the jackshaft is one solid, "
                "the duplicate lower helical mesh is removed, and the "
                "DRV-M2 reference motor body is intact",
                f"At the {ratio['input_rpm']:g} rpm M1 reference the 15T/40T "
                f"mesh and 24T/12T chain B give S2 eccentric "
                f"{ratio['s2_ecc_rpm']:g} rpm; the 2-start/16T worm wheel "
                f"drives the auger at {ratio['auger_rpm']:g} rpm",
                "The fin-bypass feed uses a driven four-turn auger in an "
                "open U cradle with a measured positive flight/floor gap; "
                "the flat structural slab is not a passive transport claim",
                "puller nip: spring-loaded 1.75 mm filament grip; spool "
                "winder, traverse and slip tensioner replace SPOOL-ENV",
                "power policy: 500 W hard modeled operational budget; "
                "normal virtual peak 416 W, above-500 W demands rejected; "
                "792 W is the separate PSU current-derived ceiling, not an "
                "operating allowance; M1/M2 loads remain UNRATED estimates",
                "retained-internal S1-SYNC_001/002 vs S1-BR-CAP_001 contacts "
                "are inherited from C1 and not audited by this build",
            ],
        },
        "closed_interfaces": [
            "S2 process interval Y255..295 mm replaces the legacy S2 chamber interval",
            "S2 input shaft remains coaxial with the retained ANSI35 12T bore12 reference at X308.569/Z280",
            "four legacy metal S2 legs are relocated to face-contact the C2.1 support plates",
            "S1/feed/extruder/cooling/puller/spool/electrical/frame objects are retained in one assembly"
        ],
        "holds": [
            "C1 M1/M2, gears, sprockets, screw and electrical parts are interface references, not final selections",
            "support fastener grade/preload, weld detail and frame stiffness are not rated",
            "guards, wiring routes, service sweep and anti-reach are not complete containment geometry",
            "full unchanged C1 pair audit is inherited; this run checks every new/relocated-to-retained pair",
            "loaded deflection, tolerance and thermal-growth collision are not proven"
        ],
        **config["release"]
    }
    (C21/"results/machine_integration.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {"closed_interfaces", "holds"}}, indent=2))
    if (result["status"] != "DIGITAL_MACHINE_INTEGRATION_PASS_RELEASE_HOLD"
            or result["expected_solids"] != result["reimported_solids"]
            or not result["step_reimport_valid"] or result["missing_required_groups"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
