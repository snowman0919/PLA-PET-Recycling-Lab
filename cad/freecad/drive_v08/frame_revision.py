"""Small integrated-frame revision; base historical geometry stays immutable."""
import json
import math
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / 'cad/parameters/ggm_frame_revision.json'


def steel_tie(spec):
    length, w, h, t, r = (spec[k] for k in ('length_mm', 'width_mm', 'height_mm', 'thickness_mm', 'inside_bend_radius_mm'))
    outer = r + t
    def v(y, z): return App.Vector(0, y, z)
    edges = []
    def line(a, b): edges.append(Part.makeLine(v(*a), v(*b)))
    def arc(a, mid, b): edges.append(Part.Arc(v(*a), v(*mid), v(*b)).toShape())
    d = math.sqrt(0.5)
    line((0,h),(0,outer)); arc((0,outer),(outer-outer*d,outer-outer*d),(outer,0))
    line((outer,0),(w-outer,0)); arc((w-outer,0),(w-outer+outer*d,outer-outer*d),(w,outer))
    line((w,outer),(w,h)); line((w,h),(w-t,h)); line((w-t,h),(w-t,outer))
    arc((w-t,outer),(w-outer+r*d,outer-r*d),(w-outer,t))
    line((w-outer,t),(outer,t)); arc((outer,t),(outer-r*d,outer-r*d),(t,outer))
    line((t,outer),(t,h)); line((t,h),(0,h))
    section = Part.Face(Part.Wire(edges))
    shape = section.extrude(App.Vector(length,0,0))
    for x in spec['hole_x_mm']:
        for y in spec['hole_y_local_mm']:
            shape = shape.cut(Part.makeCylinder(spec['hole_diameter_mm']/2,t,App.Vector(x,y,0)))
    shape = shape.removeSplitter()
    shape.translate(App.Vector(*spec['origin_mm']))
    if not shape.isValid() or len(shape.Solids) != 1:
        raise ValueError('invalid formed-steel tie')
    return shape, section


def apply_revision(items):
    spec = json.loads(CONTRACT.read_text())
    names = {row['name'] for row in items}
    removed = set(spec['remove_profiles'])
    if not removed <= names or spec['tie']['object'] in names:
        raise ValueError('frame revision input mismatch or double application')
    out = [row for row in items if row['name'] not in removed]
    shape, _ = steel_tie(spec['tie'])
    out.append({'name': spec['tie']['object'], 'shape': shape, 'group': 'frame',
                'material': 'FR-TIE-01 S275JR formed channel 40x20x3 R3 L470',
                'classification': 'manufactured_or_stock'})
    return out, sorted(removed | {spec['tie']['object']})
