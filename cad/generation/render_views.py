#!/usr/bin/env python3
"""Render standard PNG review views from STL without an OpenGL context."""

from __future__ import annotations

from math import sqrt
from pathlib import Path

import vtk
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
RENDERS = ROOT / "renders"
WIDTH, HEIGHT, MARGIN = 1600, 1200, 70


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def normalize(v):
    mag = sqrt(dot(v, v))
    return tuple(x / mag for x in v)


def triangles_from_stl(source: Path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(source))
    reader.Update()
    data = reader.GetOutput()
    ids = vtk.vtkIdList()
    cells = data.GetPolys()
    cells.InitTraversal()
    triangles = []
    while cells.GetNextCell(ids):
        points = [data.GetPoint(ids.GetId(i)) for i in range(ids.GetNumberOfIds())]
        if len(points) == 3:
            triangles.append(points)
    if not triangles:
        raise RuntimeError(f"no triangles in {source}")
    return triangles


def shaded(base, normal, camera_direction):
    facing = abs(dot(normalize(normal), camera_direction))
    factor = 0.58 + 0.38 * facing
    return tuple(max(0, min(255, round(255 * channel * factor))) for channel in base)


def render_view(triangles, target: Path, base_colour, camera_direction, nominal_up):
    cam = normalize(camera_direction)
    right = normalize(cross(nominal_up, cam))
    up = normalize(cross(cam, right))
    projected = []
    xs, ys = [], []
    for triangle in triangles:
        plane = [(dot(point, right), dot(point, up), dot(point, cam)) for point in triangle]
        xs.extend(p[0] for p in plane)
        ys.extend(p[1] for p in plane)
        edge1 = subtract(triangle[1], triangle[0])
        edge2 = subtract(triangle[2], triangle[0])
        projected.append((sum(p[2] for p in plane) / 3, plane, cross(edge1, edge2)))
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    scale = min((WIDTH - 2 * MARGIN) / max(span_x, 1e-9), (HEIGHT - 2 * MARGIN) / max(span_y, 1e-9))
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2

    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    # Low depth is farther from a camera placed in +cam direction.
    for _depth, plane, normal in sorted(projected, key=lambda item: item[0]):
        polygon = [
            (WIDTH / 2 + (x - center_x) * scale, HEIGHT / 2 - (y - center_y) * scale)
            for x, y, _z in plane
        ]
        draw.polygon(polygon, fill=shaded(base_colour, normal, cam), outline=(42, 42, 42), width=1)
    image.save(target)


def render(stem: str, category: str, colour: tuple[float, float, float]) -> None:
    triangles = triangles_from_stl(ROOT / "exports" / "stl" / f"{stem}.stl")
    output = RENDERS / category
    output.mkdir(parents=True, exist_ok=True)
    views = {
        "front": ((0, -1, 0), (0, 0, 1)),
        "rear": ((0, 1, 0), (0, 0, 1)),
        "left": ((-1, 0, 0), (0, 0, 1)),
        "right": ((1, 0, 0), (0, 0, 1)),
        "top": ((0, 0, 1), (0, 1, 0)),
        "bottom": ((0, 0, -1), (0, 1, 0)),
        "isometric": ((1, -1, 0.8), (0, 0, 1)),
    }
    for name, (direction, up) in views.items():
        render_view(triangles, output / f"{stem}_{name}.png", colour, direction, up)


def main() -> None:
    render("tolerance_coupon", "modules", (0.95, 0.70, 0.15))
    render("stage1_cutter_stack", "modules", (0.72, 0.34, 0.18))
    render("stage1_shredder_proof", "modules", (0.78, 0.35, 0.22))
    render("full_assembly_skeleton", "assembly", (0.35, 0.62, 0.86))


if __name__ == "__main__":
    main()
