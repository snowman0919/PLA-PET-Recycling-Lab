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
        if item["group"] == excluded:
            continue
        shape = cq.importers.importStep(str(REPO/"cad/parts"/(item["part"]+".step"))).val()
        axis_angle = item["rotation"]
        if axis_angle[3]:
            shape = shape.rotate((0, 0, 0), tuple(axis_angle[:3]), axis_angle[3])
        at = list(item["at"])
        if item["name"] in overrides:
            at[1] = overrides[item["name"]]
        shape = shape.translate(tuple(at))
        placed.append({"name": item["name"], "part": item["part"],
                       "group": item["group"], "shape": shape,
                       "relocated": item["name"] in overrides})
    return placed


def c21_parts(config):
    transform = config["c2_subassembly_transform"]
    axis = tuple(transform["rotation_axis"])
    angle = transform["rotation_deg"]
    translation = tuple(transform["translation_mm"])
    return [{"name": name, "part": name, "group": "S2-C2.1",
             "shape": shape.rotate((0, 0, 0), axis, angle).translate(translation),
             "relocated": True}
            for name, shape in components()]


def collision_audit(changed, stable):
    checks = 0
    candidates = 0
    failures = []
    for item in changed:
        for other in stable:
            checks += 1
            if not bbox_overlap(item["shape"], other["shape"]):
                continue
            candidates += 1
            volume = item["shape"].intersect(other["shape"]).Volume()
            if volume > 0.05:
                failures.append({"a": item["name"], "b": other["name"],
                                 "overlap_mm3": volume})
    return {"method": "BREP_EXACT_AFTER_BBOX", "pair_checks": checks,
            "bbox_candidates": candidates, "unexpected": failures,
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
    all_parts = legacy+c21
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
        "revision": config["revision"],
        "status": "DIGITAL_MACHINE_INTEGRATION_PASS_RELEASE_HOLD"
                  if interface["passed"] and relocated["passed"]
                  and body_extent["passed"] and operating_extent["passed"]
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
