"""Verify the actual GGM whole-machine STEP/native pair for the handoff."""
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[1]
base = ROOT/'exports/final/drive_ggm_v08'
manifest = json.loads((base/'manifest.json').read_text())
assert manifest['status'] == 'NEW_DRIVE_CLEARANCE_PASS'
assert manifest['machine_release'] == 'HOLD' and manifest['physical_validation'] == 'NOT_RUN'
for name, digest in manifest['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
for row in manifest['exports']:
    for key, hashkey in [('file','sha256'),('fcstd','fcstd_sha256')]:
        assert hashlib.sha256((base/row[key]).read_bytes()).hexdigest() == row[hashkey]
row = next(r for r in manifest['exports'] if r['file'] == 'GGM-FULL-ASM.step')
doc = App.openDocument(str(base/row['fcstd']))
objects = [o for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()]
names = {o.Name for o in objects}
assert {'GGM_Shredder','GGM_Extruder','GGM_SH_12T','GGM_SH_30T'} <= names
assert 'DriveMotorGMP60Reference' not in names
native = Part.makeCompound([o.Shape for o in objects]); step = Part.read(str(base/row['file']))
assert native.isValid() and step.isValid()
assert len(native.Solids) == len(step.Solids) == row['solids']
assert abs(native.Volume-step.Volume) <= step.Volume*1e-6
for actual, expected, hard in zip((step.BoundBox.XLength,step.BoundBox.YLength,step.BoundBox.ZLength), row['bbox_mm'], (500,750,1000)):
    assert abs(actual-expected) <= 1e-5 and actual <= hard
App.closeDocument(doc.Name)
print('GGM_NATIVE_STEP_HANDOFF_PASS envelope=470x729x930 hard_envelope=500x750x1000 physical=NOT_RUN')
