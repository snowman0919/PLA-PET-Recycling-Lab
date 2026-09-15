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

import sys
sys.path.insert(0, str(ROOT / 'validation'))
from integrated_assembly_clearance import audit
native_rows = [{'name': o.SourceObjectId, 'shape': o.Shape,
                'classification': o.ComponentRole,
                'material': o.MaterialSpecification, 'group': o.Subsystem}
               for o in objects]
native_review = audit(native_rows)
assert native_review['unexpected_count'] == 0

def same_location(a, b):
    return (a.CenterOfMass - b.CenterOfMass).Length <= 1e-5

def solid_equivalence(left, right):
    """Compare actual missing/added solids, not subtraction of volume integrals."""
    remaining = list(right)
    for solid in left:
        tolerance = max(1e-5, solid.Volume * 1e-6)
        for index, other in enumerate(remaining):
            if not same_location(solid, other):
                continue
            missing, added = solid.cut(other), other.cut(solid)
            if not (missing.isNull() or missing.isValid()) or not (added.isNull() or added.isValid()):
                continue
            if missing.Volume <= tolerance and added.Volume <= tolerance:
                remaining.pop(index)
                break
        else:
            raise AssertionError(f'STEP/native geometry differs volume={solid.Volume} bbox={solid.BoundBox}')
    assert not remaining, 'STEP contains extra solids'

solid_equivalence(native.Solids, step.Solids)
probe = native.Solids[0].copy()
probe.translate(App.Vector(0.5, 0, 0))
try:
    solid_equivalence([probe], [native.Solids[0]])
except AssertionError:
    pass
else:
    raise AssertionError('same-volume displaced solid was accepted')
print('GGM_EXPORTED_SOLIDS_EQUIVALENT', len(step.Solids),
      'unexpected_overlaps', native_review['unexpected_count'],
      'reference_overlaps', len(native_review['reference_overlaps']))

App.closeDocument(doc.Name)
print('GGM_NATIVE_STEP_HANDOFF_PASS envelope=470x729x930 hard_envelope=500x750x1000 physical=NOT_RUN')

# Equal scalar measurements must not hide differently located internal features.
stock = Part.makeBox(20, 20, 20)
left = stock.copy()
right = stock.copy()
for x, y in ((5, 10), (15, 10)):
    left = left.cut(Part.makeCylinder(1, 20, App.Vector(x, y, 0)))
for x, y in ((10, 5), (10, 15)):
    right = right.cut(Part.makeCylinder(1, 20, App.Vector(x, y, 0)))
assert abs(left.Volume - right.Volume) < 1e-5
assert same_location(left.Solids[0], right.Solids[0])
try:
    solid_equivalence(left.Solids, right.Solids)
except AssertionError:
    pass
else:
    raise AssertionError('different internal holes with equal volume/centroid were accepted')
print('GGM_INTERNAL_FEATURE_DIFFERENCE_REJECTION_PASS')
