"""Compare immutable published CAD with the current native handoff geometry."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from validation.integrated_assembly_clearance import REPAIRED_PAIRS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(name):
    return name.replace('-', '_').replace('.', '_')


def objects(doc):
    out = {}
    for obj in doc.Objects:
        if not hasattr(obj, 'Shape') or obj.Shape.isNull():
            continue
        key = identity(getattr(obj, 'SourceObjectId', obj.Name))
        if key in out:
            raise ValueError('duplicate normalized object identity')
        if not obj.Shape.isValid() or not obj.Shape.Solids:
            raise ValueError('invalid CAD solid: ' + key)
        out[key] = obj.Shape
    return out


def main():
    contract = ROOT/'cad/parameters/ggm_frame_revision.json'
    reference = json.loads(contract.read_text())['reference_commit']
    rel = 'exports/final/drive_ggm_v08/GGM-FULL-ASM.FCStd'
    current = ROOT/rel
    manifest = ROOT/'exports/final/drive_ggm_v08/manifest.json'
    data = json.loads(manifest.read_text())
    whole = next(r for r in data['exports'] if r['file'] == 'GGM-FULL-ASM.step')
    if sha(current) != whole['fcstd_sha256']:
        raise ValueError('current native model differs from its manifest')
    historical = subprocess.check_output(['git', 'show', reference+':'+rel], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='published-compare-', dir=ROOT/'.build') as tmp:
        old_path = Path(tmp)/'published.FCStd'
        old_path.write_bytes(historical)
        previous = App.openDocument(str(old_path))
        revised = App.openDocument(str(current))
        try:
            old, new = objects(previous), objects(revised)
            rows = []
            for left, right in REPAIRED_PAIRS:
                a, b = identity(left), identity(right)
                before = old[a].common(old[b]).Volume
                after = new[a].common(new[b]).Volume
                if after > 0.01:
                    raise ValueError('repaired exported interface still intersects: '+left+'/'+right)
                rows.append({'left': left, 'right': right,
                             'published_overlap_mm3': before, 'revised_overlap_mm3': after})
            removed = sorted(set(old)-set(new))
            added = sorted(set(new)-set(old))
        finally:
            App.closeDocument(revised.Name)
            App.closeDocument(previous.Name)
    result = {'status': 'PUBLISHED_CAD_COMPARISON_PASS',
              'reference_commit': reference, 'reference_native_sha256': hashlib.sha256(historical).hexdigest(),
              'current_native_sha256': sha(current), 'pairs': rows,
              'resolved_published_intersections': sum(r['published_overlap_mm3'] > 0.01 for r in rows),
              'removed_objects': removed, 'added_objects': added,
              'scope': 'Named nominal interface comparison; not whole-machine physical qualification',
              'reference_overlaps': data['integrated_clearance']['reference_overlaps'],
              'physical_validation_state': 'NOT_RUN', 'fabrication_authorized': False,
              'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
                  (Path(__file__).resolve(), contract, manifest, current,
                   ROOT/'validation/integrated_assembly_clearance.py')}}
    out = ROOT/'analysis/frame_v08/results/published_comparison.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'], 'resolved', result['resolved_published_intersections'], flush=True)


if __name__ == '__main__':
    main()
