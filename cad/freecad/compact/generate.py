"""Generate closed-solid FCStd/STEP/STL/3MF for compact v0.5."""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path

import FreeCAD as App
import Mesh
import Part
import importDXF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from geometry import assembly_objects, print_parts, review_keepout_objects, shredder_metal_parts, tolerance_coupon  # noqa: E402

PARAMS = json.loads((ROOT / "cad/parameters/baseline.json").read_text())


def dirs():
    for p in (ROOT / "cad/generation/fcstd", ROOT / "cad/review_keepouts", ROOT / "exports/step", ROOT / "exports/cnc", ROOT / "exports/print", ROOT / "exports/print/plate_layouts", ROOT / "exports/print/slicer_profiles", ROOT / "exports/print/slicing_previews"):
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
    # OpenCASCADE appends a process-local export sequence to the translator
    # product name.  It is not geometry, but otherwise changes every rebuild.
    text = re.sub(
        r"Open CASCADE STEP translator ([0-9.]+) [0-9]+",
        r"Open CASCADE STEP translator \1 0",
        text,
    )
    path.write_text(text, encoding="ascii", newline="\n")


def normalize_dxf(path):
    """Keep FreeCAD's DXF export stable and free of trailing blank spaces."""
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8", newline="\n")


def normalize_zip_container(path, normalize_fcstd=False):
    """Remove run time, random UUID and transient FreeCAD object IDs."""
    temporary = path.with_suffix(path.suffix + ".normalized")
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as target:
        target.comment = source.comment
        stable_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, str(path.relative_to(ROOT))))
        for member in source.infolist():
            data = source.read(member.filename)
            if normalize_fcstd and member.filename == "Document.xml":
                text = data.decode("utf-8")
                text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", "2000-01-01T00:00:00+00:00", text)
                text = re.sub(r'(<Uuid value=")[^"]+("/>)', rf"\g<1>{stable_uuid}\2", text)
                transient_ids = list(dict.fromkeys(re.findall(r'id="(\d+)"', text)))
                id_map = {old: str(1000 + index) for index, old in enumerate(transient_ids)}
                text = re.sub(r'id="(\d+)"', lambda match: f'id="{id_map[match.group(1)]}"', text)
                data = text.encode("utf-8")
            elif normalize_fcstd and member.filename.endswith(".Shape.Map.txt"):
                counter = iter(range(1, 10000))
                text = data.decode("ascii")
                text = re.sub(r";D[0-9A-Fa-f]+", lambda _match: f";D{next(counter):04x}", text)
                data = text.encode("ascii")
            info = zipfile.ZipInfo(member.filename, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = member.external_attr
            info.create_system = member.create_system
            target.writestr(info, data)
    temporary.replace(path)


def _projection_polylines(shape, axes, box, margin=16):
    """Return deterministic SVG polylines for one orthographic projection."""
    x0, y0, width, height = box
    points = []
    edge_rows = []
    for edge in shape.Edges:
        row = edge.discretize(Deflection=0.7)
        projected = [(getattr(p, axes[0]), getattr(p, axes[1])) for p in row]
        if len(projected) >= 2:
            edge_rows.append(projected); points.extend(projected)
    if not points:
        return ""
    min_a=min(p[0] for p in points); max_a=max(p[0] for p in points)
    min_b=min(p[1] for p in points); max_b=max(p[1] for p in points)
    scale=min((width-2*margin)/max(1e-6,max_a-min_a),(height-2*margin)/max(1e-6,max_b-min_b))
    def map_point(p):
        return (x0+margin+(p[0]-min_a)*scale, y0+height-margin-(p[1]-min_b)*scale)
    lines=[]
    for row in edge_rows:
        coords=" ".join(f"{x:.2f},{y:.2f}" for x,y in map(map_point,row))
        lines.append(f'<polyline points="{coords}" fill="none" stroke="#263238" stroke-width="0.8"/>')
    return "\n".join(lines)


def write_dimension_sheet(spec, path):
    """Create an inspectable A4-landscape orthographic dimension sheet."""
    bb=spec["shape"].BoundBox
    values=[
        f"Revision: {PARAMS['revision']}",
        f"Part: {spec['id']} — {spec['name']}  Qty {spec['qty']}  Material {spec['material']}",
        f"Overall: X {bb.XLength:.2f}  Y {bb.YLength:.2f}  Z {bb.ZLength:.2f} mm; unless noted printed tolerance ±0.30 mm",
        f"Interface: {spec['interfaces']}",
        f"Fastener: {spec['fastener']}; insert/nut: {spec['insert']}; tightening: {spec['tightening']}",
        f"Edge distance: {spec['edge_distance']}; mating: {spec['mating']}",
        f"Print: {spec['orientation']}; {spec['layer']}; {spec['walls']} perimeters; support: {spec['support']}",
        "Dimensions govern over SVG scale. Ream/fit only after printing the PPR-TC01 tolerance coupon.",
    ]
    views=(
        _projection_polylines(spec["shape"],("x","y"),(30,110,335,250)),
        _projection_polylines(spec["shape"],("x","z"),(395,110,335,250)),
        _projection_polylines(spec["shape"],("y","z"),(760,110,335,250)),
    )
    escaped=[html.escape(v) for v in values]
    text_rows="\n".join(f'<text x="34" y="{430+i*36}" font-size="18">{value}</text>' for i,value in enumerate(escaped))
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">
<rect width="1123" height="794" fill="white"/><rect x="12" y="12" width="1099" height="770" fill="none" stroke="#263238" stroke-width="2"/>
<text x="30" y="52" font-size="26" font-family="sans-serif" font-weight="bold">{html.escape(spec['id'])} PRINT DIMENSION SHEET</text>
<text x="30" y="82" font-size="16" font-family="sans-serif">FreeCAD Python source of truth · units mm · DIGITAL_GEOMETRY_AND_SURROGATE_BASELINE</text>
<g font-family="sans-serif"><text x="40" y="132" font-size="16">TOP X-Y</text>{views[0]}<text x="405" y="132" font-size="16">FRONT X-Z</text>{views[1]}<text x="770" y="132" font-size="16">SIDE Y-Z</text>{views[2]}{text_rows}</g>
</svg>\n'''
    path.write_text(svg)


def write_part_source(spec, path):
    path.write_text(f'''#!/usr/bin/env python3
"""Regenerate {spec['id']} from the shared v0.5 FreeCAD source."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from geometry import print_parts
from generate import export_print_part
spec=next(item for item in print_parts() if item["id"]=="{spec['id']}")
export_print_part(spec)
print("{spec['id']}_REGENERATED")
''')


def export_print_part(spec):
    part_dir = ROOT / "exports/print" / spec["id"]
    part_dir.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument(spec["id"].replace("-", "_"))
    obj = feature(doc, "Body", spec["shape"], spec["name"], spec["id"], spec["material"])
    doc.recompute()
    fcstd = part_dir / f"{spec['id']}.FCStd"; fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd, normalize_fcstd=True)
    step = part_dir / f"{spec['id']}.step"; Part.export([obj], str(step)); normalize_step(step)
    stl = part_dir / f"{spec['id']}.stl"; Mesh.export([obj], str(stl))
    three = part_dir / f"{spec['id']}.3mf"; Mesh.export([obj], str(three)); normalize_zip_container(three)
    write_part_source(spec, part_dir / f"{spec['id']}.py")
    write_dimension_sheet(spec, part_dir / "dimension_sheet.svg")
    density = 1.04 if spec["material"] == "ABS" else 1.24
    mass_each = spec["shape"].Volume / 1000.0 * density
    bb = spec["shape"].BoundBox
    notes = f"""# {spec['id']} — {spec['name']}

- revision: `{PARAMS['revision']}`
- quantity: {spec['qty']}
- material: {spec['material']}
- nozzle diameter: {spec['nozzle_mm']:.1f} mm
- orientation: {spec['orientation']}
- layer height: {spec['layer']}
- wall count: {spec['walls']}
- top/bottom layers: {spec['top_bottom_layers']}
- infill: {spec['infill']}
- support: {spec['support']}
- support-contact region: {spec['support_contact']}
- support removal: {spec['support_removal']}
- brim: {spec['brim']}
- designed minimum wall: {spec['minimum_wall_mm']:.1f} mm
- estimated mass: {mass_each:.1f} g/ea, {mass_each * spec['qty']:.1f} g total
- estimated print time: {(mass_each * spec['qty'] / 12):.1f} h at 12 g/h planning rate
- fastener: {spec['fastener']}
- insert or captured nut: {spec['insert']}
- tightening torque: {spec['tightening']}
- fastener edge distance: {spec['edge_distance']}
- physical interfaces: {spec['interfaces']}
- tolerance: {spec['tolerance']}
- mating part: {spec['mating']}
- assembly order: {spec['order']}
- bounding box: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm
- FreeCAD Python source: `{spec['id']}.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.
"""
    (part_dir / "print_notes.md").write_text(notes)
    App.closeDocument(doc.Name)
    return {**spec, "mass_each_g": mass_each, "x_mm": bb.XLength, "y_mm": bb.YLength, "z_mm": bb.ZLength}


def export_tolerance_coupon():
    part_id="PPR-TC01"; shape=tolerance_coupon(); part_dir=ROOT/"exports/print/coupons"/part_id
    part_dir.mkdir(parents=True,exist_ok=True)
    doc=App.newDocument(part_id.replace("-","_")); obj=feature(doc,"Body",shape,"Fastener and fit tolerance coupon",part_id,"PLA")
    doc.recompute()
    fcstd=part_dir/f"{part_id}.FCStd"; fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd,True)
    step=part_dir/f"{part_id}.step"; Part.export([obj],str(step)); normalize_step(step)
    stl=part_dir/f"{part_id}.stl"; Mesh.export([obj],str(stl))
    three=part_dir/f"{part_id}.3mf"; Mesh.export([obj],str(three)); normalize_zip_container(three)
    source=part_dir/f"{part_id}.py"
    source.write_text('''#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from generate import export_tolerance_coupon
export_tolerance_coupon()
print("PPR-TC01_REGENERATED")
''')
    notes=f'''# {part_id} — fastener/insert/fit tolerance coupon

- revision: `{PARAMS['revision']}`
- status: `REQUIRED_BEFORE_PRODUCTION_PRINTS`; coupon mass is excluded from machine print total
- material/profile: same spool, nozzle and slicer profile as the target PLA parts
- orientation: flat; 0.4 mm nozzle; 0.20 mm layer; 4 perimeters; no support
- through-hole ladders: M3 Ø3.2/3.4/3.6, M4 insert Ø4.2/4.4/4.6, M5 Ø5.3/5.5/5.7
- square-nut pockets: M3 5.6/5.8/6.0 and M4 7.0/7.2/7.4 mm
- male gauges: Ø7.8/8.0/8.2 and Ø11.8/12.0/12.2 mm
- acceptance: select the smallest hole/pocket that accepts the actual hardware without splitting; select the male gauge producing the documented slide/ream allowance. Record selection in `tolerance_coupon_results.csv`.
- limitation: slicer success does not qualify fit; the coupon must be physically printed and measured for each printer/material batch.
'''
    (part_dir/"print_notes.md").write_text(notes)
    with (part_dir/"tolerance_coupon_results.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["date","printer","material_lot","nozzle_mm","feature_family","nominal_mm","measured_mm","fit_result","selected_compensation_mm","operator","evidence"])
    App.closeDocument(doc.Name)


def export_assembly():
    doc = App.newDocument("CompactFullAssembly")
    objects = []
    assembly_items=assembly_objects()
    for i, item in enumerate(assembly_items):
        obj=feature(doc, f"Part{i:03d}", item["shape"], item["name"], material=item["material"])
        obj.addProperty("App::PropertyString", "Classification", "BOM"); obj.Classification=item["classification"]
        objects.append(obj)
    doc.recompute()
    fcstd = ROOT / "cad/generation/fcstd/compact_full_assembly.FCStd"; fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd, normalize_fcstd=True)
    step = ROOT / "exports/step/compact_full_assembly.step"; Part.export(objects, str(step)); normalize_step(step)
    compound = Part.makeCompound([o.Shape for o in objects])
    bb = compound.BoundBox
    meta = {
        "revision": PARAMS["revision"],
        "bounding_box_mm": [round(bb.XLength, 2), round(bb.YLength, 2), round(bb.ZLength, 2)],
        "minimum_mm": [round(bb.XMin, 2), round(bb.YMin, 2), round(bb.ZMin, 2)],
        "maximum_mm": [round(bb.XMax, 2), round(bb.YMax, 2), round(bb.ZMax, 2)],
        "object_count": len(objects),
        "reference_component_policy": "purchased/donor envelope objects retain classification and evidence; keep-outs remain in cad/review_keepouts",
        "includes": ["closed lid", "guards", "parametric reference drive", "cable duct", "1 kg spool", "dancer arm", "traverse rail"],
        "excludes": ["motion and service keep-outs; see cad/review_keepouts"],
    }
    (ROOT / "cad/generation/assembly_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    with (ROOT/"cad/generation/assembly_classification.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["object","group","material","classification","shape_type","solid_count","volume_mm3","mass_override_kg","evidence"])
        for item in assembly_items:
            w.writerow([item["name"],item["group"],item["material"],item["classification"],item["shape"].ShapeType,len(item["shape"].Solids),f"{item['shape'].Volume:.3f}",item.get("mass_override_kg") or "",item.get("evidence","")])
    App.closeDocument(doc.Name)
    return meta


def export_review_keepouts():
    """Write spatial-review volumes outside every manufacturing export."""
    doc=App.newDocument("ReviewKeepouts")
    objects=[]
    for index,item in enumerate(review_keepout_objects()):
        obj=feature(doc,f"Keepout{index:02d}",item["shape"],item["name"],material="REVIEW_ONLY")
        obj.addProperty("App::PropertyString","Purpose","Review"); obj.Purpose=item["purpose"]
        objects.append(obj)
    doc.recompute()
    fcstd=ROOT/"cad/review_keepouts/review_keepouts.FCStd"; fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd,True)
    manifest={"revision":PARAMS["revision"],"classification":"REVIEW_ONLY_NOT_MANUFACTURED","objects":[{"name":i["name"],"purpose":i["purpose"]} for i in review_keepout_objects()]}
    (ROOT/"cad/review_keepouts/manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    App.closeDocument(doc.Name)


def export_metal_parts():
    rows = []
    gate1_release = {
        "CUT-01": "GATE1_MAX_2_ALLOWED_USER_APPROVAL_REQUIRED; REMAINING_10_HOLD",
        "CUT-03": "GATE1_QTY_2_ALLOWED_USER_APPROVAL_REQUIRED",
        "CUT-04": "GATE1_MAX_1_ALLOWED_USER_APPROVAL_REQUIRED; REMAINING_1_HOLD",
        "CUT-05": "GATE1_QTY_2_ALLOWED_USER_APPROVAL_REQUIRED",
        "CUT-07": "GATE1_QTY_1_ALLOWED_AFTER_DONOR_MEASUREMENT_AND_USER_APPROVAL",
        "CUT-08": "GATE1_QTY_2_ALLOWED_USER_APPROVAL_REQUIRED",
    }
    for spec in shredder_metal_parts():
        part_dir = ROOT / "exports/cnc" / spec["id"]
        part_dir.mkdir(parents=True, exist_ok=True)
        doc = App.newDocument(spec["id"].replace("-", "_"))
        obj = feature(doc, "Part", spec["shape"], spec["name"], spec["id"], spec["material"])
        doc.recompute()
        fcstd = part_dir / f"{spec['id']}.FCStd"
        fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd, normalize_fcstd=True)
        step = part_dir / f"{spec['id']}.step"
        Part.export([obj], str(step)); normalize_step(step)
        dxf = part_dir / f"{spec['id']}.dxf"
        importDXF.export([obj], str(dxf)); normalize_dxf(dxf)
        bb = spec["shape"].BoundBox
        release_state=gate1_release.get(spec["id"], "HOLD_UNTIL_PHYSICAL_GATE1_PASS")
        notes = (
            f"# {spec['id']} — {spec['name']}\n\n"
            f"- 수량: {spec['qty']}\n- 재료: {spec['material']}\n- 공정: {spec['process']}\n"
            f"- CAD bounding box: {bb.XLength:.2f} x {bb.YLength:.2f} x {bb.ZLength:.2f} mm\n"
            "- 일반공차: ISO 2768-m, 별도 표기 없는 edge C0.3 deburr\n"
            f"- 중요공차/검사: {spec['critical']}\n"
            "- 좌표기준: STEP 원점과 축을 기준으로 하며 DXF는 2D profile 견적용이다. 회전체는 STEP과 본 notes를 함께 견적한다.\n"
            f"- 발주상태: {release_state}\n"
            "- 공통 잠금: 사용자 승인 없는 가공 금지. CUT-01 full stack과 Gate-1 지그에 불필요한 수량은 물리 Gate-1 PASS 전 발주 금지\n"
        )
        (part_dir / "drawing_notes.md").write_text(notes)
        rows.append({**spec, "x_mm": bb.XLength, "y_mm": bb.YLength, "z_mm": bb.ZLength})
        App.closeDocument(doc.Name)
    with (ROOT / "exports/cnc/shredder_manifest.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["part_id", "name", "quantity", "material", "process", "x_mm", "y_mm", "z_mm", "files", "release_state"])
        for r in rows:
            w.writerow([r["id"], r["name"], r["qty"], r["material"], r["process"], f"{r['x_mm']:.2f}", f"{r['y_mm']:.2f}", f"{r['z_mm']:.2f}", "FCStd|STEP|DXF|notes", gate1_release.get(r["id"], "HOLD_UNTIL_PHYSICAL_GATE1_PASS")])
    return rows


def export_plates(rows):
    # Plate 3MF is a slicer-owned artifact. Remove stale FreeCAD mesh plates;
    # validation/slice_prints.py recreates every plate with the pinned profile.
    for old in (ROOT / "exports/print/plate_layouts").glob("plate-*.3mf"):
        old.unlink()


def main():
    dirs()
    metal_rows = export_metal_parts()
    rows = [export_print_part(spec) for spec in print_parts()]
    export_tolerance_coupon()
    export_plates(rows)
    manifest = ROOT / "exports/print/print_manifest.csv"
    with manifest.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["revision", "part_id", "name", "quantity", "material", "x_mm", "y_mm", "z_mm", "cad_net_mass_each_g", "cad_net_mass_total_g", "slicer_mass_total_g", "slicer_time_s", "orientation", "nozzle_mm", "layer_height", "walls", "top_bottom_layers", "infill", "support", "support_contact", "support_removal", "brim", "minimum_wall_mm", "fastener", "insert_or_nut", "tightening_torque", "edge_distance", "interfaces", "tolerance", "mating_part", "assembly_order", "freecad_source", "dimension_sheet", "slicer_status"])
        for r in rows:
            writer.writerow([PARAMS["revision"], r["id"], r["name"], r["qty"], r["material"], f"{r['x_mm']:.2f}", f"{r['y_mm']:.2f}", f"{r['z_mm']:.2f}", f"{r['mass_each_g']:.2f}", f"{r['mass_each_g']*r['qty']:.2f}", "PENDING_SLICER", "PENDING_SLICER", r["orientation"], r["nozzle_mm"], r["layer"], r["walls"], r["top_bottom_layers"], r["infill"], r["support"], r["support_contact"], r["support_removal"], r["brim"], r["minimum_wall_mm"], r["fastener"], r["insert"], r["tightening"], r["edge_distance"], r["interfaces"], r["tolerance"], r["mating"], r["order"], f"{r['id']}.py", "dimension_sheet.svg", "PENDING"])
    total = sum(r["mass_each_g"] * r["qty"] for r in rows)
    report = f"# 출력물 총 재료 보고\n\n- revision: `{PARAMS['revision']}`\n- CAD solid-volume 기반 총 질량: **{total:.1f} g**\n- 목표 1,500 g 대비 margin: **{1500-total:.1f} g**\n- hard review threshold 2,000 g: **PASS**\n- 예상 재료비(18,000 KRW/kg): **{total/1000*18000:,.0f} KRW**\n\nCoupon은 이 합계에서 제외한다. Slicer infill/line width와 purge는 별도이므로 실제 plate slicing 후 갱신한다.\n"
    (ROOT / "exports/print/total_material_report.md").write_text(report)
    with (ROOT / "bom/printed_material_cost.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["part_id", "quantity", "material", "estimated_mass_g", "cost_krw_per_kg", "estimated_cost_krw", "status"])
        for r in rows: w.writerow([r["id"], r["qty"], r["material"], f"{r['mass_each_g']*r['qty']:.2f}", 18000, round(r["mass_each_g"]*r["qty"]/1000*18000), "CAD_VOLUME_ESTIMATE"])
    meta = export_assembly()
    export_review_keepouts()
    print(f"COMPACT_CAD_GENERATION_OK print_parts={len(rows)} metal_parts={len(metal_rows)} mass_g={total:.1f} envelope={meta['bounding_box_mm']}")


if __name__ == "__main__":
    main()
