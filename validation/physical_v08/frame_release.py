"""R1: bind integrated CAD, comparative evidence and cut demand; no cut permission."""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = 'exports/final/frame_v08/frame_release.json'
CUTLIST = 'exports/fabrication/frame_cut_list.csv'
CONTRACT = 'cad/parameters/ggm_frame_revision.json'
GEOMETRY = 'analysis/frame_v08/results/geometry.json'
BEAM = 'analysis/frame_v08/results/beam_comparison.json'
GGM = 'exports/final/drive_ggm_v08/manifest.json'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def checked(root, rel):
    if not isinstance(rel, str) or not rel or '\\' in rel:
        raise ValueError('invalid frame source path')
    path = root / rel
    if Path(rel).is_absolute() or '..' in Path(rel).parts or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('unsafe frame source: ' + rel)
    if any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root)):
        raise ValueError('symlinked frame source: ' + rel)
    if not path.is_file(): raise ValueError('missing frame source: ' + rel)
    return path

def check_hashes(root, values, required=()):
    if not isinstance(values, dict) or not values or not set(required) <= set(values):
        raise ValueError('empty or incomplete frame bindings')
    for rel, digest in values.items():
        if sha(checked(root, rel)) != digest: raise ValueError('stale frame binding: ' + rel)

def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('nonfinite or nonnumeric frame evidence')
    return value

def beam_checks(beam, spec):
    expected = set(itertools.product((.03, .1, 1.), (.01, 1., 100.), (.5, 1.)))
    results = beam.get('results', [])
    if beam.get('unit_benchmark') != 'CANTILEVER_AXIAL_BIAXIAL_BENDING_TORSION_PASS':
        raise ValueError('beam analytic benchmark missing')
    if len(results) != len(expected) or beam.get('configurations') != len(expected):
        raise ValueError('beam sensitivity coverage mismatch')
    seen = set(); worst = 0.0
    for result in results:
        key = tuple(finite(result[k]) for k in ('torsion_fraction', 'joint_scale', 'tie_section_scale'))
        if key not in expected or key in seen: raise ValueError('beam sensitivity duplicated/missing')
        seen.add(key)
        before, after = result['before'], result['after']
        if before['labels'] != after['labels'] or len(set(before['labels'])) != 27:
            raise ValueError('beam load coverage mismatch')
        a, b = before['compliance_mm'], after['compliance_mm']
        if len(a) != 27 or len(b) != 27 or any(finite(v) <= 0 for v in a + b):
            raise ValueError('invalid beam compliance samples')
        if any(finite(x['residual_n']) < 0 or x['residual_n'] >= 1e-4 for x in (before, after)):
            raise ValueError('beam equilibrium residual exceeds criterion')
        ratio = max(y/x for x, y in zip(a, b))
        if not math.isclose(ratio, finite(result['max_compliance_ratio']), rel_tol=1e-10):
            raise ValueError('beam ratio not supported by samples')
        if result.get('pass') is not True or ratio > finite(spec['comparative_screen_limit_ratio']):
            raise ValueError('frame comparative compliance exceeds contract')
        worst = max(worst, ratio)
    if not math.isclose(worst, finite(beam['worst_ratio']), rel_tol=1e-10):
        raise ValueError('beam worst ratio mismatch')
    if beam.get('assembled_frame_strength_qualified') is not False:
        raise ValueError('comparative screen cannot authorize assembled frame strength')

def validate(root=ROOT):
    root = Path(root).resolve()
    report = json.loads(checked(root, REPORT).read_text())
    if report.get('status') != 'FRAME_CUTLIST_GEOMETRY_MATCH' or report.get('cut_authorization') is not False or report.get('physical_validation_state') != 'NOT_RUN':
        raise ValueError('frame release status/authorization mismatch')
    check_hashes(root, report['source_sha256'], [CONTRACT, GEOMETRY, BEAM, GGM, 'release/build_frame_release.py'])
    check_hashes(root, report['output_sha256'], [CUTLIST, 'exports/final/frame_v08/frame_members.csv'])
    spec = json.loads(checked(root, CONTRACT).read_text())
    geometry = json.loads(checked(root, GEOMETRY).read_text())
    beam = json.loads(checked(root, BEAM).read_text())
    if report.get('revision') != spec['revision'] or geometry.get('status') != 'FRAME_DELTA_GEOMETRY_PASS' or beam.get('status') != 'FRAME_COMPARATIVE_SCREEN_PASS':
        raise ValueError('frame delta verification incomplete')
    for evidence in (geometry, beam): check_hashes(root, evidence['source_sha256'])
    check_hashes(root, geometry['source_sha256'], ['cad/freecad/drive_v08/layout.py', 'cad/freecad/drive_v08/detail.py', 'cad/freecad/drive_v08/frame_revision.py'])
    if geometry.get('new_interferences') != [] or geometry.get('joint_strength_qualified') is not False:
        raise ValueError('invalid geometry or overclaimed joint strength')
    beam_checks(beam, spec)
    ggm = json.loads(checked(root, GGM).read_text())
    check_hashes(root, ggm['source_sha256'])
    if ggm.get('status') != 'NEW_DRIVE_CLEARANCE_PASS' or ggm.get('machine_release') != 'HOLD':
        raise ValueError('integrated CAD status mismatch')
    clearance = ggm.get('integrated_clearance', {})
    if (clearance.get('status') != 'GGM_NOMINAL_COLLISION_POLICY_PASS' or
            clearance.get('unexpected_count') != 0 or
            clearance.get('physical_validation_state') != 'NOT_RUN' or
            clearance.get('fabrication_authorized') is not False):
        raise ValueError('full integrated clearance gate missing or invalid')
    motion = ggm.get('integrated_motion', {})
    if (motion.get('status') != 'GGM_NOMINAL_MOTION_CLEARANCE_PASS' or
            motion.get('physical_validation_state') != 'NOT_RUN' or
            motion.get('fabrication_authorized') is not False):
        raise ValueError('integrated motion review missing or invalid')
    whole = next(r for r in ggm['exports'] if r['file'] == 'GGM-FULL-ASM.step')
    for name, key in (('file', 'sha256'), ('fcstd', 'fcstd_sha256')):
        rel = 'exports/final/drive_ggm_v08/' + whole[name]
        if report['source_sha256'].get(rel) != whole[key] or sha(checked(root, rel)) != whole[key]:
            raise ValueError('frame CAD export binding mismatch')
    with checked(root, CUTLIST).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if rows != report['members'] or not rows: raise ValueError('frame member table mismatch')
    expected = {r['id']: r for r in geometry['after'] if 'section_mm' in r}
    if len({r['cad_object'] for r in rows}) != len(rows) or {r['cad_object'] for r in rows} != set(expected):
        raise ValueError('frame member identity coverage mismatch')
    totals = {'2020': {'count': 0, 'length_mm': 0.}, '2040': {'count': 0, 'length_mm': 0.}}
    for row in rows:
        item = expected[row['cad_object']]; typ = row['profile_type']
        if typ not in totals or row['quantity'] != '1' or float(row['cut_length_mm']) != finite(item['length_mm']):
            raise ValueError('frame count/length mismatch')
        section = [20., 20.] if typ == '2020' else [20., 40.]
        if item['section_mm'] != section or row['axis'] != 'XYZ'[item['axis']]:
            raise ValueError('frame CAD section/orientation mismatch')
        if row['stock'] != ('20x20' if typ == '2020' else '20x40') + ' aluminum profile':
            raise ValueError('frame section mismatch')
        if row['part_id'] != 'FRM-' + row['cad_object'] or row['length_tolerance_mm'] != '+/-0.5':
            raise ValueError('frame member ID or cut allowance drift')
        totals[typ]['count'] += 1; totals[typ]['length_mm'] += item['length_mm']
    if totals != spec['expected_profiles'] or totals != report['totals']:
        raise ValueError('frame totals mismatch')
    return {'status': 'FRAME_CUTLIST_BINDING_PASS', 'members': len(rows), 'totals': totals,
            'cut_authorization': False, 'stock_nesting_status': 'ACTUAL_STOCK_REQUIRED',
            'frame_release_sha256': sha(root/REPORT), 'cutlist_sha256': sha(root/CUTLIST)}

if __name__ == '__main__': print(json.dumps(validate(), indent=2))
