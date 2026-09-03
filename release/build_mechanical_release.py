#!/usr/bin/env python3
"""Build and verify the v0.8 mechanical manufacturing package.

Run with FreeCAD's Python runtime:
  nix develop --command FreeCADCmd -c 'exec(open("release/build_mechanical_release.py").read())'
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import Part

ROOT = Path(__file__).resolve().parents[1]
REVISION = "final-design-fabrication-closure-v0.8"
MFG = ROOT / "exports/final/manufacturing"
STEP_OUT = ROOT / "exports/final/step"
DRAWINGS = ROOT / "docs/drawings/manufacturing"
FAMILIES = (
    "cutter", "shafts", "phase_gears", "screw_barrel", "die",
    "bearing_plates", "feeder", "hot_zone", "guards_panels", "RFQ",
)
FIELDS = (
    "part_id", "revision", "quantity", "material", "process",
    "critical_tolerance", "datum_scheme", "inspection", "status",
    "source_step", "source_dxf", "step_file", "dxf_file", "drawing_pdf",
    "solid_count", "bbox_mm", "volume_mm3", "sha256_step", "sha256_dxf",
    "sha256_pdf",
    "release_gate",
)

MATERIAL_FREEZE = {
    "CUT-01": "6 mm AISI D2 tool steel (JIS SKD11 equivalent)",
    "CUT-02": "S45C normalized steel",
    "CUT-03": "12 mm S275JR steel",
    "CUT-06": "S45C normalized steel",
    "FD-BIN-01": "1 mm 304 stainless sheet",
    "FD-MET-02": "POM-C",
    "EX-THR-01": "12 mm S45C normalized steel",
    "FM-GR-01": "POM-C",
    "FM-RL-01": "6061-T6 hub + replaceable Shore A 50–70 silicone sleeve",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def note_value(path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^- {re.escape(label)}:\s*`?(.+?)`?\s*$", text, re.MULTILINE)
    return match.group(1).strip("`") if match else ""


def family(part_id: str) -> str:
    if part_id == "TH-BH-01":
        return "hot_zone"
    if part_id in {"TH-PTC-01", "TH-PTC-02"}:
        return "feeder"
    if part_id in {"CUT-01", "CUT-02", "CUT-04"}:
        return "cutter"
    if part_id in {"CUT-05", "FD-MET-03", "FM-AX-01", "FM-GA-01", "SP-AX-01", "SP-SH-01"}:
        return "shafts"
    if part_id in {"CUT-06", "DRV-02", "DRV-03", "DRV-F01A", "DRV-F01B", "DRV-F01P"}:
        return "phase_gears"
    if part_id.startswith(("EX-SCR", "EX-BAR", "EX-CPN")):
        return "screw_barrel"
    if part_id.startswith("EX-DIE"):
        return "die"
    if part_id in {"CUT-03", "CUT-08", "EX-THR-01", "FM-PL-01", "SP-BP-01"}:
        return "bearing_plates"
    if part_id.startswith(("IN-", "FD-")):
        return "feeder"
    return "guards_panels"


def datum_for(part_family: str) -> str:
    return {
        "cutter": "A=shaft bore axis; B=ground stack face; C=keyway centre plane",
        "shafts": "A=common journal axis; B=drive-end shoulder/face; C=keyway or retaining feature plane",
        "phase_gears": "A=shaft bore axis; B=stack face; C=key/dowel angular datum",
        "screw_barrel": "A=common journal/bore axis; B=drive/feed datum face; C=feed-port angular plane",
        "die": "A=barrel interface face; B=melt-channel axis; C=fastener-pattern centre plane",
        "bearing_plates": "A=frame mounting face; B=primary bearing axis; C=secondary bearing/fastener axis",
        "feeder": "A=material-flow axis; B=mounting face; C=drive/sensor centre plane",
        "guards_panels": "A=frame mounting plane; B=primary edge; C=mounting-hole centreline",
        "hot_zone": "A=profile mounting plane; B=barrel axis; C=rear axial datum",
    }[part_family]


def inspection_for(part_id: str, part_family: str) -> str:
    common = "CMM/caliper against STEP and drawing; deburr and visual crack/warp inspection"
    extra = {
        "cutter": "; inspect flatness/parallelism and stack gap with metal shims",
        "shafts": "; micrometer bearing seats; dial-indicator TIR/runout between centres",
        "phase_gears": "; CMM centre distance; blue-check backlash/contact; verify keyed torque path",
        "screw_barrel": "; certified material/heat-treatment report; three-station bore/OD and TIR report",
        "die": "; pin-gauge channels/orifice; face flatness; shielded hydro/hot-polymer containment test",
        "bearing_plates": "; bore gauge; matched-pair centre distance and axis parallelism",
        "feeder": "; dry assembly rotation and cleanout/dead-pocket inspection",
        "guards_panels": "; fit-up, PE bond where metal, reach/access and interlock actuation inspection",
        "hot_zone": "; barrel-axis alignment; sliding travel and cold/hot clearance inspection",
    }[part_family]
    if part_id == "CUT-01":
        extra += "; hardness and post-treatment grinding report required"
    return common + extra


def source_parts() -> list[dict[str, str]]:
    parts: dict[str, dict[str, str]] = {}

    def add(row: dict[str, str], base: Path, quantity: str, release: str) -> None:
        part_id = row["part_id"]
        if part_id in {"CUT-07", "DRV-A42"}:  # superseded duplicate and unselected reference
            return
        note = base / "drawing_notes.md"
        critical = note_value(note, "controlling requirements") or note_value(note, "중요공차/검사")
        part_family = family(part_id)
        source_step = base / f"{part_id}.step"
        source_dxf = base / f"{part_id}.dxf"
        if not critical:
            critical = "HOLD: authoritative critical tolerance absent; supplier/user markup required before RFQ"
        if part_id == "EX-SCR-01":
            critical += "; SCM440 QT 28–32 HRC; gas nitride 0.30–0.50 mm, surface 900–1100 HV; flight OD TIR ≤0.05/256; OD Ra≤0.8 µm"
        elif part_id == "EX-BAR-01":
            critical += "; SCM440 QT 28–32 HRC; gas nitride 0.30–0.50 mm, surface ≥900 HV; final hone bore Ra 0.4–0.8 µm; three-station bore report"
        critical = critical.replace("; full part HOLD", "").replace("full part HOLD; ", "")
        status = "HOLD" if critical.startswith("HOLD: authoritative") else "PASS"
        parts[part_id] = {
            "part_id": part_id,
            "name": row.get("name", part_id),
            "revision": REVISION,
            "quantity": quantity,
            "material": MATERIAL_FREEZE.get(part_id, row.get("material", "")),
            "process": row.get("process", ""),
            "critical_tolerance": critical,
            "datum_scheme": datum_for(part_family) + "; verify datum marking on supplier inspection report",
            "inspection": inspection_for(part_id, part_family),
            "status": status,
            "release_gate": release,
            "source_step": str(source_step.relative_to(ROOT)),
            "source_dxf": str(source_dxf.relative_to(ROOT)),
            "family": part_family,
        }

    for row in rows("exports/cnc/shredder_manifest.csv"):
        add(row, ROOT / "exports/cnc" / row["part_id"], row["quantity"], row["release_state"])
    for row in rows("exports/cnc/extruder/rfq_manifest.csv"):
        add(row, ROOT / "exports/cnc/extruder/parts" / row["part_id"], row["qty"], row["release"])
    for row in rows("exports/fabrication/machine_manifest.csv"):
        add(row, ROOT / "exports/fabrication/parts" / row["part_id"], row["quantity"], row["release_state"])
    for row in rows("exports/drive_interface/manifest.csv"):
        add(row, ROOT / "exports/drive_interface/parts" / row["part_id"], row["quantity"], row["release_state"])
    for row in rows("exports/thermal/manifest.csv"):
        if row["part_id"] not in {"TH-BH-01", "TH-PTC-01", "TH-PTC-02"}:
            continue
        base = ROOT / "exports/thermal/parts" / row["part_id"]
        add({**row, "process": note_value(base / "drawing_notes.md", "process")}, base, row["quantity"], row["release_state"])
    return [parts[key] for key in sorted(parts)]


def projection(shape: Part.Shape, axes: tuple[str, str], box: tuple[int, int, int, int]) -> str:
    x0, y0, width, height = box
    paths, points = [], []
    for edge in shape.Edges:
        row = [(getattr(p, axes[0]), getattr(p, axes[1])) for p in edge.discretize(Deflection=0.7)]
        if len(row) > 1:
            paths.append(row); points.extend(row)
    if not points:
        return ""
    lo_a, hi_a = min(x for x, _ in points), max(x for x, _ in points)
    lo_b, hi_b = min(y for _, y in points), max(y for _, y in points)
    scale = min((width - 32) / max(hi_a - lo_a, 1e-6), (height - 32) / max(hi_b - lo_b, 1e-6))
    def mapped(point: tuple[float, float]) -> tuple[float, float]:
        return x0 + 16 + (point[0] - lo_a) * scale, y0 + height - 16 - (point[1] - lo_b) * scale
    return "\n".join(
        f'<polyline points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in map(mapped, row))}" fill="none" stroke="#263238" stroke-width="0.8"/>'
        for row in paths
    )


def drawing_svg(part: dict[str, str], shape: Part.Shape, path: Path, commit: str) -> None:
    box = shape.BoundBox
    detail = [
        f"Drawing MFG-{part['part_id']} | Part {part['part_id']} — {part['name']} | Qty {part['quantity']}",
        f"Rev {REVISION} | Units mm | Scale NTS, dimensions govern | Third-angle projection | source commit {commit}",
        f"Material: {part['material']} | Process/finish: {part['process']}",
        f"Overall: X {box.XLength:.3f} × Y {box.YLength:.3f} × Z {box.ZLength:.3f} mm | general tolerance ISO 2768-m unless noted",
        f"Critical: {part['critical_tolerance']}",
        f"GD&T/datums: {part['datum_scheme']}",
        f"Inspection: {part['inspection']}",
        "Edges: remove burrs; break unspecified sharp edges C0.3–0.5. No unapproved material/tolerance substitution.",
        f"Release: {part['status']} — physical validation NOT_RUN; procurement and machining USER_APPROVAL_REQUIRED.",
    ]
    lines: list[str] = []
    for item in detail:
        lines.extend(textwrap.wrap(item, width=145, break_long_words=False, break_on_hyphens=False) or [""])
    if len(lines) > 17:
        raise RuntimeError(f"{part['part_id']}: drawing note overflow ({len(lines)} lines)")
    text_rows = "\n".join(
        f'<text x="28" y="{418 + i * 21}" font-size="11">{html.escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    views = (
        projection(shape, ("x", "y"), (25, 88, 335, 285)),
        projection(shape, ("x", "z"), (394, 88, 335, 285)),
        projection(shape, ("y", "z"), (763, 88, 335, 285)),
    )
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">
<rect width="1123" height="794" fill="white"/><rect x="12" y="12" width="1099" height="770" fill="none" stroke="#111" stroke-width="2"/>
<g font-family="Noto Sans CJK KR,sans-serif" fill="#111"><text x="28" y="48" font-size="24" font-weight="bold">MFG-{html.escape(part['part_id'])} · v0.8 MANUFACTURING DRAWING</text>
<text x="35" y="106" font-size="14">TOP X-Y</text>{views[0]}<text x="404" y="106" font-size="14">FRONT X-Z</text>{views[1]}<text x="773" y="106" font-size="14">SIDE Y-Z</text>{views[2]}
<line x1="20" y1="398" x2="1103" y2="398" stroke="#111"/>{text_rows}</g></svg>\n''', encoding="utf-8")


def compile_pdf(svg: Path, pdf: Path) -> None:
    typ = svg.with_suffix(".typ")
    typ.write_text(f'#set page(width: 297mm, height: 210mm, margin: 0mm)\n#image("{svg.name}", width: 297mm, height: 210mm)\n', encoding="utf-8")
    try:
        subprocess.run(["typst", "compile", "--root", str(ROOT), str(typ), str(pdf)], cwd=ROOT, check=True)
    finally:
        typ.unlink(missing_ok=True)


def copy_part(part: dict[str, str], commit: str) -> dict[str, str]:
    family_dir = MFG / part["family"]
    family_dir.mkdir(parents=True, exist_ok=True)
    source_step, source_dxf = ROOT / part["source_step"], ROOT / part["source_dxf"]
    if not source_step.is_file() or not source_dxf.is_file():
        raise RuntimeError(f"{part['part_id']}: authoritative STEP/DXF missing")
    step, dxf, pdf = family_dir / f"{part['part_id']}.step", family_dir / f"{part['part_id']}.dxf", family_dir / f"{part['part_id']}.pdf"
    if source_step.resolve() != step.resolve():
        shutil.copyfile(source_step, step)
    if source_dxf.resolve() != dxf.resolve():
        shutil.copyfile(source_dxf, dxf)
    shape = Part.read(str(step))
    if not shape.isValid() or not shape.Solids:
        raise RuntimeError(f"{part['part_id']}: STEP clean reimport has no valid solid")
    svg = DRAWINGS / f"{part['part_id']}.svg"
    drawing_svg(part, shape, svg, commit); compile_pdf(svg, pdf)
    box = shape.BoundBox
    return {
        **{key: part[key] for key in FIELDS[:9]},
        "source_step": part["source_step"], "source_dxf": part["source_dxf"],
        "step_file": step.name, "dxf_file": dxf.name, "drawing_pdf": pdf.name,
        "solid_count": str(len(shape.Solids)),
        "bbox_mm": f"{box.XLength:.6f}x{box.YLength:.6f}x{box.ZLength:.6f}",
        "volume_mm3": f"{shape.Volume:.6f}",
        "sha256_step": sha256(step), "sha256_dxf": sha256(dxf), "sha256_pdf": sha256(pdf),
        "release_gate": part["release_gate"],
    }


def hot_zone_parts(commit: str) -> list[dict[str, str]]:
    metadata = {
        "ExtruderSupportRailRear": ("1", "2020 aluminum profile L390", "saw cut, face and deburr", "length 390.0 ±0.5 mm; end squareness 0.3; front/rear support height difference ≤0.20 mm; axis parallelism ≤0.20/390"),
        "ExtruderRearFixedDatum": ("1", "8 mm S275 steel", "laser/waterjet rough + bore/face finish", "barrel bore Ø34.10 +0.05/0; 2×Ø6.6 rail holes; datum face flatness 0.10; bore axis perpendicularity 0.10/54; hole position ±0.10"),
        "ExtruderFrontSlidingGuide": ("1", "8 mm S275 steel", "laser/waterjet rough + bore/face finish", "guide bore Ø34.60 +0.10/0; 2×Ø6.6 rail holes; datum face flatness 0.10; bore position ±0.10; cold axial travel ≥1.30 mm; no axial clamp"),
        "ExtruderFixedCollar": ("1", "S45C steel", "turn, split, black oxide with bore masked", "OD Ø50; L12.00 ±0.05; bore Ø34.10 +0.03/0; datum face runout 0.05 to bore axis; bore Ra≤1.6 µm; blue-fit contact ≥70%"),
    }
    result = []
    for part_id, (qty, material, process, critical) in metadata.items():
        source_step = STEP_OUT / "cnc_parts" / f"{part_id}.step"
        source_dxf = MFG / "hot_zone" / f"{part_id}.dxf"
        part = {
            "part_id": part_id, "name": part_id, "revision": REVISION, "quantity": qty,
            "material": material, "process": process, "critical_tolerance": critical,
            "datum_scheme": datum_for("hot_zone") + "; verify datum marking on supplier inspection report",
            "inspection": inspection_for(part_id, "hot_zone"), "status": "PASS",
            "release_gate": "USER_APPROVAL_AND_PHYSICAL_INSPECTION_REQUIRED",
            "source_step": str(source_step.relative_to(ROOT)), "source_dxf": str(source_dxf.relative_to(ROOT)),
            "family": "hot_zone",
        }
        result.append(copy_part(part, commit))
    return result


def write_manifest(path: Path, data: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(data)


def populate_step_categories(data: list[dict[str, str]], commit: str) -> None:
    for name in ("printed_parts", "shafts", "sheet_parts", "purchased_part_envelopes"):
        target = STEP_OUT / name
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
    step_rows: dict[str, list[list[str]]] = {name: [] for name in ("printed_parts", "shafts", "sheet_parts", "purchased_part_envelopes")}
    def step_row(part_id: str, source: Path, target: Path, status: str, release_gate: str) -> list[str]:
        shape = Part.read(str(target)); box = shape.BoundBox
        if not shape.isValid() or not shape.Solids:
            raise RuntimeError(f"{part_id}: STEP category reimport failed")
        return [part_id, REVISION, str(source.relative_to(ROOT)), commit, target.name, "AP214_FALLBACK_FREECAD", "mm", "1", str(len(shape.Solids)), f"{box.XLength:.6f}x{box.YLength:.6f}x{box.ZLength:.6f}", f"{shape.Volume:.6f}", "", sha256(target), status, release_gate]
    for folder in sorted((ROOT / "exports/print").glob("PPR-C[0-9][0-9]")):
        source = folder / f"{folder.name}.step"; target = STEP_OUT / "printed_parts" / source.name
        shutil.copyfile(source, target); step_rows["printed_parts"].append(step_row(folder.name, source, target, "PASS", "PHYSICAL_FIT_NOT_RUN"))
    for row in data:
        category = "shafts" if row["part_id"] in {"CUT-05", "FD-MET-03", "FM-AX-01", "FM-GA-01", "SP-AX-01", "SP-SH-01"} else "sheet_parts"
        if category == "sheet_parts" and row["part_id"].startswith(("EX-SCR", "EX-BAR", "EX-CPN", "EX-DIE", "DRV-F", "TH-BH")):
            continue
        source_family = "hot_zone" if row["part_id"].startswith("Extruder") else family(row["part_id"])
        source = MFG / source_family / row["step_file"]
        target = STEP_OUT / category / source.name
        shutil.copyfile(source, target); step_rows[category].append(step_row(row["part_id"], source, target, row["status"], row["release_gate"]))
    for row in rows("exports/thermal/manifest.csv"):
        part_id = row["part_id"]
        source = ROOT / "exports/thermal/parts" / part_id / f"{part_id}.step"
        target = STEP_OUT / "purchased_part_envelopes" / source.name
        shutil.copyfile(source, target); step_rows["purchased_part_envelopes"].append(step_row(part_id, source, target, "PASS", "USER_RECEIPT_INSPECTION_REQUIRED"))
    for category, values in step_rows.items():
        with (STEP_OUT / category / "manifest.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n"); writer.writerow(["part_id", "revision", "source_object", "source_commit", "file", "format", "units", "body_count", "solid_count", "bbox_mm", "volume_mm3", "mass_g", "sha256", "status", "release_gate"]); writer.writerows(values)
    root_manifest = STEP_OUT / "step_manifest.csv"
    preserved = [row for row in rows(str(root_manifest.relative_to(ROOT))) if row["file"].startswith(("assembly/", "cnc_parts/"))]
    combined = preserved[:]
    for category in step_rows:
        for row in rows(str((STEP_OUT / category / "manifest.csv").relative_to(ROOT))):
            combined.append({**row, "file": f"{category}/{row['file']}"})
    root_fields = ["part_id", "revision", "source_object", "source_commit", "file", "format", "units", "body_count", "solid_count", "bbox_mm", "volume_mm3", "mass_g", "sha256", "status", "release_gate"]
    with root_manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=root_fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(combined)


def verify() -> dict[str, object]:
    checked, totals = set(), {}
    for family_name in FAMILIES:
        folder, manifest = MFG / family_name, MFG / family_name / "manifest.csv"
        if not manifest.is_file():
            raise RuntimeError(f"missing family manifest: {family_name}")
        data = rows(str(manifest.relative_to(ROOT)))
        missing = set(FIELDS[:9]) - set(data[0] if data else {})
        if missing or not data:
            raise RuntimeError(f"{family_name}: empty/bad manifest {sorted(missing)}")
        if any(row["status"] not in {"PASS", "HOLD"} for row in data):
            raise RuntimeError(f"{family_name}: invalid status")
        for row in data:
            for field in ("step_file", "dxf_file", "drawing_pdf"):
                path = folder / row[field]
                if not path.is_file():
                    raise RuntimeError(f"{family_name}/{row['part_id']}: missing {field}")
            step = folder / row["step_file"]
            shape = Part.read(str(step))
            if not shape.isValid() or len(shape.Solids) != int(row["solid_count"]):
                raise RuntimeError(f"{family_name}/{row['part_id']}: STEP reimport mismatch")
            if sha256(step) != row["sha256_step"] or sha256(folder / row["dxf_file"]) != row["sha256_dxf"] or sha256(folder / row["drawing_pdf"]) != row["sha256_pdf"]:
                raise RuntimeError(f"{family_name}/{row['part_id']}: hash mismatch")
            if (folder / row["drawing_pdf"]).read_bytes()[:4] != b"%PDF":
                raise RuntimeError(f"{family_name}/{row['part_id']}: invalid PDF")
            checked.add(row["part_id"])
        totals[family_name] = len(data)
    for category in ("printed_parts", "shafts", "sheet_parts", "purchased_part_envelopes"):
        manifest = STEP_OUT / category / "manifest.csv"
        data = rows(str(manifest.relative_to(ROOT)))
        if not data:
            raise RuntimeError(f"empty STEP category: {category}")
        for row in data:
            shape = Part.read(str(manifest.parent / row["file"]))
            if not shape.isValid() or not shape.Solids:
                raise RuntimeError(f"{category}/{row['part_id']}: STEP clean reimport failed")
        totals[f"step/{category}"] = len(data)
    report = {
        "revision": REVISION, "status": "PASS" if all(
            row["status"] == "PASS" for name in FAMILIES
            for row in rows(str((MFG / name / "manifest.csv").relative_to(ROOT)))
        ) else "HOLD",
        "digital_artifact_check": "PASS", "physical_validation_state": "NOT_RUN",
        "procurement_gate": "USER_APPROVAL_REQUIRED", "manufacturing_part_ids": sorted(checked),
        "counts": totals,
        "notes": [
            "CUT-07 is superseded by identical active DRV-01; DRV-A42 is an unselected reference and excluded.",
            "Manifest status covers digital geometry/drawing completeness; release_gate preserves user approval, donor measurement, coupon and physical gates.",
            "STEP validation is clean reimport/solid/bounds evidence, not physical inspection or safety certification.",
        ],
    }
    (MFG / "mechanical_release_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    if not shutil.which("typst"):
        raise SystemExit("run inside `nix develop`: typst missing")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    DRAWINGS.mkdir(parents=True, exist_ok=True)
    for path in DRAWINGS.glob("*"):
        if path.is_file():
            path.unlink()
    for name in FAMILIES:
        if name == "hot_zone":
            for suffix in (".step", ".pdf"):
                for path in (MFG / name).glob(f"*{suffix}"):
                    if path.name != "hot_zone_mount_drawings.pdf":
                        path.unlink()
            (MFG / name / "manifest.csv").unlink(missing_ok=True)
        else:
            shutil.rmtree(MFG / name, ignore_errors=True)
            (MFG / name).mkdir(parents=True)
    source = source_parts()
    built = [copy_part(part, commit) for part in source]
    built.extend(hot_zone_parts(commit))
    for family_name in FAMILIES[:-1]:
        write_manifest(MFG / family_name / "manifest.csv", [
            row for row in built
            if ("hot_zone" if row["part_id"].startswith("Extruder") else family(row["part_id"])) == family_name
        ])
    rfq = MFG / "RFQ"
    rfq_rows = []
    for row in built:
        source_dir = MFG / ("hot_zone" if row["part_id"].startswith("Extruder") else family(row["part_id"]))
        for field in ("step_file", "dxf_file", "drawing_pdf"):
            shutil.copyfile(source_dir / row[field], rfq / row[field])
        rfq_rows.append(row)
    write_manifest(rfq / "manifest.csv", rfq_rows)
    populate_step_categories(built, commit)
    report = verify()
    print(f"V08_MECHANICAL_RELEASE_OK parts={len(built)} families={len(FAMILIES)} counts={json.dumps(report['counts'], sort_keys=True)}")


if __name__ == "__main__" or __name__ == "builtins":
    main()
