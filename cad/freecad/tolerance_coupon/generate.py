"""Generate a two-piece FDM clearance and hole calibration coupon."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

COMMON = Path(__file__).resolve().parents[1] / "common"
sys.path.insert(0, str(COMMON))
from project import ROOT, add_feature, bounding_box_report, export_document, load_parameters  # noqa: E402


def build():
    p = load_parameters()["tolerance_coupon"]
    gaps = p["gaps_mm"]
    nominal = p["nominal_tab_mm"]
    holes = p["hole_diameters_mm"]
    doc = App.newDocument("ToleranceCoupon")

    base = Part.makeBox(100, 70, 5)
    for i, gap in enumerate(gaps):
        slot_w = nominal + gap
        x = 5 + i * 18
        slot = Part.makeBox(slot_w, 22, 7, App.Vector(x, 5, -1))
        base = base.cut(slot)
    for i, diameter in enumerate(holes):
        x = 10 + i * 18
        hole = Part.makeCylinder(diameter / 2, 7, App.Vector(x, 52, -1))
        base = base.cut(hole)
    base_obj = add_feature(doc, "CouponBase", "CAL-COUPON-BASE", base, "CAL-COUPON-BASE", "PLA test material")

    # Keep a 5 mm print-plate gap from the base, whose maximum Y is 70 mm.
    comb = Part.makeBox(100, 16, 5, App.Vector(0, 93, 0))
    for i, _gap in enumerate(gaps):
        x = 5 + i * 18
        tab = Part.makeBox(nominal, 18, 5, App.Vector(x, 75, 0))
        comb = comb.fuse(tab)
    comb_obj = add_feature(doc, "CouponComb", "CAL-COUPON-COMB", comb, "CAL-COUPON-COMB", "PLA test material")

    outputs = export_document(doc, "tolerance_coupon", [base_obj, comb_obj])
    report = {
        "revision": load_parameters()["revision"],
        "base": bounding_box_report(base_obj),
        "comb": bounding_box_report(comb_obj),
        "gap_series_mm": gaps,
        "hole_diameters_mm": holes,
        "outputs": outputs,
    }
    report_path = ROOT / "validation" / "fabrication_review" / "tolerance_coupon.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
