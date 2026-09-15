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
    from plain_shaft_drawing import views
    for pid,length in [('SP-TG-01',196),('SP-AX-01',38),('SP-AX-02',52)]:
        shaft=Part.makeCylinder(4,length)
        rendered=views({'part_id':pid},shaft)
        tree=ET.fromstring('<svg>'+rendered+'</svg>')
        rectangle=tree.find('.//rect')
        assert rectangle is not None
        assert abs(float(rectangle.attrib['height'])/float(rectangle.attrib['width'])-8/length)<1e-9
        assert f'L {length}' in rendered and '7.991 - 8.000' in rendered
        assert 'marker-start=' in rendered and 'SILHOUETTE' in rendered
    for shape in [Part.makeCylinder(3,52),Part.makeBox(8,8,52),
                  Part.makeCylinder(4,52).cut(Part.makeCylinder(1,52))]:
        try: views({'part_id':'SP-AX-02'},shape)
        except ValueError: pass
        else: raise AssertionError('non-plain feature silently hidden')
    print("MANUFACTURING_PROJECTION_CIRCLE_AND_TITLE_CLEARANCE_PASS")


if __name__ == "__main__":
    main()
