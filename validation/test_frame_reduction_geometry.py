"""Actual CAD delta: retained components unchanged, tie seating and holes clear."""
from pathlib import Path
import json
import sys
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'cad/freecad/drive_v08')]
from cad.freecad.drive_v08.assembly import integrated_objects
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.drive_v08.frame_revision import apply_revision, steel_tie, CONTRACT

spec=json.loads(CONTRACT.read_text());before,_=integrated_objects(final_objects(), frame_revision=False)
after,_=apply_revision(before); old={r['name']:r for r in before};new={r['name']:r for r in after}
assert set(old)-set(new)==set(spec['remove_profiles'])
assert set(new)-set(old)=={spec['tie']['object']}
for name in set(old)&set(new):assert old[name]['shape'] is new[name]['shape']
s,section=steel_tie(spec['tie']); assert s.isValid() and len(s.Solids)==1
assert abs(s.BoundBox.XLength-470)<1e-8
for row in after:
    if row['name']==spec['tie']['object']:continue
    if s.BoundBox.intersect(row['shape'].BoundBox):assert s.common(row['shape']).Volume<1e-5
for x in spec['tie']['hole_x_mm']:
    for y in spec['tie']['hole_y_local_mm']:
        hole=Part.makeCylinder(2.7,3,App.Vector(x,y+265,20))
        washer=Part.makeCylinder(5,1,App.Vector(x,y+265,23))
        assert s.common(hole).Volume<1e-7 and s.common(washer).Volume<1e-7
for name in ('FrameY0_0','FrameY0_450'):assert s.distToShape(new[name]['shape'])[0]<1e-8
print('FRAME_REDUCTION_CAD_REGRESSION_PASS removed=2 retained_shapes_unchanged=True physical=NOT_RUN')
