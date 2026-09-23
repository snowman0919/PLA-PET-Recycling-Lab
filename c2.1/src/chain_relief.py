"""VP1 Stage 3/4: parametric relief/notch bodies for the real chain and gear
paths against retained legacy structure (ADR-002-CHAIN-ROUTING.md rev B).

C1 root sources stay frozen: the reliefs are applied AT INTEGRATION TIME to
the retained legacy instance solids inside build_machine_integration.py, and
each relieved solid is exported to c2.1/cad/parts_stage1/<instance>.step so
the native FreeCAD build consumes the same relieved geometry.

ADR-002 rev B (VP1 Stage 4) supersedes rev A's frozen-layout reading: legacy
instances may be MOVED/REPLACED at integration.  With the Stage 4 layout the
two function-destroying rev A reliefs are GONE:
- DRV-JACK_001: the jackshaft is ONE SOLID again (chain B now leaves the
  jackshaft 24T sprocket tangentially - the strand never returns to the jack
  core; the rev A sever y 370..378.5 and the RJ_COUPLING sleeve are deleted).
- DRV-M2_001: untouched (the doubled lower helical mesh that forced the
  8336 mm3 pocket is deleted; the reference motor body is intact).

The remaining reliefs are small corner/wrap channels whose removal does not
delete a part's function.

Generic pocket rule: pocket = bbox(contact solid intersect legacy solid)
expanded by the spec margin (1.5 mm) on all sides; the pocket box is cut from
the legacy solid and the removed volume is measured and recorded.  Two
contacts keep non-generic treatment:
- S1-STUD_001: trim tail (box spans to the stud end so the wall-to-wall
  tie span y 108..329.6 is preserved; only the y>330.5 overhang is removed).
- DRV-DECK_001 vs DRV_SH40R_upper: the 40T gear tip circle dips 3.4 mm below
  the deck top plane; the pocket is a wrap channel through the deck edge.
"""
from __future__ import annotations

import cadquery as cq

V = cq.Vector

MARGIN = 1.5

# (legacy_instance, new_part, kind, note)
RELIEFS = [
    ("S1-ROOF-R_001", "DRV-CHAIN-A", "pocket",
     "chain A top-wrap channel notch in the roof bracket corner (bracket "
     "load path and bolt seats preserved)"),
    ("S1-STUD_001", "DRV-CHAIN-A", "trim",
     "stud tail trimmed beyond the wall face (y>330.5): wall-to-wall span "
     "y 108..329.6 preserved; the chain A strand owns the freed volume"),
    ("DRV-B12_001", "DRV-CHAIN-A", "pocket",
     "corner relief on the input-shaft rear bearing plate (bearing seat at "
     "x 74..86 untouched)"),
    ("DRV-DECK_001", "DRV-CHAIN-A", "pocket", "deck relief for strand A"),
    ("DRV-DECK_001", "DRV-CHAIN-B", "pocket", "deck relief for strand B"),
    ("DRV-DECK_001", "DRV_SH40R_upper", "pocket",
     "deck relief for the 40T gear tip circle"),
]


def _bbox_box(shape, margin):
    b = shape.BoundingBox()
    return cq.Solid.makeBox(
        b.xmax - b.xmin + 2 * margin, b.ymax - b.ymin + 2 * margin,
        b.zmax - b.zmin + 2 * margin,
        V(b.xmin - margin, b.ymin - margin, b.zmin - margin))


def apply(legacy, new_by_name):
    """Cut relief pockets into the named legacy instance solids.

    legacy: list of integration part records (mutated in place).
    new_by_name: {new_part_name: solid} for the relief tools.
    Returns the list of relief records for the results block and the set of
    relieved instance names.
    """
    index = {}
    for item in legacy:
        index.setdefault(item["name"], item)
    records = []
    relieved = set()
    for legacy_name, new_name, kind, note in RELIEFS:
        li = index.get(legacy_name)
        tool = new_by_name.get(new_name)
        if li is None or tool is None:
            raise RuntimeError("relief missing solid: %s/%s"
                               % (legacy_name, new_name))
        inter = li["shape"].intersect(tool)
        vols = [x.Volume() for x in inter.Solids() if x.Volume() > 0.05]
        overlap = sum(vols)
        if overlap <= 0.05:
            records.append({"legacy": legacy_name, "new": new_name,
                            "kind": kind, "applied": False, "removed_mm3": 0.0,
                            "note": note + " (no contact after earlier "
                                            "relief or envelope change)"})
            continue
        if kind == "trim":
            # trim box: removes everything beyond the wall face (y 329.6 +
            # 0.9 mm leaves a 1.4 mm nut seat) up to the part end
            b = inter.BoundingBox()
            ys = li["shape"].BoundingBox().ymax
            pocket = cq.Solid.makeBox(
                b.xmax - b.xmin + 2 * MARGIN, ys - 330.5,
                b.zmax - b.zmin + 2 * MARGIN,
                V(b.xmin - MARGIN, 330.5, b.zmin - MARGIN))
        else:
            pocket = _bbox_box(inter, MARGIN)
        cut = li["shape"].cut(pocket)
        pieces = [x for x in cut.Solids() if x.Volume() > 10.0]
        removed = li["shape"].Volume() - sum(x.Volume() for x in pieces)
        li["shape"] = cq.Compound.makeCompound(pieces).clean()
        relieved.add(legacy_name)
        records.append({"legacy": legacy_name, "new": new_name, "kind": kind,
                        "applied": True, "overlap_before_mm3": overlap,
                        "removed_mm3": round(removed, 3),
                        "pocket_solids": len(pieces), "note": note})
    return records, relieved
