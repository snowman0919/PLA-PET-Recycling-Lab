"""Build and verify the C2.1 S2 subassembly inside the complete C1 machine.

C1 is reused as an interface baseline, not as a release of its motors, gears,
screw, electrical system, guards, or procurement choices.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

import cadquery as cq

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(C21/"src"))
from build_cad import components
import drive_teeth
import chute as chute_mod
import guards as guards_mod
import winder as winder_mod
import electrical_bay as electrical_mod
import chain_relief

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
    placed = []
    for item in master["instances"]:
        if item["group"] == excluded or item["name"] in EXCLUDED_LEGACY_INSTANCES:
            continue
        if item["name"] in drive_teeth.INSTANCE_PART:
            # VP1 Stage 1: real toothed gear/sprocket solid, same part id and
            # instance name (part-local frame, same rotate/translate path).
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
        shape = shape.translate(tuple(at))
        placed.append({"name": item["name"], "part": item["part"],
                       "group": item["group"], "shape": shape,
                       "relocated": item["name"] in overrides,
                       "replaced": replaced})
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


def extent(records):
    compound = cq.Compound.makeCompound([item["shape"] for item in records])
    b = bounds(compound)
    return {"bounds_mm": b, "size_mm": [b[i+3]-b[i] for i in range(3)]}


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
    relocated = collision_audit(relocated_legs, stable)
    # --- VP1 Stage 1: real drivetrain + chute --------------------------------
    replaced = [item for item in legacy if item.get("replaced")]
    chain_parts = [{"name": name, "part": name, "group": "drive",
                    "shape": solid, "relocated": False, "replaced": True}
                   for name, solid in drive_teeth.chain_components()]
    chute_parts = [{"name": name, "part": name, "group": "feed",
                    "shape": solid, "relocated": False, "replaced": True}
                   for name, solid in chute_mod.components()]
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
    out = C21/"cad/PPR_C2_1_machine_integration.step"
    cq.exporters.export(compound, str(out))
    normalize_step_timestamp(out)
    imported = cq.importers.importStep(str(out))
    imported_solids = imported.solids().vals()

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
    result = {
        "revision": config["revision"] + "+VP1-STAGE1",
        "status": "DIGITAL_MACHINE_INTEGRATION_PASS_RELEASE_HOLD"
                  if interface["passed"] and relocated["passed"]
                  and body_extent["passed"] and operating_extent["passed"]
                  and vp1_against["passed"] and vp1_internal["passed"]
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
            "chain_relief_adr": "c2.1/docs/ADR-002-CHAIN-ROUTING.md",
            "electrical_load": electrical_mod.load_inventory(),
            "vp1_stage3": {
                "adr": "c2.1/docs/ADR-002-CHAIN-ROUTING.md",
                "relief_records": relief_records,
                "relieved_instances": sorted(relieved),
            },
            "kinematic_chain": drive_teeth.ratio_chain(),
            "vp1_against_retained": vp1_against,
            "vp1_internal": vp1_internal,
            "notes": [
                "gear mesh phase: pinion tooth centre on the line of centres, "
                "40T space centre at 180deg; helix hands opposed per mesh pair",
                "chain A vs S1-ROOF-R_001 collision inherited from the frozen "
                "C1 layout (bracket blocks the chain wrap) - recorded as "
                "known contact, layout fix required",
                "S2 input from chain B is 116 rpm, not the 120 rpm ADR-001 "
                "nominal (58 rpm M1 * 24/12); S2 q=8 model unchanged",
                "chute slope defect: frozen datums leave only ~6.5 mm between "
                "the S1 bottom and the S2 shell outer apex; a >=45deg sliding "
                "path is impossible, floor is near-flat (batch accumulation "
                "transport); the 115deg saddle fin is BYPASSED (route south "
                "of the chamber, path_check trough_fin_gap PASS)",
                "puller nip opened to 2.5 mm minimum with a positive stop "
                "(frozen envelope pair gave 1.8 mm); spool winder + traverse "
                "+ slip tensioner replace the SPOOL-ENV envelope",
                "electrical peak load 616 W EXCEEDS the 500 W operating cap "
                "(-116 W headroom) with all three band heaters at nameplate; "
                "M1/M2 loads are UNRATED estimates (motors not owned)",
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
