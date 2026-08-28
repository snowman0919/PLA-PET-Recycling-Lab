#!/usr/bin/env python3
"""Software-render actual FreeCAD tessellations without an OpenGL dependency."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import FreeCAD as App
import Part
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GEOM = ROOT / "cad/freecad/compact"
sys.path.insert(0, str(GEOM))
from geometry import assembly_objects, hook_disc, print_parts  # noqa: E402

W, H = 1600, 1200


def project(p, view):
    x, y, z = p.x, p.y, p.z
    if view == "front": return x, z, y
    if view == "top": return x, y, z
    if view == "right": return y, z, x
    return x - 0.58 * y, z + 0.26 * x + 0.18 * y, x + y - 0.4 * z


def normal_z(a, b, c):
    ux, uy, uz = b.x-a.x, b.y-a.y, b.z-a.z
    vx, vy, vz = c.x-a.x, c.y-a.y, c.z-a.z
    nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
    n = math.sqrt(nx*nx+ny*ny+nz*nz) or 1
    return nz/n


def render(items, output, title, view="iso", clip=None, support=False, arrow=False, arrow_target=(1060,430)):
    triangles = []
    for item in items:
        if "_mesh" not in item:
            # Review images show assembly relationships, not surface finish.
            # A coarse deterministic mesh keeps clean-clone rendering bounded.
            item["_mesh"] = item["shape"].tessellate(7.0)
        pts, faces = item["_mesh"]
        for face in faces:
            a, b, c = (App.Vector(*pts[i]) for i in face)
            centroid = ((a.x+b.x+c.x)/3, (a.y+b.y+c.y)/3, (a.z+b.z+c.z)/3)
            if clip and not clip(centroid): continue
            pp = [project(q, view) for q in (a, b, c)]
            color = item["color"]
            if support and normal_z(a, b, c) < -0.45: color = (205, 55, 45)
            triangles.append((sum(q[2] for q in pp)/3, [(q[0], q[1]) for q in pp], color))
    if not triangles: raise RuntimeError(f"no triangles for {output}")
    xs = [p[0] for _, tri, _ in triangles for p in tri]; ys = [p[1] for _, tri, _ in triangles for p in tri]
    margin = 110; scale = min((W-2*margin)/(max(xs)-min(xs) or 1), (H-2*margin)/(max(ys)-min(ys) or 1))
    def screen(pt): return (margin + (pt[0]-min(xs))*scale, H-margin-(pt[1]-min(ys))*scale)
    image = Image.new("RGB", (W, H), (246, 248, 249)); draw = ImageDraw.Draw(image)
    for _, tri, color in sorted(triangles, key=lambda t: t[0], reverse=True):
        poly = [screen(p) for p in tri]
        draw.polygon(poly, fill=color, outline=tuple(max(0, c-42) for c in color))
    font = ImageFont.load_default(size=25)
    draw.rectangle((24, 20, W-24, 67), fill=(255,255,255), outline=(75,95,105), width=2)
    draw.text((42, 31), title, fill=(25,45,55), font=font)
    if arrow:
        tx,ty=arrow_target
        draw.line((1320, 250, tx, ty), fill=(196,43,43), width=12)
        draw.polygon([(tx,ty),(tx+45,ty-18),(tx+35,ty+28)], fill=(196,43,43))
        draw.text((1130, 205), "M6 through-bolt access", fill=(160,30,30), font=font)
    output.parent.mkdir(parents=True, exist_ok=True); image.save(output)


def part_items():
    result=[]
    for i, spec in enumerate(print_parts()):
        shape=spec["shape"].copy(); col=i%4; row=i//4
        shape.translate(App.Vector(col*220, row*220, 0))
        result.append({"name":spec["id"],"shape":shape,"color":(63,137,178),"group":"print"})
    return result


def render_section(assembly=None):
    assembly = assembly or assembly_objects()
    slab = Part.makeBox(470, 10, 930, App.Vector(0, 342, 0))
    section=[]
    for item in assembly:
        bb=item["shape"].BoundBox
        if item["group"] == "frame" or bb.YMax <= 342 or bb.YMin >= 352: continue
        shape=item["shape"].common(slab)
        if not shape.isNull(): section.append({**item,"shape":shape})
    render(section, ROOT/"renders/review/compact_section.png", "True center slab section y=342..352 mm", "front")


def render_tool_access(assembly=None):
    assembly = assembly or assembly_objects()
    render([i for i in assembly if i["group"]=="shredder"], ROOT/"renders/review/shredder_fastener_tool_access.png", "Shredder bearing plates / interleaved discs / M6 through-bolts", "right", arrow=True, arrow_target=(1210,680))


def main():
    assembly = assembly_objects()
    cutter = hook_disc()
    if "--shredder-only" in sys.argv:
        render([{"name":"CUT-01","shape":cutter,"color":(225,116,55),"group":"part"}], ROOT/"renders/modules/CUT-01_cycloidal_hook_profile.png", "CUT-01 | 76% cycloidal capture / fast hook relief", "front")
        visible_names = ("MY1016Z", "ROTEX19Coupling", "PhaseGear", "Shaft")
        drive = [i for i in assembly if i["name"].startswith(visible_names) or i["name"] in ("Hook105_0", "Hook153_0")]
        render(drive, ROOT/"renders/modules/shredder_drive_guard_removed.png", "Guard removed | MY1016Z direct / M3 Z16 phase gears", "iso")
        print("COMPACT_SHREDDER_RENDER_OK images=2")
        return
    if "--tool-only" in sys.argv:
        render_tool_access(assembly)
        print("COMPACT_TOOL_ACCESS_RENDER_OK images=1")
        return
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_isometric.png", "compact-single-path-v0.3 | 470 x 700 x 930 mm", "iso")
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_front.png", "Front | vertical forming path and full spool", "front")
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_top.png", "Top | all normal-operation components inside frame", "top")
    shredder=[i for i in assembly if i["group"] in ("input","shredder","feed")]
    render(shredder, ROOT/"renders/modules/shared_shredder_module.png", "Shared hopper / hook cutter / removable screen / bin", "iso")
    render([{"name":"CUT-01","shape":cutter,"color":(225,116,55),"group":"part"}], ROOT/"renders/modules/CUT-01_cycloidal_hook_profile.png", "CUT-01 | 76% cycloidal capture / fast hook relief", "front")
    visible_names = ("MY1016Z", "ROTEX19Coupling", "PhaseGear", "Shaft")
    drive = [i for i in assembly if i["name"].startswith(visible_names) or i["name"] in ("Hook105_0", "Hook153_0")]
    render(drive, ROOT/"renders/modules/shredder_drive_guard_removed.png", "MY1016Z direct / M3 Z16 hardened phase gears", "iso")
    anti=print_parts()[1]
    render([{"name":anti["id"],"shape":anti["shape"],"color":(63,137,178),"group":"part"}], ROOT/"renders/modules/PPR-C02_individual.png", "PPR-C02 anti-reach baffle | individual part", "iso")
    render(assembly_objects(exploded=True), ROOT/"renders/review/compact_exploded.png", "Exploded by service module", "iso")
    render_section(assembly)
    render_tool_access(assembly)
    prints=part_items()
    render(prints, ROOT/"renders/review/print_orientation.png", "Print orientation overview | every axis <= 210 mm", "top")
    render(prints, ROOT/"renders/review/support_contact.png", "Support-contact review | downward facets in red", "iso", support=True)
    render([i for i in assembly if i["group"] in ("forming","spooler")], ROOT/"renders/review/forming_spool_motion.png", "Gauge/puller then solid guide, dancer, traverse and full spool", "iso")
    print("COMPACT_RENDER_GENERATION_OK images=13")


if __name__ == "__main__":
    main()
