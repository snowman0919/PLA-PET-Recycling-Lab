#!/usr/bin/env python3
"""Build and verify the deterministic v0.8 print release from authoritative exports."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validation.mesh_checks import audit, triangles  # noqa: E402

SOURCE = ROOT / "exports/print"
OUT = ROOT / "exports/final/print"
REVISION = "final-design-fabrication-closure-v0.8"
PART_IDS = tuple(f"PPR-C{index:02d}" for index in range(1, 13))
NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
FIELDS = (
    "revision", "part_id", "name", "quantity", "material", "orientation", "support",
    "layer_height", "perimeters", "top_bottom_layers", "infill", "postprocess",
    "critical_dimensions", "mating_part", "expected_mass_each_g", "slicer_mass_total_g",
    "estimated_print_time_s", "bbox_mm", "stl_file", "three_mf_file", "step_reference_file",
    "plate_layout_file", "orientation_render", "triangle_count", "watertight", "manifold",
    "positive_volume", "connected_components", "within_210mm", "orientation_documented",
    "plate_quantity_match", "plate_inside_220mm", "bom_quantity_match",
    "assembly_quantity_match", "three_mf_stl_geometry_match", "three_mf_revision_match",
    "slicer_status", "physical_fit_status", "status", "sha256_stl", "sha256_3mf",
    "sha256_step", "sha256_plate", "sha256_orientation_render",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def mesh_stats(items: list[tuple[tuple[float, float, float], ...]]) -> tuple[tuple[float, float, float], float]:
    points = [point for triangle in items for point in triangle]
    bbox = tuple(max(point[axis] for point in points) - min(point[axis] for point in points) for axis in range(3))
    signed = sum(
        (a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
        for a, b, c in items
    )
    return bbox, abs(signed)


def model_xml(path: Path) -> bytes:
    with zipfile.ZipFile(path) as package:
        names = [name for name in package.namelist() if name.lower().endswith(".model")]
        if len(names) != 1:
            raise RuntimeError(f"{path}: expected one 3MF model, got {names}")
        return package.read(names[0])


def three_mf_mesh(path: Path) -> tuple[list[tuple[tuple[float, float, float], ...]], ET.Element]:
    root = ET.fromstring(model_xml(path))
    mesh = root.find(".//m:object[@type='model']/m:mesh", NS)
    if mesh is None:
        raise RuntimeError(f"{path}: no model mesh")
    vertices = [tuple(float(vertex.get(axis, "nan")) for axis in "xyz") for vertex in mesh.findall("m:vertices/m:vertex", NS)]
    result = [tuple(vertices[int(triangle.get(key, "-1"))] for key in ("v1", "v2", "v3")) for triangle in mesh.findall("m:triangles/m:triangle", NS)]
    return result, root


def normalized_3mf(source: Path, target: Path, title: str) -> None:
    with zipfile.ZipFile(source) as source_zip, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as target_zip:
        for member in sorted(source_zip.infolist(), key=lambda item: item.filename):
            data = source_zip.read(member.filename)
            if member.filename.lower().endswith(".model"):
                text = data.decode("utf-8")
                text = re.sub(r'(<metadata name="(?:CreationDate|ModificationDate)">).*?(</metadata>)', r"\g<1>2000-01-01\2", text)
                text = re.sub(r'\s*<metadata name="PPR:Revision">.*?</metadata>', "", text)
                text = re.sub(r'\s*<metadata name="PPR:Part">.*?</metadata>', "", text)
                insertion = f'\n <metadata name="PPR:Revision">{REVISION}</metadata>\n <metadata name="PPR:Part">{title}</metadata>'
                text = re.sub(r"(<model\b[^>]*>)", r"\1" + insertion, text, count=1)
                data = text.encode("utf-8")
            info = zipfile.ZipInfo(member.filename, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = member.external_attr
            info.create_system = member.create_system
            target_zip.writestr(info, data)


def revision_in_3mf(path: Path) -> str:
    root = ET.fromstring(model_xml(path))
    for metadata in root.findall("m:metadata", NS):
        if metadata.get("name") == "PPR:Revision":
            return metadata.text or ""
    return ""


def build_count_and_bounds(path: Path) -> tuple[int, bool]:
    mesh, root = three_mf_mesh(path)
    points = [point for triangle in mesh for point in triangle]
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    items = root.findall("m:build/m:item", NS)
    inside = True
    for item in items:
        values = [float(value) for value in item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0").split()]
        if len(values) != 12 or any(abs(values[index] - expected) > 1e-9 for index, expected in enumerate((1, 0, 0, 0, 1, 0, 0, 0, 1))):
            inside = False
            continue
        translated_low = [low[axis] + values[9 + axis] for axis in range(3)]
        translated_high = [high[axis] + values[9 + axis] for axis in range(3)]
        inside &= translated_low[0] >= -1e-6 and translated_low[1] >= -1e-6 and translated_low[2] >= -1e-6
        inside &= translated_high[0] <= 220.0 + 1e-6 and translated_high[1] <= 220.0 + 1e-6 and translated_high[2] <= 220.0 + 1e-6
    return len(items), inside


def quantities() -> tuple[dict[str, int], dict[str, int]]:
    bom_path = ROOT / "exports/final/bom/BOM.csv"
    bom = {
        row["part_id"]: int(row["quantity"])
        for row in csv_rows(bom_path)
        if row.get("part_id") in PART_IDS
    } if bom_path.is_file() else {}
    assembly_rows = csv_rows(ROOT / "cad/generation/assembly_classification.csv")
    assembly = {part_id: sum(row["object"].startswith(part_id) for row in assembly_rows) for part_id in PART_IDS}
    return bom, assembly


def copy_inputs(source_row: dict[str, str], index: int) -> tuple[Path, Path, Path, Path, Path]:
    part_id = source_row["part_id"]
    stl = OUT / "STL" / f"{part_id}.stl"
    three = OUT / "3MF" / f"{part_id}.3mf"
    step = OUT / "STEP_REFERENCE" / f"{part_id}.step"
    plate = OUT / "plate_layouts" / f"plate-{index:02d}-{part_id}.3mf"
    render = OUT / "orientation_renders" / f"{part_id}-first-layer.svg"
    shutil.copyfile(SOURCE / part_id / f"{part_id}.stl", stl)
    shutil.copyfile(SOURCE / part_id / f"{part_id}.step", step)
    normalized_3mf(SOURCE / part_id / f"{part_id}.3mf", three, part_id)
    normalized_3mf(SOURCE / "plate_layouts" / plate.name, plate, f"{part_id}-plate")
    shutil.copyfile(SOURCE / "slicing_previews" / f"plate-{index:02d}-{part_id}-first-layer.svg", render)
    return stl, three, step, plate, render


def build_row(source_row: dict[str, str], index: int, bom: dict[str, int], assembly: dict[str, int]) -> dict[str, str]:
    part_id = source_row["part_id"]
    stl, three, step, plate, render = copy_inputs(source_row, index)
    stl_triangles = list(triangles(stl))
    stl_bbox, stl_volume = mesh_stats(stl_triangles)
    three_triangles, _ = three_mf_mesh(three)
    three_bbox, three_volume = mesh_stats(three_triangles)
    topology = audit(stl)
    count, plate_inside = build_count_and_bounds(plate)
    geometry_match = (
        len(stl_triangles) == len(three_triangles)
        and max(abs(a - b) for a, b in zip(stl_bbox, three_bbox)) <= 1e-3
        and abs(stl_volume - three_volume) / max(stl_volume, 1.0) <= 1e-5
    )
    quantity = int(source_row["quantity"])
    checks = {
        "watertight": topology["nonmanifold_edges"] == 0,
        "manifold": topology["zero_area_triangles"] == 0 and topology["nonmanifold_edges"] == 0,
        "positive_volume": stl_volume > 0,
        "within_210mm": max(stl_bbox) <= 210.0 + 1e-6,
        "orientation_documented": bool(source_row["orientation"].strip()) and render.stat().st_size > 500,
        "plate_quantity_match": count == quantity,
        "plate_inside_220mm": plate_inside,
        "bom_quantity_match": bom.get(part_id) == quantity,
        "assembly_quantity_match": assembly.get(part_id) == quantity,
        "three_mf_stl_geometry_match": geometry_match,
        "three_mf_revision_match": revision_in_3mf(three) == REVISION,
        "slicer_status": source_row["slicer_status"] == "PASS",
    }
    status = "PASS" if topology["connected_components"] == 1 and all(checks.values()) else "HOLD"
    postprocess = "; ".join(filter(lambda value: value and value != "none", (
        source_row["support_removal"], source_row["insert_or_nut"], source_row["tolerance"],
    ))) or "none"
    return {
        "revision": REVISION, "part_id": part_id, "name": source_row["name"],
        "quantity": str(quantity), "material": source_row["material"], "orientation": source_row["orientation"],
        "support": source_row["support"], "layer_height": source_row["layer_height"],
        "perimeters": source_row["walls"], "top_bottom_layers": source_row["top_bottom_layers"],
        "infill": source_row["infill"], "postprocess": postprocess,
        "critical_dimensions": f"{source_row['interfaces']}; tolerance {source_row['tolerance']}",
        "mating_part": source_row["mating_part"], "expected_mass_each_g": source_row["cad_net_mass_each_g"],
        "slicer_mass_total_g": source_row["slicer_mass_total_g"], "estimated_print_time_s": source_row["slicer_time_s"],
        "bbox_mm": "x".join(f"{value:.6f}" for value in stl_bbox),
        "stl_file": f"STL/{stl.name}", "three_mf_file": f"3MF/{three.name}",
        "step_reference_file": f"STEP_REFERENCE/{step.name}", "plate_layout_file": f"plate_layouts/{plate.name}",
        "orientation_render": f"orientation_renders/{render.name}", "triangle_count": str(len(stl_triangles)),
        "watertight": "PASS" if checks["watertight"] else "FAIL",
        "manifold": "PASS" if checks["manifold"] else "FAIL",
        "positive_volume": "PASS" if checks["positive_volume"] else "FAIL",
        "connected_components": str(topology["connected_components"]),
        "within_210mm": "PASS" if checks["within_210mm"] else "FAIL",
        "orientation_documented": "PASS" if checks["orientation_documented"] else "FAIL",
        "plate_quantity_match": "PASS" if checks["plate_quantity_match"] else "FAIL",
        "plate_inside_220mm": "PASS" if checks["plate_inside_220mm"] else "FAIL",
        "bom_quantity_match": "PASS" if checks["bom_quantity_match"] else "HOLD",
        "assembly_quantity_match": "PASS" if checks["assembly_quantity_match"] else "HOLD",
        "three_mf_stl_geometry_match": "PASS" if checks["three_mf_stl_geometry_match"] else "FAIL",
        "three_mf_revision_match": "PASS" if checks["three_mf_revision_match"] else "FAIL",
        "slicer_status": "PASS" if checks["slicer_status"] else "FAIL",
        "physical_fit_status": "HOLD_NOT_RUN", "status": status,
        "sha256_stl": sha256(stl), "sha256_3mf": sha256(three), "sha256_step": sha256(step),
        "sha256_plate": sha256(plate), "sha256_orientation_render": sha256(render),
    }


def write_settings() -> None:
    (OUT / "print_settings_ko.md").write_text("""# v0.8 3D 출력 설정

- 기준: PrusaSlicer 2.9.6, 0.4 mm nozzle, `exports/print/slicer_profiles/PPR_PrusaSlicer_2.9.6.ini`.
- 내부 release envelope는 각 축 210 mm 이하이며, plate 배치는 220 × 220 × 220 mm를 초과하지 않는다.
- part별 재료·방향·layer·wall·top/bottom·infill·support·후처리는 `print_manifest.csv`가 지배한다.
- `orientation_renders/`는 실제 released G-code의 first-layer 경로다. 3MF plate 수량과 bed bounds를 생성기가 검사한다.
- PPR-TC01 coupon을 먼저 출력하고 실제 bore/shaft/insert 보정을 기록한 뒤 critical fit을 ream/후처리한다.
- ABS 지정 PPR-C05/C06/C07도 hot-zone 내부 구조재로 쓰지 않는다. 조립 후 표면온도와 shield clearance 확인 전 가열 금지.
- STL/3MF manifold 및 디지털 수량 검사는 PASS이나 `physical_fit_status`는 실제 출력 전까지 `HOLD_NOT_RUN`이다.
""", encoding="utf-8")


def verify(data: list[dict[str, str]]) -> dict[str, object]:
    if len(data) != 12 or {row["part_id"] for row in data} != set(PART_IDS):
        raise RuntimeError("print release requires exactly PPR-C01..PPR-C12")
    required_pass = (
        "watertight", "manifold", "positive_volume", "within_210mm", "orientation_documented",
        "plate_quantity_match", "plate_inside_220mm", "bom_quantity_match", "assembly_quantity_match",
        "three_mf_stl_geometry_match", "three_mf_revision_match", "slicer_status",
    )
    for row in data:
        for field in ("stl_file", "three_mf_file", "step_reference_file", "plate_layout_file", "orientation_render"):
            path = OUT / row[field]
            if not path.is_file() or sha256(path) != row[{"stl_file": "sha256_stl", "three_mf_file": "sha256_3mf", "step_reference_file": "sha256_step", "plate_layout_file": "sha256_plate", "orientation_render": "sha256_orientation_render"}[field]]:
                raise RuntimeError(f"{row['part_id']}: missing/hash mismatch {field}")
        if row["connected_components"] != "1" or any(row[field] != "PASS" for field in required_pass) or row["status"] != "PASS":
            raise RuntimeError(f"{row['part_id']}: print digital gate not closed")
    report = {
        "revision": REVISION, "digital_status": "PASS", "part_count": len(data),
        "physical_fit_status": "HOLD_NOT_RUN", "physical_validation_state": "NOT_RUN",
        "checks": {field: "PASS" for field in required_pass},
        "notes": [
            "Per-part 3MF receives deterministic PPR:Revision metadata; mesh triangle count/bounds/volume match released STL.",
            "BOM quantity is checked against exports/final/bom/BOM.csv and assembly quantity against cad/generation/assembly_classification.csv.",
            "Digital manifold/slicer evidence does not replace tolerance-coupon, insert, thermal-clearance or assembled-fit inspection.",
        ],
    }
    (OUT / "print_release_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    source_rows = csv_rows(SOURCE / "print_manifest.csv")
    if [row["part_id"] for row in source_rows] != list(PART_IDS):
        raise SystemExit("authoritative print manifest does not contain ordered PPR-C01..PPR-C12")
    if OUT.exists():
        shutil.rmtree(OUT)
    for directory in ("STL", "3MF", "STEP_REFERENCE", "plate_layouts", "orientation_renders"):
        (OUT / directory).mkdir(parents=True)
    bom, assembly = quantities()
    built = [build_row(row, index, bom, assembly) for index, row in enumerate(source_rows, 1)]
    shutil.copyfile(ROOT / "renders/review/print_orientation.png", OUT / "orientation_renders/overview.png")
    write_settings()
    with (OUT / "print_manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(built)
    report = verify(built)
    print(f"V08_PRINT_RELEASE_OK parts={report['part_count']} digital={report['digital_status']} physical={report['physical_fit_status']}")


if __name__ == "__main__":
    main()
