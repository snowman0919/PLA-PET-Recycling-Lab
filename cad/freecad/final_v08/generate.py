#!/usr/bin/env python3
"""기존 compact geometry에 v0.8 hot-zone mount를 더해 final STEP을 생성한다."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

import FreeCAD as App
import Part
import importDXF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMPACT = ROOT / "cad" / "freecad" / "compact"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(COMPACT))

from geometry import assembly_objects, one_solid  # noqa: E402
from cad.freecad.compact.generate import _projection_polylines, normalize_dxf, normalize_step, normalize_zip_container  # noqa: E402

PARAMS = json.loads((ROOT / "cad/parameters/final_v08.json").read_text())
OUT = ROOT / "exports" / "final" / "step"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mount_plate(x: float, sliding: bool) -> Part.Shape:
    bore = PARAMS["hot_zone_mount"]["sliding_guide_bore_mm" if sliding else "fixed_collar_bore_mm"]
    vertical = Part.makeBox(8, 54, 68, App.Vector(x, 320, 348))
    foot = Part.makeBox(8, 150, 8, App.Vector(x, 270, 340))
    shape = vertical.fuse(foot)
    shape = shape.cut(Part.makeCylinder(bore / 2, 8, App.Vector(x, 347, 382), App.Vector(1, 0, 0)))
    for y in (280, 410):
        shape = shape.cut(Part.makeCylinder(3.3, 8, App.Vector(x + 4, y, 340)))
    # Open-top C-saddles preserve the feed throat (rear) and thermal-fuse
    # service path (front); radial gravity support remains in metal below.
    if sliding:
        shape = shape.cut(Part.makeBox(8, 16, 18, App.Vector(x, 339, 398)))
    else:
        shape = shape.cut(Part.makeBox(8, 54, 18, App.Vector(x, 320, 398)))
        for y in (312, 374):
            shape = shape.fuse(Part.makeBox(8, 8, 50, App.Vector(x, y, 348)))
        for y, z in PARAMS["rear_axial_retainer"]["bolt_centres_yz_mm"]:
            shape = shape.cut(Part.makeCylinder(2.25, 8, App.Vector(x, y, z), App.Vector(1, 0, 0)))
    return one_solid(shape)


def fixed_collar() -> Part.Shape:
    mount = PARAMS["hot_zone_mount"]
    length = mount["fixed_collar_length_mm"]
    x = mount["rear_fixed_plate_x_mm"] + mount["plate_thickness_mm"]
    collar = Part.makeCylinder(25, length, App.Vector(x, 347, 382), App.Vector(1, 0, 0))
    collar = collar.cut(Part.makeCylinder(mount["fixed_collar_bore_mm"] / 2, length,
                                         App.Vector(x, 347, 382), App.Vector(1, 0, 0)))
    collar = collar.cut(Part.makeBox(length, 50, 16, App.Vector(x, 322, 398)))
    shoulder = PARAMS["rear_axial_retainer"]
    collar = collar.cut(Part.makeCylinder(shoulder["collar_counterbore_mm"] / 2,
                                          shoulder["barrel_shoulder_length_mm"],
                                          App.Vector(x + length - shoulder["barrel_shoulder_length_mm"], 347, 382), App.Vector(1, 0, 0)))
    return one_solid(collar)


def rear_retainer_shapes() -> tuple[Part.Shape, list[tuple[float, Part.Shape]], list[tuple[float, Part.Shape]]]:
    spec = PARAMS["rear_axial_retainer"]
    cap_x = PARAMS["hot_zone_mount"]["rear_fixed_plate_x_mm"] + 8 + spec["spacer_length_mm"] + spec["rear_rib_mm"]
    cap = Part.makeBox(spec["retainer_thickness_mm"], 70, 50, App.Vector(cap_x, 312, 348))
    cap = cap.cut(Part.makeCylinder(17.05, spec["retainer_thickness_mm"], App.Vector(cap_x, 347, 382), App.Vector(1, 0, 0)))
    for y in (312, 372):
        cap = cap.fuse(Part.makeBox(spec["rear_rib_mm"], 10, 50, App.Vector(cap_x-spec["rear_rib_mm"], y, 348)))
    spacers, bolts = [], []
    for y, z in spec["bolt_centres_yz_mm"]:
        cap = cap.cut(Part.makeCylinder(1.65, spec["retainer_thickness_mm"] + spec["rear_rib_mm"],
                                        App.Vector(cap_x-spec["rear_rib_mm"], y, z), App.Vector(1, 0, 0)))
        spacer = Part.makeCylinder(spec["spacer_od_mm"] / 2, spec["spacer_length_mm"], App.Vector(363, y, z), App.Vector(1, 0, 0))
        spacer = spacer.cut(Part.makeCylinder(spec["spacer_id_mm"] / 2, spec["spacer_length_mm"], App.Vector(363, y, z), App.Vector(1, 0, 0)))
        bolt = Part.makeCylinder(2, 25, App.Vector(355, y, z), App.Vector(1, 0, 0)).fuse(
            Part.makeCylinder(3.5, 4, App.Vector(351, y, z), App.Vector(1, 0, 0)))
        spacers.append((y, one_solid(spacer)))
        bolts.append((y, one_solid(bolt)))
    return one_solid(cap.removeSplitter()), spacers, bolts


def final_objects() -> list[dict]:
    objects = list(assembly_objects())
    mount = PARAMS["hot_zone_mount"]
    # Bracket feet pass through close-fitting shield slots. The top panel and
    # both side sheets remain connected; final sheet drawing requires a folded
    # external baffle over each 10x10 slot.
    for item in objects:
        if item["name"] == "HotShield":
            for x in (mount["front_sliding_plate_x_mm"], mount["rear_fixed_plate_x_mm"]):
                for y in (309, 382):
                    item["shape"] = one_solid(item["shape"].cut(Part.makeBox(10, 4, 10, App.Vector(x - 1, y, 339))))
    retainer, spacers, retainer_bolts = rear_retainer_shapes()
    additions = [
        ("ExtruderSupportRailRear", Part.makeBox(mount["support_rail_length_mm"], 20, 20, App.Vector(20, 400, mount["support_rail_z_mm"])), "frame", f"2020 aluminum profile L{mount['support_rail_length_mm']:g}"),
        ("ExtruderRearFixedDatum", mount_plate(mount["rear_fixed_plate_x_mm"], False), "extruder", "EX-MT-01 8 mm S275 fixed datum plate"),
        ("ExtruderFrontSlidingGuide", mount_plate(mount["front_sliding_plate_x_mm"], True), "extruder", "EX-MT-02 8 mm S275 radial sliding guide"),
        ("ExtruderFixedCollar", fixed_collar(), "extruder", "EX-MT-03 S45C split collar"),
        ("ExtruderRearRetainer", retainer, "extruder", "EX-MT-05 4 mm S355J2 positive-stop retainer"),
    ]
    for name, shape, group, material in additions:
        objects.append({"name": name, "shape": shape, "group": group, "material": material, "classification": "manufactured_or_stock"})
    for y, shape in spacers:
        objects.append({"name": f"ExtruderRearRetainerSpacer{int(y)}", "shape": shape, "group": "extruder", "material": "EX-MT-06 OD8/ID4.5/L4.20 S275 steel spacer", "classification": "manufactured_or_stock"})
    for y, shape in retainer_bolts:
        objects.append({"name": f"RearRetainerM4_{int(y)}", "shape": shape, "group": "extruder", "material": "M4x25 class 8.8 SHCS", "classification": "purchased_fastener"})
    for plate, x in (("Front", mount["front_sliding_plate_x_mm"]), ("Rear", mount["rear_fixed_plate_x_mm"])):
        for side, y in (("Front", 280), ("Rear", 410)):
            bolt = Part.makeCylinder(2.5, 32, App.Vector(x + 4, y, 316))
            bolt = bolt.fuse(Part.makeCylinder(5, 4, App.Vector(x + 4, y, 348)))
            objects.append({"name": f"HotMountBolt{plate}{side}", "shape": one_solid(bolt), "group": "extruder", "material": "M5 class 8.8 + profile nut", "classification": "purchased_fastener"})
    return objects


def export(path: Path, objects: list[dict]) -> dict:
    doc = App.newDocument("v08_" + path.stem.replace("-", "_"))
    exported = []
    for item in objects:
        obj = doc.addObject("PartDesign::Feature", item["name"])
        obj.Shape = item["shape"]
        exported.append(obj)
    doc.recompute()
    if path.stem == "PPR-FULL-ASM":
        fcstd = ROOT / "cad/generation/fcstd/final_v08_full_assembly.FCStd"
        fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd, normalize_fcstd=True)
    Part.export(exported, str(path))
    normalize_step(path)
    expected_solids = sum(len(item["shape"].Solids) for item in objects)
    expected_volume = sum(item["shape"].Volume for item in objects)
    App.closeDocument(doc.Name)
    imported = Part.read(str(path))
    if not imported.isValid() or len(imported.Solids) != expected_solids:
        raise RuntimeError(f"{path.name}: STEP reimport solid mismatch {len(imported.Solids)} != {expected_solids}")
    error = abs(imported.Volume - expected_volume) / max(expected_volume, 1)
    if error > 1e-5:
        raise RuntimeError(f"{path.name}: STEP reimport volume drift {error}")
    box = imported.BoundBox
    return {
        "part_id": path.stem, "revision": PARAMS["revision"],
        "source_object": ";".join(item["name"] for item in objects),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "file": str(path.relative_to(OUT)), "format": "AP214_FALLBACK_FREECAD", "units": "mm",
        "body_count": len(objects), "solid_count": expected_solids,
        "bbox_mm": [round(box.XLength, 6), round(box.YLength, 6), round(box.ZLength, 6)],
        "volume_mm3": round(imported.Volume, 6), "mass_g": "",
        "sha256": sha256(path), "status": "PASS", "release_gate": "USER_APPROVAL_REQUIRED",
    }


def export_assembly_metadata(objects: list[dict]) -> None:
    compound = Part.makeCompound([item["shape"] for item in objects])
    box = compound.BoundBox
    metadata = {
        "revision": PARAMS["revision"],
        "bounding_box_mm": [round(box.XLength, 2), round(box.YLength, 2), round(box.ZLength, 2)],
        "minimum_mm": [round(box.XMin, 2), round(box.YMin, 2), round(box.ZMin, 2)],
        "maximum_mm": [round(box.XMax, 2), round(box.YMax, 2), round(box.ZMax, 2)],
        "object_count": len(objects),
        "reference_component_policy": "manufacturing, purchased-reference and fastener solids are classified; keep-outs remain in cad/review_keepouts",
        "includes": ["closed lid", "guards", "hot-zone fixed/sliding mount", "mount fasteners", "cable duct", "1 kg spool", "dancer arm", "traverse rail"],
        "excludes": ["motion and service keep-outs; see cad/review_keepouts"],
    }
    generation = ROOT / "cad/generation"
    (generation / "assembly_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    with (generation / "assembly_classification.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("object", "group", "material", "classification", "shape_type", "solid_count", "volume_mm3", "mass_override_kg", "evidence"))
        for item in objects:
            writer.writerow((item["name"], item["group"], item["material"], item["classification"], item["shape"].ShapeType,
                             len(item["shape"].Solids), f'{item["shape"].Volume:.3f}', item.get("mass_override_kg") or "", item.get("evidence", "")))


def export_hot_zone_drawings(additions: list[dict]) -> None:
    out = ROOT / "exports/final/manufacturing/hot_zone"
    out.mkdir(parents=True, exist_ok=True)
    for item in additions:
        for suffix in (".dxf", ".svg"):
            (out / f'{item["name"]}{suffix}').unlink(missing_ok=True)
        doc = App.newDocument("dxf_" + item["name"])
        obj = doc.addObject("PartDesign::Feature", item["name"]); obj.Shape = item["shape"]
        dxf = out / f'{item["name"]}.dxf'
        importDXF.export([obj], str(dxf)); normalize_dxf(dxf)
        App.closeDocument(doc.Name)
        bb = item["shape"].BoundBox
        views = (
            _projection_polylines(item["shape"], ("x", "y"), (25, 90, 335, 245)),
            _projection_polylines(item["shape"], ("x", "z"), (390, 90, 335, 245)),
            _projection_polylines(item["shape"], ("y", "z"), (755, 90, 335, 245)),
        )
        note = html.escape(
            f'{item["name"]} | {item["material"]} | overall X {bb.XLength:.2f}, Y {bb.YLength:.2f}, Z {bb.ZLength:.2f} mm'
        )
        (out / f'{item["name"]}.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">
<rect width="1123" height="794" fill="white"/><rect x="12" y="12" width="1099" height="770" fill="none" stroke="#111" stroke-width="2"/>
<g font-family="Noto Sans CJK KR,sans-serif" fill="#111"><text x="28" y="48" font-size="24" font-weight="bold">{html.escape(item["name"])} · v0.8</text>
<text x="28" y="74" font-size="15">단위 mm · 제3각법 · 일반공차 ISO 2768-m · 모서리 burr 제거</text>
<text x="35" y="112" font-size="15">TOP X-Y</text>{views[0]}<text x="400" y="112" font-size="15">FRONT X-Z</text>{views[1]}<text x="765" y="112" font-size="15">SIDE Y-Z</text>{views[2]}
<text x="28" y="390" font-size="17">{note}</text><text x="28" y="423" font-size="16">치수 판정은 CAD/STEP과 RFQ 표를 우선한다. 무단 재료·공차 변경 금지.</text>
<text x="28" y="456" font-size="16">Source: cad/freecad/final_v08/generate.py · Revision: final-design-fabrication-closure-v0.8</text></g></svg>\n''')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-assemblies", action="store_true", help="Refresh assembly STEP/FCStd only; preserve other release artifacts")
    args = parser.parse_args()
    manifest = OUT / "step_manifest.csv"
    previous = []
    if args.refresh_assemblies:
        with manifest.open(newline="") as stream:
            previous = list(csv.DictReader(stream))
    if OUT.exists() and not args.refresh_assemblies:
        shutil.rmtree(OUT)
    assembly = OUT / "assembly"
    parts = OUT / "cnc_parts"
    assembly.mkdir(parents=True, exist_ok=True)
    parts.mkdir(parents=True, exist_ok=True)
    objects = final_objects()
    # Selected GGM drive supersedes the historical tiny donor envelopes.
    if (ROOT / "control/ggm_drive_contract.json").is_file():
        sys.path.insert(0, str(ROOT / "cad/freecad/drive_v08"))
        from cad.freecad.drive_v08.assembly import integrated_objects
        objects, _ = integrated_objects(objects)
    export_assembly_metadata(objects)
    groups = {
        "PPR-FULL-ASM.step": objects,
        "PPR-SHREDDER-ASM.step": [item for item in objects if item["group"] == "shredder"],
        "PPR-FEEDER-ASM.step": [item for item in objects if item["group"] in {"input", "feed"}],
        "PPR-EXTRUDER-ASM.step": [item for item in objects if item["group"] == "extruder"],
        "PPR-FORMING-ASM.step": [item for item in objects if item["group"] in {"forming", "spooler"}],
        "PPR-FRAME-ASM.step": [item for item in objects if item["group"] == "frame"],
    }
    additions = {item["name"]: item for item in objects if item["name"] in {
        "ExtruderSupportRailRear", "ExtruderRearFixedDatum", "ExtruderFrontSlidingGuide", "ExtruderFixedCollar",
        "ExtruderRearRetainer", "ExtruderRearRetainerSpacer318",
    }}
    rows = [export(assembly / name, items) for name, items in groups.items()]
    if args.refresh_assemblies:
        prior_by_file = {row["file"]: row for row in previous}
        for index, row in enumerate(rows):
            prior = prior_by_file.get(row["file"], {})
            rows[index] = {**prior, **row,
                           "release_gate": prior.get("release_gate") or row.get("release_gate") or "USER_APPROVAL_REQUIRED"}
        replaced = {row["file"] for row in rows}
        rows += [row for row in previous if row["file"] not in replaced]
        with manifest.open("w", newline="", encoding="utf-8") as stream:
            fields = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        print(f"V08_ASSEMBLY_REFRESH_OK assemblies={len(groups)} manifest_rows={len(rows)}")
        return
    rows += [export(parts / f"{name}.step", [item]) for name, item in additions.items()]
    export_hot_zone_drawings(list(additions.values()))
    manifest = OUT / "step_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    (OUT / "README.md").write_text(
        "# v0.8 final STEP\n\nFreeCAD 1.1.3의 STEP writer가 AP242를 보장하지 않아 AP214 fallback으로 내보냈다. "
        "모든 파일은 즉시 재수입해 solid count와 volume을 검증한다.\n"
    )
    print(f"V08_FINAL_STEP_OK files={len(rows)} objects={len(objects)}")


if __name__ == "__main__":
    main()
