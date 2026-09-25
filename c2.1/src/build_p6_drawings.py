"""Export the few C2.1 plate drawings needed for fabrication review.

These are nominal RFQ drawings.  They intentionally do not invent tolerances,
fits, material grades, heat treatment, or cutting approval.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import cadquery as cq
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(C21/"src"))
from build_cad import ring, support_plate


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dimension(ax, start, end, text, offset=(0, 0)):
    x0, z0 = start
    x1, z1 = end
    dx, dz = offset
    ax.annotate("", (x1+dx, z1+dz), (x0+dx, z0+dz),
                arrowprops={"arrowstyle": "<->", "lw": .8, "color": "#333"})
    ax.text((x0+x1)/2+dx, (z0+z1)/2+dz, text, ha="center", va="bottom", fontsize=8)


def support_page(pdf, title, bore_diameter):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    outline = [(-85, -85), (85, -85), (85, 40), (40, 85), (-85, 85)]
    ax.add_patch(Polygon(outline, closed=True, fill=False, lw=1.4))
    ax.add_patch(Circle((0, 0), bore_diameter/2, fill=False, lw=1.2))
    for x in (-77, 77):
        ax.add_patch(Circle((x, -77), 3.3, fill=False, lw=1.0))
        ax.plot([x-5, x+5], [-77, -77], lw=.4, color="#777")
        ax.plot([x, x], [-82, -72], lw=.4, color="#777")
    ax.add_patch(Circle((55, 82), 7, fill=False, ls="--", lw=.8))
    ax.plot([-92, 92], [0, 0], lw=.35, color="#999")
    ax.plot([0, 0], [-92, 92], lw=.35, color="#999")
    dimension(ax, (-85, -85), (85, -85), "170 NOM", (0, -13))
    dimension(ax, (-85, -85), (-85, 85), "170 NOM", (-15, 0))
    dimension(ax, (-bore_diameter/2, 0), (bore_diameter/2, 0), f"BORE DIA {bore_diameter:.1f} NOM")
    dimension(ax, (-77, -77), (77, -77), "154 NOM (2X DIA 6.6)", (0, 9))
    ax.text(88, 62, "45 x 45 corner relief", fontsize=8, ha="left")
    ax.text(88, 52, "T = 8 NOM", fontsize=8, ha="left")
    ax.text(88, 42, "Tie boss/web: CAD reference only", fontsize=8, ha="left")
    ax.set_title(title+"\nC2.1 S2 - RFQ / REVIEW ONLY - NOT RELEASED FOR CUTTING", fontsize=13)
    ax.text(-105, -123,
            "UNITS: mm | ALL DIMENSIONS NOMINAL | DATUM/FIT/GD&T/TOLERANCE: HOLD | "
            "MATERIAL/GRADE/HEAT TREATMENT/FINISH: HOLD\n"
            "Verify bearing/shaft MPN, measured fits, S1 clearance, fasteners and frame stack before fabrication.",
            fontsize=8, va="top")
    ax.set_aspect("equal")
    ax.set_xlim(-125, 170)
    ax.set_ylim(-135, 105)
    ax.axis("off")
    pdf.savefig(fig)
    plt.close(fig)


def ring_page(pdf):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.add_patch(Circle((0, 0), 88, fill=False, lw=1.4))
    ax.add_patch(Circle((0, 0), 63.5, fill=False, lw=1.2))
    ax.plot([-98, 98], [0, 0], lw=.35, color="#999")
    ax.plot([0, 0], [-98, 98], lw=.35, color="#999")
    dimension(ax, (-88, 0), (88, 0), "OD 176 NOM", (0, 8))
    dimension(ax, (-63.5, 0), (63.5, 0), "ID 127 NOM", (0, -13))
    ax.text(105, 30, "T = 6 NOM", fontsize=9)
    ax.text(105, 17, "Qty 2", fontsize=9)
    ax.text(105, 4, "Pin pattern/attachment: HOLD", fontsize=9)
    ax.set_title("FRONT / REAR FIXED RING PLATE\nC2.1 S2 - RFQ / REVIEW ONLY - NOT RELEASED FOR CUTTING", fontsize=13)
    ax.text(-105, -123,
            "UNITS: mm | ALL DIMENSIONS NOMINAL | DATUM/FIT/GD&T/TOLERANCE: HOLD | "
            "MATERIAL/GRADE/HEAT TREATMENT/FINISH: HOLD\n"
            "Tie rods: DIA 8 x 140 NOM, qty 4. Verify reaction load, pin retention, flatness and guard interface before fabrication.",
            fontsize=8, va="top")
    ax.set_aspect("equal")
    ax.set_xlim(-125, 190)
    ax.set_ylim(-135, 105)
    ax.axis("off")
    pdf.savefig(fig)
    plt.close(fig)


def main():
    out = C21/"drawings"
    out.mkdir(exist_ok=True)
    shapes = {
        "front_support_plate": support_plate(-60, 16.1),
        "rear_support_plate": support_plate(88, 21.1),
        "fixed_ring_plate": ring(88, 63.5, 6),
    }
    dxf = {}
    for name, shape in shapes.items():
        path = out/(name+".dxf")
        cq.exporters.exportDXF(cq.Workplane(obj=shape).faces(">Y"), str(path))
        if path.stat().st_size < 1000:
            raise RuntimeError(f"DXF export too small: {path}")
        dxf[name] = {"file": str(path.relative_to(REPO)), "sha256": sha256(path)}

    pdf_path = out/"PPR_C2_1_P6_nominal_plate_review.pdf"
    metadata = {"Title": "PPR C2.1 P6 nominal plate review",
                "Author": "PPR generated evidence",
                "Subject": "RFQ review only; fabrication release HOLD",
                "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
                "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc)}
    with PdfPages(pdf_path, metadata=metadata) as pdf:
        support_page(pdf, "FRONT INPUT SUPPORT PLATE", 32.2)
        support_page(pdf, "REAR OUTPUT SUPPORT PLATE", 42.2)
        ring_page(pdf)

    bounds = {name: [shape.BoundingBox().xlen, shape.BoundingBox().ylen,
                     shape.BoundingBox().zlen] for name, shape in shapes.items()}
    expected = {"front_support_plate": [170.0, 8.0, 174.0],
                "rear_support_plate": [170.0, 8.0, 174.0],
                "fixed_ring_plate": [176.0, 6.0, 176.0]}
    assert all(math.isclose(actual, target, abs_tol=1e-9)
               for name, target_bounds in expected.items()
               for actual, target in zip(bounds[name], target_bounds))
    result = {
        "revision": "C2.1-P6",
        "status": "NOMINAL_RFQ_REVIEW_ONLY_FABRICATION_RELEASE_HOLD",
        "dxf": dxf,
        "pdf": {"file": str(pdf_path.relative_to(REPO)), "pages": 3,
                "sha256": sha256(pdf_path)},
        "nominal_bounds_xyz_mm": bounds,
        "unresolved": ["datums", "fits", "GD&T", "tolerances", "material_grade",
                       "heat_treatment", "finish", "fastener_and_reaction_rating"],
        "fabrication": "HOLD",
    }
    result_path = C21/"results/p6_drawings.json"
    result_path.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
