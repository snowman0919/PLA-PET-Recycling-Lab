"""Reject unmanufacturable or unretained dancer axle stacks."""
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
from validation.shaft_retention_clearance import audit_dancer_retention

items, _ = integrated_objects(final_objects())
parts = machine_fabrication_parts()
layout = json.loads((ROOT/'cad/parameters/baseline.json').read_text())['spooler']['dancer_layout']
result = audit_dancer_retention(items, layout, parts)
assert result['status'] == 'DANCER_RETENTION_GEOMETRY_PASS'
assert result['manufacturing_lengths_mm'] == [38,52]
assert len(result['collars']) == 4 and result['washer_quantity'] == 5
assert not result['holding_force_verified'] and not result['fabrication_authorized']


def reject(rows, definitions=parts):
    try:
        audit_dancer_retention(rows, layout, definitions)
    except (ValueError, KeyError):
        return
    raise AssertionError('invalid dancer stack accepted')


def change(name, operation):
    rows = [dict(r, shape=r['shape'].copy()) for r in items]
    row = next(r for r in rows if r['name']==name)
    operation(row)
    return rows


for missing in ('DancerPivotCollarFront','DancerEndWasher1','DancerEndAxle'):
    reject([r for r in items if r['name']!=missing])
reject(change('DancerPivotAxle', lambda r:r.update(shape=Part.makeCylinder(
    4,28,App.Vector(188,430,115),App.Vector(0,1,0)))))
reject(change('DancerEndCollarRear', lambda r:r['shape'].translate(App.Vector(0,1,0))))
reject(change('DancerPivotWasher1', lambda r:r['shape'].translate(App.Vector(0,-0.4,0))))
reject(items, [dict(r,qty=2) if r['id']=='SP-AX-01' else r for r in parts])
reject(items, [dict(r,shape=Part.makeCylinder(4,28)) if r['id']=='SP-AX-02' else r for r in parts])
reject(items + [dict(name='DancerToolObstruction',shape=Part.makeBox(6,6,6,App.Vector(185,433,130)))])
reject(change('DancerPivotAxle', lambda r:r['shape'].translate(App.Vector(0,0,1))))
reject(items, [dict(r,shape=Part.makeCylinder(3,52)) if r['id']=='SP-AX-02' else r for r in parts])
output = ROOT/'.build/engineering-closure-20260914/dancer_retention.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(result,indent=2)+'\n')
print('DANCER_RETENTION_TEST_PASS cases=12 physical=NOT_RUN')
