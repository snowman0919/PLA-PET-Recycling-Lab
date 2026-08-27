"""Generate the initial module-envelope and frame assembly skeleton."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

COMMON = Path(__file__).resolve().parents[1] / "common"
sys.path.insert(0, str(COMMON))
from project import ROOT, add_feature, export_document, load_parameters  # noqa: E402


def box(doc, name, label, part_id, xyz, size, material):
    shape = Part.makeBox(*size, App.Vector(*xyz))
    return add_feature(doc, name, label, shape, part_id, material)


def build():
    p = load_parameters()["assembly"]
    doc = App.newDocument("FullAssemblySkeleton")
    objects = []

    # Four 4040 posts and base/top rails: envelope, not detailed extrusion profiles.
    w, d, h = p["tower_width_mm"], p["tower_depth_mm"], p["tower_height_mm"]
    for i, (x, y) in enumerate(((0, 0), (w - 40, 0), (0, d - 40), (w - 40, d - 40))):
        objects.append(box(doc, f"FramePost{i+1}", f"FRM-POST-{i+1}", f"FRM-POST-{i+1}", (x, y, 0), (40, 40, h), "Aluminum profile 4040"))
    for i, (x, y, z, sx, sy) in enumerate((
        (0, 0, 0, w, 40), (0, d-40, 0, w, 40),
        (0, 0, h-40, w, 40), (0, d-40, h-40, w, 40),
        (0, 0, 0, 40, d), (w-40, 0, 0, 40, d),
    )):
        objects.append(box(doc, f"FrameRail{i+1}", f"FRM-RAIL-{i+1}", f"FRM-RAIL-{i+1}", (x, y, z), (sx, sy, 40), "Aluminum profile 4040"))

    modules = [
        ("InputClassifier", "MOD-INPUT", (60, 70, 560), (320, 220, 120)),
        ("ShredderStage1", "MOD-SHRED-1", (90, 100, 440), (260, 160, 105)),
        ("ShredderStage2", "MOD-SHRED-2", (105, 110, 325), (230, 140, 95)),
        ("GranulatorStage3", "MOD-SHRED-3", (115, 115, 210), (210, 130, 95)),
        ("VibratorySorter", "MOD-SORTER", (80, 80, 90), (280, 200, 95)),
        # The dryer and extruder use their validated proof envelopes.  They are
        # separated laterally so a flexible, grounded metal transfer tube can
        # connect the auger outlet to the cooled feed throat without occupying
        # the hot-line service corridor.
        ("DryerFeeder", "MOD-DRYER", (470, 0, 60), (320, 270, 580)),
        ("Extruder", "MOD-EXTRUDER", (450, 300, 40), (850, 220, 240)),
        # Forming and spooler envelopes now match their proof CAD.  Their small
        # X overlap is the guarded dancer/threading transition, not a rigid
        # component collision.
        ("CoolingGaugePuller", "MOD-COOL-GAUGE-PULLER", (1228, 330, 40), (760, 160, 180)),
        ("Spooler", "MOD-SPOOLER", (1940, 270, 20), (355, 240, 320)),
        ("ControlEnclosure", "MOD-CONTROL", (820, 20, 60), (300, 220, 180)),
    ]
    for name, part_id, xyz, size in modules:
        objects.append(box(doc, name, part_id, part_id, xyz, size, "Envelope only"))

    outputs = export_document(doc, "full_assembly_skeleton", objects)
    overall = doc.addObject("PartDesign::Feature", "OverallEnvelope")
    overall.Label = "REFERENCE-OVERALL-ENVELOPE"
    overall.Shape = Part.makeCompound([o.Shape for o in objects])
    bb = overall.Shape.BoundBox
    report = {
        "revision": load_parameters()["revision"],
        "overall_mm": {"x": round(bb.XLength, 1), "y": round(bb.YLength, 1), "z": round(bb.ZLength, 1)},
        "module_count": len(modules),
        "notes": [
            "Module solids are keep-out envelopes, not fabrication geometry.",
            "Dryer, extruder, cooling/gauge/puller and spooler envelopes match their current proof CAD.",
            "The 2.295 m by 0.52 m workbench footprint preserves about 0.96 m from die to loaded-spool centreline.",
            "Tower center of mass and anchoring require later validation.",
            "No safety acceptance may be inferred from this skeleton.",
        ],
        "outputs": outputs,
    }
    report_path = ROOT / "validation" / "visual_review" / "full_assembly_skeleton.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
