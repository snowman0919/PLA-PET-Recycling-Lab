"""Missing, floating and under-engaged axial stops must fail CAD acceptance."""
import csv
import json
import sys
from pathlib import Path
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'cad/freecad/drive_v08')]
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.drive_v08.assembly import integrated_objects
from cad.freecad.compact.geometry import machine_fabrication_parts
from validation.shaft_retention_clearance import audit_traverse_retention

items, _ = integrated_objects(final_objects())
layout = json.loads((ROOT/'cad/parameters/baseline.json').read_text())['spooler']['traverse_layout']
result = audit_traverse_retention(items, layout)
assert result['status'] == 'TRAVERSE_AXIAL_STOP_GEOMETRY_PASS'
assert result['collar_quantity'] == 4 and result['guide_rod_length_mm'] == 196
assert not result['holding_force_verified'] and not result['fabrication_authorized']
by = {r['name']: r for r in items}


def reject(rows):
    try:
        audit_traverse_retention(rows, layout)
    except ValueError:
        return
    raise AssertionError('invalid rod retention accepted')


reject([r for r in items if r['name'] != 'TraverseCollarAFront'])
shifted = by['TraverseCollarAFront']['shape'].copy()
shifted.translate(App.Vector(0, -1, 0))
reject([dict(r, shape=shifted) if r['name'] == 'TraverseCollarAFront' else r for r in items])
short = Part.makeCylinder(4, 188, App.Vector(437, 454, 374), App.Vector(0, 1, 0))
reject([dict(r, shape=short) if r['name'] == 'TraverseRodA' else r for r in items])
obstacle = dict(name='BlockedCollarTool', shape=Part.makeBox(6,6,6,App.Vector(434,453,390)))
reject(items + [obstacle])
part = next(p for p in machine_fabrication_parts() if p['id'] == 'SP-TG-01')
assert part['qty'] == 2
assert abs(part['shape'].Volume - by['TraverseRodA']['shape'].Volume) < 1e-4
assert abs(part['shape'].BoundBox.ZLength - layout['rod_length_mm']) < 1e-6
with (ROOT/'bom/bom.csv').open(newline='') as handle:
    collars = [r for r in csv.DictReader(handle) if r['part_id'] == 'SP-SC-08']
assert len(collars) == 1 and float(collars[0]['quantity']) == 4
assert collars[0]['status'] == 'RECEIPT_HOLD'
assert layout['retention']['torque_nm'] is None
assert layout['retention']['holding_force_n'] is None
print('TRAVERSE_RETENTION_TEST_PASS cases=7 physical=NOT_RUN')
