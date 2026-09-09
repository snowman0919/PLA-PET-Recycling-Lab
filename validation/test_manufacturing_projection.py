"""실제 FreeCAD 원형 모서리의 투상 근사와 제목 여백 회귀 검사.

실행: PYTHONPATH=/usr/lib/freecad/lib /usr/bin/python3 validation/test_manufacturing_projection.py
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import FreeCAD
import Part

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "release"))
from build_mechanical_release import projection


def main():
    circle = Part.Wire([Part.makeCircle(17)])
    svg = projection(circle, ("x", "y"), (25, 120, 335, 253))
    lines = ET.fromstring("<svg>" + svg + "</svg>")
    points = [tuple(map(float, p.split(','))) for p in lines[0].attrib["points"].split()]
    assert len(points) > 80, "coarse circle tessellation returned"
    assert min(y for x, y in points) >= 136, "projection overlaps view-title zone"
    radius_px = (253 - 32) / 2
    for a, b in zip(points, points[1:]):
        chord = math.dist(a, b)
        sagitta_mm = (radius_px - math.sqrt(max(0, radius_px**2 - chord**2/4))) * 17/radius_px
        assert sagitta_mm < .012, sagitta_mm
    print("MANUFACTURING_PROJECTION_CIRCLE_AND_TITLE_CLEARANCE_PASS")


if __name__ == "__main__":
    main()
