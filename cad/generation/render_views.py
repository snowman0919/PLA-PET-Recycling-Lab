#!/usr/bin/env python3
"""Render standard PNG review views from STL without an OpenGL context."""

from __future__ import annotations

from math import sqrt
from pathlib import Path

import vtk
from PIL import Image, ImageDraw, ImageFont


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


def render_view(triangles, target: Path, base_colour, camera_direction, nominal_up,
                mode="solid", colour_for=None, annotation=None):
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
        projected.append((sum(p[2] for p in plane) / 3, plane, cross(edge1, edge2), triangle))
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    scale = min((WIDTH - 2 * MARGIN) / max(span_x, 1e-9), (HEIGHT - 2 * MARGIN) / max(span_y, 1e-9))
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2

    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    # Low depth is farther from a camera placed in +cam direction.
    for _depth, plane, normal, triangle in sorted(projected, key=lambda item: item[0]):
        polygon = [
            (WIDTH / 2 + (x - center_x) * scale, HEIGHT / 2 - (y - center_y) * scale)
            for x, y, _z in plane
        ]
        if mode == "wireframe":
            draw.line(polygon + [polygon[0]], fill=(74, 103, 119), width=1)
        else:
            colour = colour_for(triangle) if colour_for else base_colour
            draw.polygon(polygon, fill=shaded(colour, normal, cam), outline=(42, 42, 42), width=1)
    if annotation:
        annotation(draw, image)
    image.save(target)


def triangle_centroid(triangle):
    return tuple(sum(point[axis] for point in triangle) / 3 for axis in range(3))


def assembly_colour(triangle):
    """Decision-review colours for the two-tower architecture STL.

    STL has no material metadata, so this deterministic spatial map makes the
    frame, process zones and two tower roles distinguishable without implying
    final paint or polymer selection.
    """
    x, y, z = triangle_centroid(triangle)
    aluminium = (0.62, 0.66, 0.68)
    if x < 620:
        if x < 90 or x > 510 or y < 90 or y > 510:
            return aluminium
        if z < 225:
            return (0.28, 0.56, 0.38)  # sealed batch storage
        if z < 410:
            return (0.25, 0.52, 0.70)  # sorter
        if z < 1040:
            return (0.72, 0.34, 0.20)  # three-stage size reduction
        return (0.30, 0.57, 0.76)      # optical input classifier
    if x < 850:
        return (0.88, 0.88, 0.88)      # deliberate separation corridor
    if x <= 1750:
        if x < 1240 and z > 450:
            return (0.79, 0.56, 0.20)  # dryer / batch dock
        if y > 275 and z < 350:
            return (0.72, 0.25, 0.16)  # guarded extruder hot line
        if x > 1320 and y < 270 and z < 430:
            return (0.35, 0.40, 0.46)  # grounded controls / energy zone
        return aluminium
    if y < 290:
        return (0.28, 0.43, 0.65)      # offset spooler
    if z < 90:
        return aluminium               # straight 2040 service rail
    return (0.23, 0.58, 0.72)          # cooling / gauge / puller


def section_triangles(triangles, axis=1, retained_fraction=0.52):
    centroids = [triangle_centroid(triangle)[axis] for triangle in triangles]
    low, high = min(centroids), max(centroids)
    cut = low + retained_fraction * (high - low)
    kept = [triangle for triangle, value in zip(triangles, centroids) if value <= cut]
    if not kept:
        raise RuntimeError("empty section scene")
    return kept


def exploded_triangles(triangles, expansion=0.38):
    parent = list(range(len(triangles)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    owners = {}
    for index, triangle in enumerate(triangles):
        for point in triangle:
            key = tuple(round(value, 5) for value in point)
            prior = owners.setdefault(key, index)
            union(index, prior)
    groups = {}
    for index in range(len(triangles)):
        groups.setdefault(find(index), []).append(index)
    all_points = [point for triangle in triangles for point in triangle]
    global_center = tuple(sum(point[axis] for point in all_points) / len(all_points) for axis in range(3))
    transformed = [None] * len(triangles)
    for order, indices in enumerate(sorted(groups.values(), key=lambda group: min(group))):
        points = [point for index in indices for point in triangles[index]]
        center = tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))
        shift = tuple((center[axis] - global_center[axis]) * expansion for axis in range(3))
        if len(groups) > 1:
            shift = (shift[0], shift[1], shift[2] + ((order % 5) - 2) * 2.0)
        for index in indices:
            transformed[index] = [
                tuple(point[axis] + shift[axis] for axis in range(3))
                for point in triangles[index]
            ]
    return transformed


def label_annotation(title, subtitle=""):
    def annotate(draw, _image):
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        draw.rectangle((32, 28, 760, 96 if subtitle else 72), fill=(255, 255, 255), outline=(38, 74, 92), width=2)
        draw.text((48, 36), title, fill=(23, 62, 81), font=font)
        if subtitle:
            draw.text((48, 72), subtitle, fill=(70, 70, 70), font=small)
    return annotate


def cable_annotation(draw, _image):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    routes = [
        ((180, 900), (540, 700), (880, 760), (1380, 520)),
        ((210, 980), (610, 850), (1000, 900), (1420, 690)),
        ((170, 1050), (560, 1010), (940, 1040), (1390, 910)),
    ]
    colours = ((198, 48, 48), (32, 116, 176), (36, 142, 78))
    labels = ("PWR", "SENSOR", "PE")
    for points, colour, label in zip(routes, colours, labels):
        draw.line(points, fill=colour, width=10, joint="curve")
        draw.ellipse((points[-1][0] - 9, points[-1][1] - 9,
                      points[-1][0] + 9, points[-1][1] + 9), fill=colour)
        draw.text((points[0][0] - 10, points[0][1] - 38), label, fill=colour, font=font)
    label_annotation("CABLE ROUTING REVIEW", "schematic paths; verify harness lengths and bend radii")(draw, _image)


def tool_annotation(draw, _image):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    for x, y, radius in ((380, 630, 115), (790, 520, 100), (1180, 690, 130)):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                     outline=(206, 111, 25), width=8)
        draw.line((x, y, x + radius + 70, y - radius - 45), fill=(206, 111, 25), width=8)
    draw.text((1200, 420), "TOOL SWEEP", fill=(168, 78, 18), font=font)
    label_annotation("TOOL ACCESS REVIEW", "overlay is a service-volume prompt; physical reach test remains open")(draw, _image)


def render_review_variants():
    output = RENDERS / "review"
    output.mkdir(parents=True, exist_ok=True)
    iso = ((1, -1, 0.8), (0, 0, 1))
    sections = (
        "input_classifier_proof", "stage1_shredder_proof", "stage2_shredder_proof",
        "stage3_granulator_proof", "dryer_feeder_proof", "extruder_proof",
        "full_assembly_skeleton",
    )
    for stem in sections:
        triangles = triangles_from_stl(ROOT / "exports" / "stl" / f"{stem}.stl")
        render_view(section_triangles(triangles), output / f"{stem}_section.png",
                    (0.68, 0.43, 0.22), *iso,
                    colour_for=assembly_colour if stem == "full_assembly_skeleton" else None,
                    annotation=label_annotation("SECTION / CUTAWAY", "centroid-clipped review scene; no section cap"))
    transparent = (
        "input_classifier_proof", "dryer_feeder_proof", "extruder_proof",
        "control_enclosure_proof",
    )
    for stem in transparent:
        triangles = triangles_from_stl(ROOT / "exports" / "stl" / f"{stem}.stl")
        render_view(triangles, output / f"{stem}_transparent.png", (0.4, 0.65, 0.76), *iso,
                    mode="wireframe",
                    annotation=label_annotation("TRANSPARENT / X-RAY", "all triangle edges shown; hidden-line removal disabled"))
    exploded = (
        "full_assembly_skeleton", "stage1_shredder_proof", "dryer_feeder_proof",
        "extruder_proof", "spooler_proof",
    )
    for stem in exploded:
        triangles = triangles_from_stl(ROOT / "exports" / "stl" / f"{stem}.stl")
        render_view(exploded_triangles(triangles), output / f"{stem}_exploded.png",
                    (0.36, 0.58, 0.72), *iso,
                    colour_for=assembly_colour if stem == "full_assembly_skeleton" else None,
                    annotation=label_annotation("EXPLODED REVIEW", "connected shells displaced from assembly centroid"))
    for stem in ("full_assembly_skeleton", "extruder_proof", "spooler_proof"):
        triangles = triangles_from_stl(ROOT / "exports" / "stl" / f"{stem}.stl")
        render_view(triangles, output / f"{stem}_tool_access.png", (0.42, 0.59, 0.68), *iso,
                    colour_for=assembly_colour if stem == "full_assembly_skeleton" else None,
                    annotation=tool_annotation)
    for stem in ("full_assembly_skeleton", "control_enclosure_proof"):
        triangles = triangles_from_stl(ROOT / "exports" / "stl" / f"{stem}.stl")
        render_view(triangles, output / f"{stem}_cable_routing.png", (0.52, 0.58, 0.62), *iso,
                    colour_for=assembly_colour if stem == "full_assembly_skeleton" else None,
                    annotation=cable_annotation)
    triangles = triangles_from_stl(ROOT / "exports" / "stl" / "tolerance_coupon.stl")
    z_values = [triangle_centroid(triangle)[2] for triangle in triangles]
    low, high = min(z_values), max(z_values)
    palette = ((0.24, 0.56, 0.76), (0.25, 0.70, 0.56), (0.92, 0.67, 0.18), (0.82, 0.34, 0.22))
    def layer_colour(triangle):
        ratio = (triangle_centroid(triangle)[2] - low) / max(high - low, 1e-9)
        return palette[min(len(palette) - 1, int(ratio * len(palette)))]
    render_view(triangles, output / "tolerance_coupon_slicing_preview.png", (0.5, 0.5, 0.5), *iso,
                colour_for=layer_colour,
                annotation=label_annotation("SLICING ORIENTATION PREVIEW", "height bands only; generate and inspect machine-specific G-code"))


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
        render_view(
            triangles, output / f"{stem}_{name}.png", colour, direction, up,
            colour_for=assembly_colour if stem == "full_assembly_skeleton" else None,
        )


def main() -> None:
    render("tolerance_coupon", "modules", (0.95, 0.70, 0.15))
    render("input_classifier_proof", "modules", (0.28, 0.56, 0.72))
    render("classification_storage_proof", "modules", (0.36, 0.58, 0.42))
    render("stage1_cutter_stack", "modules", (0.72, 0.34, 0.18))
    render("stage1_shredder_proof", "modules", (0.78, 0.35, 0.22))
    render("stage2_shredder_proof", "modules", (0.64, 0.32, 0.24))
    render("stage3_granulator_proof", "modules", (0.50, 0.30, 0.24))
    render("vibratory_sorter_proof", "modules", (0.32, 0.52, 0.68))
    render("dryer_feeder_proof", "modules", (0.72, 0.48, 0.18))
    render("extruder_screw", "modules", (0.58, 0.58, 0.62))
    render("extruder_proof", "modules", (0.68, 0.28, 0.18))
    render("forming_line_proof", "modules", (0.26, 0.54, 0.66))
    render("diameter_gauge_optical_proof", "modules", (0.42, 0.64, 0.78))
    render("spooler_proof", "modules", (0.30, 0.48, 0.68))
    render("control_enclosure_proof", "modules", (0.46, 0.50, 0.56))
    render("full_assembly_skeleton", "assembly", (0.35, 0.62, 0.86))
    render_review_variants()


if __name__ == "__main__":
    main()
