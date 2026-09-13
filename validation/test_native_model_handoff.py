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
    """Apply the exporter's one-ppm volume tolerance to each individual solid."""
    remaining = list(right)
    for solid in left:
        tolerance = max(1e-5, solid.Volume * 1e-6)
        for index, other in enumerate(remaining):
            if not same_location(solid, other) or abs(solid.Volume-other.Volume) > tolerance:
                continue
            common = solid.common(other).Volume
            if abs(solid.Volume-common) <= tolerance and abs(other.Volume-common) <= tolerance:
                remaining.pop(index)
                break
        else:
            candidates = [(other.Volume, solid.common(other).Volume, other.isValid()) for other in remaining if same_location(solid, other)]
            raise AssertionError(f'STEP/native individual solid mismatch volume={solid.Volume} bbox={solid.BoundBox} candidates={candidates}')
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
