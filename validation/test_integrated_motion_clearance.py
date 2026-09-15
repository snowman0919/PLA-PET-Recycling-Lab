"""Regression tests for the actual integrated kinematic layout."""
import sys
from pathlib import Path
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'cad/freecad/drive_v08')]
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.drive_v08.assembly import integrated_objects
from validation.integrated_motion_clearance import audit, contact_area
base = Part.makeBox(20, 20, 20)
seated = Part.makeBox(20, 20, 20, App.Vector(0, 0, 20))
assert abs(contact_area(base, seated) - 400) < 1e-6
for dz in (-0.1, 0.1):
    displaced = seated.copy(); displaced.translate(App.Vector(0, 0, dz))
    assert contact_area(base, displaced) == 0
items,_=integrated_objects(final_objects())
result=audit(items)
assert result['status']=='GGM_NOMINAL_MOTION_CLEARANCE_PASS'
assert result['traverse_stroke_mm']==80 and result['traverse_sample_count']==81
assert result['fabrication_authorized'] is False

def changed(name, action):
    rows=[dict(r,shape=r['shape'].copy()) for r in items]
    row=next(r for r in rows if r['name']==name)
    action(row)
    return rows

def reject(rows):
    try: audit(rows)
    except ValueError: return
    raise AssertionError('invalid geometry accepted')

reject(changed('TraverseRodA',lambda r:r['shape'].rotate(App.Vector(),App.Vector(0,0,1),90)))
reject(changed('FrameTraversePostLeft',lambda r:r['shape'].translate(App.Vector(8,0,0))))
reject(changed('PPR-C10_TraverseCarriage',lambda r:r.update(shape=Part.makeBox(55,90,24,App.Vector(397,476.5,362)))))
reject(changed('PPR-C01_SlidingLid',lambda r:r.update(shape=Part.makeBox(195,195,2,App.Vector(30,290,900)))))
reject(items+[{'name':'BlockedLidRemoval','shape':Part.makeBox(5,5,5,App.Vector(-30,340,903))}])
reject(items+[items[0]])
print('GGM_MOTION_REGRESSION_PASS assembly_cases=7 contact_cases=3 physical=NOT_RUN')
