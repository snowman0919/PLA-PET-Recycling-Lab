"""Shared FreeCAD generation helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

import FreeCAD as App
import Mesh
import Part


ROOT = Path(__file__).resolve().parents[3]
PARAMETERS = ROOT / "cad" / "parameters" / "baseline.json"
REPRODUCIBLE_STEP_TIMESTAMP = "2000-01-01T00:00:00"


def load_parameters() -> dict:
    return json.loads(PARAMETERS.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def add_feature(doc, name: str, label: str, shape, part_id: str, material: str):
    obj = doc.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "PartID", "BOM")
    obj.PartID = part_id
    obj.addProperty("App::PropertyString", "Material", "BOM")
    obj.Material = material
    return obj


def export_document(doc, stem: str, export_objects=None) -> dict[str, str]:
    step_dir = ensure_dir(ROOT / "exports" / "step")
    stl_dir = ensure_dir(ROOT / "exports" / "stl")
    fcstd_dir = ensure_dir(ROOT / "cad" / "generation" / "fcstd")
    doc.recompute()
    fcstd_path = fcstd_dir / f"{stem}.FCStd"
    step_path = step_dir / f"{stem}.step"
    stl_path = stl_dir / f"{stem}.stl"
    doc.saveAs(str(fcstd_path))
    objects = export_objects or [o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
    Part.export(objects, str(step_path))
    step_text = step_path.read_text(encoding="ascii")
    step_text, substitutions = re.subn(
        r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'",
        f"'{REPRODUCIBLE_STEP_TIMESTAMP}'",
        step_text,
        count=1,
    )
    if substitutions != 1:
        raise RuntimeError(f"could not normalize STEP timestamp: {step_path}")
    step_path.write_text(step_text, encoding="ascii", newline="\n")
    Mesh.export(objects, str(stl_path))
    return {
        "fcstd": str(fcstd_path.relative_to(ROOT)),
        "step": str(step_path.relative_to(ROOT)),
        "stl": str(stl_path.relative_to(ROOT)),
    }


def bounding_box_report(obj) -> dict[str, float | bool]:
    bb = obj.Shape.BoundBox
    limit = float(load_parameters()["print_bed_limit_mm"])
    return {
        "x_mm": round(bb.XLength, 3),
        "y_mm": round(bb.YLength, 3),
        "z_mm": round(bb.ZLength, 3),
        "fits_210_cube": bb.XLength <= limit and bb.YLength <= limit and bb.ZLength <= limit,
    }
