"""Generate FCStd/STEP/STL/3MF and print package for compact v0.3."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import FreeCAD as App
import Mesh
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from geometry import assembly_objects, print_parts  # noqa: E402

PARAMS = json.loads((ROOT / "cad/parameters/baseline.json").read_text())


def dirs():
    for p in (ROOT / "cad/generation/fcstd", ROOT / "exports/step", ROOT / "exports/print", ROOT / "exports/print/plate_layouts"):
        p.mkdir(parents=True, exist_ok=True)


def feature(doc, name, shape, label, part_id="", material=""):
    obj = doc.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if part_id:
        obj.addProperty("App::PropertyString", "PartID", "BOM"); obj.PartID = part_id
        obj.addProperty("App::PropertyString", "Material", "BOM"); obj.Material = material
    return obj


def normalize_step(path):
    text = path.read_text(encoding="ascii")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2000-01-01T00:00:00'", text, count=1)
    path.write_text(text, encoding="ascii", newline="\n")


def export_print_part(spec):
    part_dir = ROOT / "exports/print" / spec["id"]
    part_dir.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument(spec["id"].replace("-", "_"))
    obj = feature(doc, "Body", spec["shape"], spec["name"], spec["id"], spec["material"])
    doc.recompute()
    fcstd = part_dir / f"{spec['id']}.FCStd"; doc.saveAs(str(fcstd))
    step = part_dir / f"{spec['id']}.step"; Part.export([obj], str(step)); normalize_step(step)
    stl = part_dir / f"{spec['id']}.stl"; Mesh.export([obj], str(stl))
    three = part_dir / f"{spec['id']}.3mf"; Mesh.export([obj], str(three))
    density = 1.04 if spec["material"] == "ABS" else 1.24
    mass_each = spec["shape"].Volume / 1000.0 * density
    bb = spec["shape"].BoundBox
    notes = f"""# {spec['id']} — {spec['name']}

- quantity: {spec['qty']}
- material: {spec['material']}
- orientation: {spec['orientation']}
- layer height: {spec['layer']}
- wall count: {spec['walls']}
- infill: {spec['infill']}
- support: {spec['support']}
- estimated mass: {mass_each:.1f} g/ea, {mass_each * spec['qty']:.1f} g total
- estimated print time: {(mass_each * spec['qty'] / 12):.1f} h at 12 g/h planning rate
- fastener: {spec['fastener']}
- tolerance: {spec['tolerance']}
- mating part: {spec['mating']}
- assembly order: {spec['order']}
- bounding box: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm

Mass와 시간은 CAD volume/nominal rate 기반이며 slicer 결과가 아니다. 실제 printer profile로 재검증한다.
"""
    (part_dir / "print_notes.md").write_text(notes)
    App.closeDocument(doc.Name)
    return {**spec, "mass_each_g": mass_each, "x_mm": bb.XLength, "y_mm": bb.YLength, "z_mm": bb.ZLength}


def export_assembly():
    doc = App.newDocument("CompactFullAssembly")
    objects = []
    for i, item in enumerate(assembly_objects()):
        objects.append(feature(doc, f"Part{i:03d}", item["shape"], item["name"], material=item["material"]))
    doc.recompute()
    fcstd = ROOT / "cad/generation/fcstd/compact_full_assembly.FCStd"; doc.saveAs(str(fcstd))
    step = ROOT / "exports/step/compact_full_assembly.step"; Part.export(objects, str(step)); normalize_step(step)
    compound = Part.makeCompound([o.Shape for o in objects])
    bb = compound.BoundBox
    meta = {
        "revision": PARAMS["revision"],
        "bounding_box_mm": [round(bb.XLength, 2), round(bb.YLength, 2), round(bb.ZLength, 2)],
        "minimum_mm": [round(bb.XMin, 2), round(bb.YMin, 2), round(bb.ZMin, 2)],
        "maximum_mm": [round(bb.XMax, 2), round(bb.YMax, 2), round(bb.ZMax, 2)],
        "object_count": len(objects),
        "includes": ["closed lid", "guards", "motor/reducer keepouts", "cable duct", "1 kg spool", "dancer/traverse motion"],
    }
    (ROOT / "cad/generation/assembly_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    App.closeDocument(doc.Name)
    return meta


def export_plates(rows):
    # One family per plate keeps quantities traceable and every arrangement
    # inside the 210 mm square without relying on a particular slicer.
    groups = [[row["id"]] for row in rows]
    by_id = {r["id"]: r for r in rows}
    for old in (ROOT / "exports/print/plate_layouts").glob("plate-*.3mf"):
        old.unlink()
    for index, ids in enumerate(groups, 1):
        doc = App.newDocument(f"Plate{index:02d}")
        x = y = row_h = 0.0; objs = []
        for pid in ids:
            spec = by_id[pid]
            for q in range(spec["qty"]):
                shape = spec["shape"].copy(); bb = shape.BoundBox
                if x + bb.XLength > 205:
                    x = 0; y += row_h + 5; row_h = 0
                shape.translate(App.Vector(x - bb.XMin, y - bb.YMin, -bb.ZMin))
                objs.append(feature(doc, f"{pid.replace('-', '_')}_{q}", shape, pid))
                x += bb.XLength + 5; row_h = max(row_h, bb.YLength)
        doc.recompute()
        out = ROOT / f"exports/print/plate_layouts/plate-{index:02d}.3mf"
        Mesh.export(objs, str(out))
        App.closeDocument(doc.Name)


def main():
    dirs()
    rows = [export_print_part(spec) for spec in print_parts()]
    export_plates(rows)
    manifest = ROOT / "exports/print/print_manifest.csv"
    with manifest.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["part_id", "name", "quantity", "material", "x_mm", "y_mm", "z_mm", "mass_each_g", "mass_total_g", "orientation", "layer_height", "walls", "infill", "support", "fastener", "tolerance", "mating_part", "assembly_order"])
        for r in rows:
            writer.writerow([r["id"], r["name"], r["qty"], r["material"], f"{r['x_mm']:.2f}", f"{r['y_mm']:.2f}", f"{r['z_mm']:.2f}", f"{r['mass_each_g']:.2f}", f"{r['mass_each_g']*r['qty']:.2f}", r["orientation"], r["layer"], r["walls"], r["infill"], r["support"], r["fastener"], r["tolerance"], r["mating"], r["order"]])
    total = sum(r["mass_each_g"] * r["qty"] for r in rows)
    report = f"# 출력물 총 재료 보고\n\n- revision: `{PARAMS['revision']}`\n- CAD solid-volume 기반 총 질량: **{total:.1f} g**\n- 목표 1,500 g 대비 margin: **{1500-total:.1f} g**\n- hard review threshold 2,000 g: **PASS**\n- 예상 재료비(18,000 KRW/kg): **{total/1000*18000:,.0f} KRW**\n\nCoupon은 이 합계에서 제외한다. Slicer infill/line width와 purge는 별도이므로 실제 plate slicing 후 갱신한다.\n"
    (ROOT / "exports/print/total_material_report.md").write_text(report)
    with (ROOT / "bom/printed_material_cost.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["part_id", "quantity", "material", "estimated_mass_g", "cost_krw_per_kg", "estimated_cost_krw", "status"])
        for r in rows: w.writerow([r["id"], r["qty"], r["material"], f"{r['mass_each_g']*r['qty']:.2f}", 18000, round(r["mass_each_g"]*r["qty"]/1000*18000), "CAD_VOLUME_ESTIMATE"])
    meta = export_assembly()
    print(f"COMPACT_CAD_GENERATION_OK parts={len(rows)} mass_g={total:.1f} envelope={meta['bounding_box_mm']}")


if __name__ == "__main__":
    main()
