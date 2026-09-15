"""Dancer assembly and machining definitions share the same nominal dimensions."""
import json
from pathlib import Path
import FreeCAD as App
import Part
from shaft_retention import collar_shape

ROOT = Path(__file__).resolve().parents[3]
BASE = json.loads((ROOT / 'cad/parameters/baseline.json').read_text())
SPEC = BASE['spooler']['dancer_layout']
COLLAR = BASE['spooler']['traverse_layout']['retention']


def washer_shape():
    s = SPEC['washer']
    return Part.makeCylinder(s['outer_diameter_mm']/2, s['thickness_mm']).cut(
        Part.makeCylinder(s['bore_mm']/2, s['thickness_mm'])).removeSplitter()


def axle_parts():
    parts = []
    for key, label in (('pivot_axle', 'pivot'), ('end_axle', 'roller')):
        s = SPEC[key]
        parts.append(dict(id=s['part_id'], name='Dancer '+label+' axle', qty=1,
            shape=Part.makeCylinder(SPEC['shaft_diameter_mm']/2, s['length_mm']),
            material='8 h6 stainless ground shaft', process='cut + face + deburr',
            critical=f"Diameter 7.991-8.000; length {s['length_mm']:g} +/-0.10; ends C0.2; shaft straightness <=0.05; retain with two SP-SC-08 collars; endplay 0.10-0.30 after adjustment; collar torque and axial slip proof HOLD"))
    return parts


def assembly_rows():
    rows = []
    def add(name, shape, material, kind='manufactured_or_stock'):
        rows.append(dict(name=name, shape=shape, group='spooler', material=material,
                         classification=kind))
    for key, label in (('pivot_axle', 'Pivot'), ('end_axle', 'End')):
        s = SPEC[key]
        x, y, z = s['origin_mm']
        add('Dancer'+label+'Axle', Part.makeCylinder(4, s['length_mm'],
            App.Vector(x,y,z), App.Vector(0,1,0)), s['part_id']+' 8 h6 stainless')
        for end, start in zip(('Front', 'Rear'), s['collar_start_y_mm']):
            add('Dancer'+label+'Collar'+end, collar_shape(x,start,z,COLLAR),
                'SP-SC-08 GN705-8-E reference; received torque/holding force required',
                'purchased_reference_lod')
        for index, start in enumerate(s['washer_start_y_mm']):
            shape = washer_shape()
            shape.rotate(App.Vector(), App.Vector(1,0,0), -90)
            shape.translate(App.Vector(x,start,z))
            add('Dancer'+label+'Washer'+str(index), shape, 'SP-AW-08 304SS shim')
    return rows


def moving_names():
    return {'DancerArm','DancerEndRoller'} | {
        row['name'] for row in assembly_rows() if row['name'].startswith('DancerEnd')}
