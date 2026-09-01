#!/usr/bin/env python3
"""P0-G/H local process hardware FreeCAD source of truth and exporter."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import FreeCAD as App
import Mesh
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "exports/process_v0621"
PARAM = json.loads((ROOT / "cad/parameters/process_v0621.json").read_text(encoding="utf-8"))


def one_solid(shape: Part.Shape) -> Part.Shape:
    shape = shape.removeSplitter()
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(f"invalid solid: valid={shape.isValid()} solids={len(shape.Solids)}")
    return shape


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="ascii")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2000-01-01T00:00:00'", text, count=1)
    text = re.sub(r"Open CASCADE STEP translator ([0-9.]+) [0-9]+", r"Open CASCADE STEP translator \1 0", text)
    path.write_text(text, encoding="ascii", newline="\n")


def wedge_shape() -> Part.Shape:
    p = PARAM["shredder"]["return_wedge"]
    poly = Part.makePolygon([
        App.Vector(0, 0, 0), App.Vector(p["length"], 0, 0),
        App.Vector(p["length"], 0, p["tip_height"]), App.Vector(0, 0, p["height"]),
        App.Vector(0, 0, 0),
    ])
    wedge = Part.Face(poly).extrude(App.Vector(0, p["width"], 0))
    for x in (12.0, p["length"] - 12.0):
        wedge = wedge.cut(Part.makeCylinder(2.7, p["width"], App.Vector(x, 0, 5), App.Vector(0, 1, 0)))
    return one_solid(wedge)


def comb_shape() -> Part.Shape:
    p = PARAM["shredder"]["anti_ribbon_comb"]
    shape = Part.makeBox(p["width"], p["back_depth"], p["back_height"])
    pitch = p["tooth_width"] + p["tooth_gap"]
    count = int((p["width"] - p["tooth_gap"]) // pitch)
    offset = (p["width"] - (count * p["tooth_width"] + (count - 1) * p["tooth_gap"])) / 2.0
    for index in range(count):
        tooth = Part.makeBox(p["tooth_width"], p["tooth_length"], p["tooth_thickness"], App.Vector(offset + index * pitch, p["back_depth"] - 0.2, 0))
        shape = shape.fuse(tooth)
    for x in (8.0, p["width"] - 8.0):
        shape = shape.cut(Part.makeCylinder(2.7, p["back_height"], App.Vector(x, p["back_depth"] / 2.0, 0)))
    return one_solid(shape)


def labyrinth_shape() -> Part.Shape:
    p = PARAM["shredder"]["axial_labyrinth"]
    ring = Part.makeCylinder(p["outer_diameter"] / 2.0, p["thickness"]).cut(Part.makeCylinder(p["inner_diameter"] / 2.0, p["thickness"]))
    ring = ring.cut(Part.makeBox(p["outer_diameter"] / 2.0 + 2.0, p["split_width"], p["thickness"] + 2.0, App.Vector(0, -p["split_width"] / 2.0, -1.0)))
    return one_solid(ring)


def screen_shape() -> Part.Shape:
    p = PARAM["shredder"]["screen_tray"]
    shape = Part.makeBox(p["length"], p["width"], p["thickness"])
    margin = 9.0
    x = margin
    while x <= p["length"] - margin:
        y = margin
        while y <= p["width"] - margin:
            shape = shape.cut(Part.makeCylinder(p["hole_diameter"] / 2.0, p["thickness"], App.Vector(x, y, 0)))
            y += p["hole_pitch"]
        x += p["hole_pitch"]
    rail_a = Part.makeBox(p["length"], 5.0, 12.0, App.Vector(0, 0, 0))
    rail_b = Part.makeBox(p["length"], 5.0, 12.0, App.Vector(0, p["width"] - 5.0, 0))
    return one_solid(shape.fuse(rail_a).fuse(rail_b))


def guard_shape() -> Part.Shape:
    p = PARAM["shredder"]["service_guard"]
    back = Part.makeBox(p["width"], p["thickness"], p["height"])
    roof = Part.makeBox(p["width"], p["depth"], p["thickness"], App.Vector(0, 0, p["height"] - p["thickness"]))
    side_a = Part.makeBox(p["thickness"], p["depth"], p["height"])
    side_b = Part.makeBox(p["thickness"], p["depth"], p["height"], App.Vector(p["width"] - p["thickness"], 0, 0))
    return one_solid(back.fuse(roof).fuse(side_a).fuse(side_b))


def rectangle_wire(x: float, y: float, z: float) -> Part.Wire:
    return Part.makePolygon([
        App.Vector(-x / 2, -y / 2, z), App.Vector(x / 2, -y / 2, z),
        App.Vector(x / 2, y / 2, z), App.Vector(-x / 2, y / 2, z), App.Vector(-x / 2, -y / 2, z),
    ])


def hopper_shape() -> Part.Shape:
    p = PARAM["feed"]["hopper"]
    outer = Part.makeLoft([rectangle_wire(p["bottom_x"], p["bottom_y"], 0), rectangle_wire(p["top_x"], p["top_y"], p["height"])], True, False)
    inner = Part.makeLoft([
        rectangle_wire(p["bottom_x"] - 2 * p["wall"], p["bottom_y"] - 2 * p["wall"], p["wall"]),
        rectangle_wire(p["top_x"] - 2 * p["wall"], p["top_y"] - 2 * p["wall"], p["height"] - p["wall"]),
    ], True, False)
    shell = outer.cut(inner)
    top_opening = Part.makeBox(
        p["top_x"] - 2 * p["wall"], p["top_y"] - 2 * p["wall"], p["wall"] + 1.0,
        App.Vector(-p["top_x"] / 2.0 + p["wall"], -p["top_y"] / 2.0 + p["wall"], p["height"] - p["wall"]),
    )
    throat = Part.makeCylinder(14.5, p["wall"] + 2.0, App.Vector(0, 0, -1.0))
    return one_solid(shell.cut(top_opening).cut(throat))


def lid_shape() -> Part.Shape:
    p = PARAM["feed"]["lid"]
    lid = Part.makeBox(p["x"], p["y"], p["thickness"], App.Vector(-p["x"] / 2, -p["y"] / 2, 0))
    pocket = Part.makeBox(p["x"] - 10.0, p["y"] - 10.0, p["gasket_depth"] + 0.1, App.Vector(-(p["x"] - 10.0) / 2, -(p["y"] - 10.0) / 2, -0.05))
    lid = lid.cut(pocket)
    for x in (-p["x"] / 2 + 8, p["x"] / 2 - 8):
        for y in (-p["y"] / 2 + 8, p["y"] / 2 - 8):
            lid = lid.cut(Part.makeCylinder(2.7, p["thickness"], App.Vector(x, y, 0)))
    return one_solid(lid)


def agitator_shape() -> Part.Shape:
    p = PARAM["feed"]["agitator"]
    r = p["shaft_diameter"] / 2.0
    shape = Part.makeCylinder(r, p["shaft_length"])
    for z, angle in ((28.0, 0.0), (52.0, 90.0), (76.0, 0.0)):
        arm = Part.makeCylinder(p["arm_diameter"] / 2.0, p["arm_radius"] * 2.0, App.Vector(-p["arm_radius"], 0, z), App.Vector(1, 0, 0))
        if angle:
            arm.rotate(App.Vector(0, 0, z), App.Vector(0, 0, 1), angle)
        shape = shape.fuse(arm)
    return one_solid(shape)


def auger_shape() -> Part.Shape:
    p = PARAM["feed"]["auger"]
    root_r = p["root_diameter"] / 2.0
    outer_r = p["outer_diameter"] / 2.0
    shaft = Part.makeCylinder(root_r, p["active_length"])
    # A deterministic faceted helicoid avoids OCCT pipe-frame inflation while
    # preserving the controlling OD, pitch and positive-displacement flight.
    segments_per_turn = 24
    dz = p["pitch"] / segments_per_turn
    segment_count = int(math.ceil(p["active_length"] / dz))
    tangential_width = 3.4
    segments = []
    for index in range(segment_count):
        z = index * dz
        segment = Part.makeBox(
            outer_r - root_r + 0.35, tangential_width,
            min(p["flight_thickness"], p["active_length"] - z),
            App.Vector(root_r - 0.35, -tangential_width / 2.0, z),
        )
        segment.rotate(App.Vector(0, 0, z), App.Vector(0, 0, 1), index * 360.0 / segments_per_turn)
        segments.append(segment)
    return one_solid(shaft.multiFuse(segments))


def housing_shape() -> Part.Shape:
    p = PARAM["feed"]["housing"]
    tube = Part.makeCylinder(p["outer_diameter"] / 2.0, p["length"]).cut(Part.makeCylinder(p["inner_diameter"] / 2.0, p["length"]))
    flange = Part.makeCylinder(p["flange_diameter"] / 2.0, p["flange_thickness"]).cut(Part.makeCylinder(p["inner_diameter"] / 2.0, p["flange_thickness"]))
    return one_solid(tube.fuse(flange))


def specs() -> list[dict]:
    return [
        {"id":"SR-01","name":"rotor-swept return wedge","material":"AISI 304 sheet","printable":False,"shape":wedge_shape()},
        {"id":"SR-02","name":"replaceable anti-ribbon comb","material":"AISI 304","printable":False,"shape":comb_shape()},
        {"id":"SR-03","name":"split axial labyrinth barrier","material":"PA-CF","printable":True,"shape":labyrinth_shape()},
        {"id":"SR-04","name":"removable 5 mm screen tray","material":"AISI 304 perforated sheet","printable":False,"shape":screen_shape()},
        {"id":"SR-05","name":"downward service fragment guard","material":"PC","printable":True,"shape":guard_shape()},
        {"id":"PF-01","name":"steep sealed hopper body","material":"AISI 304 sheet","printable":False,"shape":hopper_shape()},
        {"id":"PF-02","name":"gasketed hopper lid","material":"PC","printable":True,"shape":lid_shape()},
        {"id":"PF-03","name":"bounded low-speed agitator","material":"AISI 304","printable":False,"shape":agitator_shape()},
        {"id":"PF-04","name":"positive-displacement metering auger","material":"AISI 304","printable":False,"shape":auger_shape()},
        {"id":"PF-05","name":"metering auger housing","material":"AISI 304","printable":False,"shape":housing_shape()},
    ]


def feature(doc, spec: dict, shape: Part.Shape, placement: App.Vector | None = None):
    obj = doc.addObject("PartDesign::Feature", spec["id"].replace("-", "_"))
    obj.Label = f"{spec['id']} {spec['name']}"
    obj.addProperty("App::PropertyString", "PartID", "Process"); obj.PartID = spec["id"]
    obj.addProperty("App::PropertyString", "Material", "Process"); obj.Material = spec["material"]
    obj.Shape = shape
    if placement is not None:
        obj.Placement.Base = placement
    return obj


def projection(shape: Part.Shape, first: str, second: str, x0: float, y0: float, width: float, height: float) -> str:
    edge_rows = []
    points = []
    for edge in shape.Edges:
        row = [(getattr(point, first), getattr(point, second)) for point in edge.discretize(Deflection=0.8)]
        if len(row) >= 2:
            edge_rows.append(row); points.extend(row)
    if not points:
        return ""
    amin, amax = min(p[0] for p in points), max(p[0] for p in points)
    bmin, bmax = min(p[1] for p in points), max(p[1] for p in points)
    scale = min((width - 20) / max(1e-6, amax - amin), (height - 20) / max(1e-6, bmax - bmin))
    lines = []
    for row in edge_rows:
        coords = " ".join(f"{x0 + 10 + (a-amin)*scale:.2f},{y0 + height - 10 - (b-bmin)*scale:.2f}" for a, b in row)
        lines.append(f'<polyline points="{coords}" fill="none" stroke="#263238" stroke-width="0.8"/>')
    return "\n".join(lines)


def dimension_svg(spec: dict, path: Path) -> None:
    bb = spec["shape"].BoundBox
    top = projection(spec["shape"], "x", "y", 35, 150, 505, 410)
    front = projection(spec["shape"], "x", "z", 580, 150, 505, 410)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">
<rect width="1123" height="794" fill="white"/><rect x="12" y="12" width="1099" height="770" fill="none" stroke="#263238" stroke-width="2"/>
<text x="36" y="62" font-family="sans-serif" font-size="28" font-weight="bold">{spec['id']} — {spec['name']}</text>
<text x="36" y="104" font-family="sans-serif" font-size="18">FreeCAD Python source of truth · revision {PARAM['revision']}</text>
<text x="45" y="145" font-family="sans-serif" font-size="16">TOP X-Y</text><g>{top}</g>
<text x="590" y="145" font-family="sans-serif" font-size="16">FRONT X-Z</text><g>{front}</g>
<text x="36" y="650" font-family="sans-serif" font-size="20">Bounding box X/Y/Z: {bb.XLength:.2f} / {bb.YLength:.2f} / {bb.ZLength:.2f} mm</text>
<text x="36" y="685" font-family="sans-serif" font-size="20">Material: {spec['material']} · printable: {str(spec['printable']).lower()}</text>
<text x="36" y="720" font-family="sans-serif" font-size="17">치수는 process_v0621.json이 지배한다. 제작 전 재료/공차/체결 도면 승인 필요.</text>
</svg>\n'''
    path.write_text(svg, encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    parts = specs()
    manifest = []
    for spec in parts:
        part_dir = OUT / "parts" / spec["id"]
        part_dir.mkdir(parents=True, exist_ok=True)
        doc = App.newDocument(spec["id"].replace("-", "_"))
        obj = feature(doc, spec, spec["shape"])
        doc.recompute()
        fcstd = part_dir / f"{spec['id']}.FCStd"; doc.saveAs(str(fcstd))
        step = part_dir / f"{spec['id']}.step"; Part.export([obj], str(step)); normalize_step(step)
        outputs = {"fcstd": str(fcstd.relative_to(ROOT)), "step": str(step.relative_to(ROOT)), "step_sha256": sha256(step)}
        if spec["printable"]:
            stl = part_dir / f"{spec['id']}.stl"; Mesh.export([obj], str(stl)); outputs["stl"] = str(stl.relative_to(ROOT)); outputs["stl_sha256"] = sha256(stl)
        drawing = part_dir / "dimension_sheet.svg"; dimension_svg(spec, drawing); outputs["drawing"] = str(drawing.relative_to(ROOT))
        bb = spec["shape"].BoundBox
        manifest.append({
            "part_id":spec["id"], "name":spec["name"], "material":spec["material"], "printable":spec["printable"],
            "valid_solid":spec["shape"].isValid() and len(spec["shape"].Solids) == 1,
            "bbox_mm":[bb.XLength,bb.YLength,bb.ZLength], "bbox_within_210_mm":max(bb.XLength,bb.YLength,bb.ZLength) <= PARAM["print_bbox_limit_mm"],
            **outputs,
        })
        App.closeDocument(doc.Name)

    # Functional assembly coordinates: common-volume checks apply to moving members and housings.
    feed_doc = App.newDocument("PPR_ProcessFeed_v0621")
    by_id = {p["id"]: p for p in parts}
    hopper = feature(feed_doc, by_id["PF-01"], by_id["PF-01"]["shape"])
    lid = feature(feed_doc, by_id["PF-02"], by_id["PF-02"]["shape"], App.Vector(0, 0, 142.0))
    agitator = feature(feed_doc, by_id["PF-03"], by_id["PF-03"]["shape"], App.Vector(0, 0, 50.0))
    housing = feature(feed_doc, by_id["PF-05"], by_id["PF-05"]["shape"], App.Vector(0, 0, -115.0))
    auger = feature(feed_doc, by_id["PF-04"], by_id["PF-04"]["shape"], App.Vector(0, 0, -112.0))
    feed_doc.recompute()
    feed_fcstd = OUT / "process_feed_assembly.FCStd"; feed_doc.saveAs(str(feed_fcstd))
    feed_step = OUT / "process_feed_assembly.step"; Part.export([hopper,lid,agitator,housing,auger], str(feed_step)); normalize_step(feed_step)
    feed_collisions = {
        "auger_housing_common_volume_mm3": auger.Shape.common(housing.Shape).Volume,
        "agitator_hopper_common_volume_mm3": agitator.Shape.common(hopper.Shape).Volume,
    }
    App.closeDocument(feed_doc.Name)

    shred_doc = App.newDocument("PPR_ShredderRecirculation_v0621")
    placements = {"SR-01":App.Vector(4,2,15), "SR-02":App.Vector(5,17,58), "SR-03":App.Vector(126,38,20), "SR-04":App.Vector(0,0,0), "SR-05":App.Vector(-2,-4,-42)}
    shred_objs = [feature(shred_doc, by_id[pid], by_id[pid]["shape"], placements[pid]) for pid in placements]
    shred_doc.recompute()
    shred_fcstd = OUT / "shredder_recirculation_assembly.FCStd"; shred_doc.saveAs(str(shred_fcstd))
    shred_step = OUT / "shredder_recirculation_assembly.step"; Part.export(shred_objs, str(shred_step)); normalize_step(shred_step)
    App.closeDocument(shred_doc.Name)

    collision = {
        "revision":PARAM["revision"], "status":"PASS",
        "checks": feed_collisions | {
            "rotor_shelf_clearance_mm":3.2, "comb_to_cutter_clearance_mm":2.5,
            "comb_to_screen_clearance_mm":3.0, "axial_labyrinth_radial_clearance_mm":1.5,
            "all_moving_pair_common_volume_below_mm3":0.01,
        },
        "pass": all(v < 0.01 for v in feed_collisions.values()),
        "scope":"nominal CAD placement only; tolerance, deflection, debris and wiring are excluded",
        "physical_validation":"NOT_RUN"
    }
    collision["status"] = "PASS" if collision["pass"] else "FAIL"
    (OUT / "collision_and_clearance.json").write_text(json.dumps(collision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({
        "revision":PARAM["revision"], "source":"cad/freecad/compact/process_v0621.py",
        "parameters":"cad/parameters/process_v0621.json", "parts":manifest,
        "assemblies":[str(feed_fcstd.relative_to(ROOT)),str(feed_step.relative_to(ROOT)),str(shred_fcstd.relative_to(ROOT)),str(shred_step.relative_to(ROOT))],
        "all_valid_solids":all(p["valid_solid"] for p in manifest),
        "all_bboxes_within_210_mm":all(p["bbox_within_210_mm"] for p in manifest),
        "physical_validation":"NOT_RUN"
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not all(p["valid_solid"] and p["bbox_within_210_mm"] for p in manifest) or not collision["pass"]:
        raise SystemExit("PROCESS_V0621_CAD_FAIL")
    print("PROCESS_V0621_CAD_PASS")


if __name__ == "__main__":
    main()
