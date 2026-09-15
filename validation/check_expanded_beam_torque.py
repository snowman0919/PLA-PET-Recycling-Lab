"""FRD 확장 빔 고정단의 힘에서 독립 토크 추출; 물리 구조 qualification 아님."""
import json
import math
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/final_validation'))
from run_calculix_v08 import reactions, sha256


def verify_torque(reaction, applied):
    assert reaction['node_count']==4
    torque = reaction['moment_about_origin_nm'][0]
    assert math.isfinite(applied) and math.isfinite(torque) and abs(torque+applied)<.001
    return torque

summary = ROOT/'analysis/final_validation/results/v0.8/summary.json'
data = json.loads(summary.read_text())
raw = ROOT/data['raw_directory']
output = summary.with_name('expanded_beam_torque.json')
output.write_text('{"status":"INCOMPLETE","physical_validation_state":"NOT_RUN"}\n')
checks = []
for case in ('LC02','LC05'):
    for shaft,series in data[case]['per_shaft'].items():
        for mesh in series['meshes']:
            frd = raw/f"{case}_{shaft}_{mesh['mesh']}"/'model.frd'
            coordinates = {}
            active = False
            for line in frd.read_text().splitlines():
                if line.startswith('    2C'):
                    active = True
                    continue
                if active and line.startswith(' -3'):
                    break
                if active and line.startswith(' -1'):
                    v = re.findall(r'[-+]?\d*\.?\d+(?:E[-+]?\d+)?',line)
                    coordinates[int(v[1])] = tuple(map(float,v[2:5]))
            selected = {n for n,(x,y,z) in coordinates.items() if abs(x)<1e-10}
            assert len(selected)==4 and all(math.isfinite(v) for xyz in coordinates.values() for v in xyz)
            reaction = reactions(frd,selected,coordinates)
            applied = mesh['provenance']['applied_torque_nm']
            torque = verify_torque(reaction,applied)
            checks.append({'case':case,'shaft':shaft,'mesh':mesh['mesh'],
                           'measured_torque_nm':torque,'applied_torque_nm':applied,
                           'residual_nm':torque+applied,'frd_sha256':sha256(frd)})
assert len(checks)==9
negative_controls = 0
for reaction, applied in (
    ({'node_count':4,'moment_about_origin_nm':[22,0,0]},22),
    ({'node_count':4,'moment_about_origin_nm':[-21,0,0]},22),
    ({'node_count':3,'moment_about_origin_nm':[-22,0,0]},22),
    ({'node_count':4,'moment_about_origin_nm':[float('nan'),0,0]},22),
):
    try:
        verify_torque(reaction,applied)
    except AssertionError:
        negative_controls += 1
    else:
        raise AssertionError('Corrupt reaction accepted')
assert negative_controls==4
output.write_text(json.dumps({'status':'HOLD','extraction_checks':'PASS',
    'negative_controls_rejected':negative_controls,
    'physical_validation_state':'NOT_RUN','checks':checks,
    'scope':'B31 expanded x=0 section only; equivalent square beam and end torsion datum assumptions remain',
    'source_sha256':{str(p.relative_to(ROOT)):sha256(p) for p in
        (Path(__file__).resolve(),summary,ROOT/'analysis/final_validation/run_calculix_v08.py')}},indent=2)+'\n')
print('EXPANDED_BEAM_TORQUE_HOLD',len(checks),max(abs(c['residual_nm']) for c in checks))
