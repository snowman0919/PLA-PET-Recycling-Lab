"""Validate a coherent drive-review snapshot, not physical commissioning."""
from pathlib import Path
import hashlib, json, math, re, subprocess
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'exports/final/drive_ggm_v08'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def bound_path(base, relative):
    path = (base/relative).resolve()
    if not path.is_relative_to(base.resolve()): raise ValueError('Path escapes evidence root')
    return path

def check_bindings(data):
    bindings = data.get('source_sha256', {})
    if not bindings: raise ValueError('Empty evidence bindings')
    for name, digest in bindings.items():
        if not re.fullmatch('[0-9a-f]{64}', digest): raise ValueError('Invalid digest')
        if sha(bound_path(ROOT,name)) != digest: raise ValueError('Stale source: '+name)

def main():
    paths = [OUT/'manifest.json', HERE/'geometry_review.json', HERE/'process_limits.json',
             ROOT/'control/ggm_drive_contract.json', Path(__file__)]
    started = {str(p.relative_to(ROOT)):sha(p) for p in paths}
    geometry, lands, limits, contract = [json.loads(p.read_text()) for p in paths[:4]]
    for data in (geometry,lands,limits): check_bindings(data)
    if geometry['status']!='NEW_DRIVE_CLEARANCE_PASS' or geometry['review']['new_interference']:
        raise ValueError('Unresolved new drive interference')
    seen=set()
    for row in geometry['exports']:
        if row['file'] in seen: raise ValueError('Duplicate export')
        seen.add(row['file'])
        for filekey,hashkey in [('file','sha256'),('fcstd','fcstd_sha256')]:
            if sha(bound_path(OUT,row[filekey])) != row[hashkey]: raise ValueError('Changed export')
        if row['status']!='REIMPORT_PASS' or row['solids']<=0: raise ValueError('Invalid solid export')
    full=next(r for r in geometry['exports'] if r['file']=='GGM-FULL-ASM.step')
    if not all(0<a<=b for a,b in zip(full['bbox_mm'],[500,750,1000])):
        raise ValueError('Machine exceeds design envelope')
    if not all(r['pass'] for r in lands['journal_checks']): raise ValueError('Invalid bearing land')
    if limits['case_count']!=8: raise ValueError('Missing operating cases')
    raw = HERE/'raw'; raw.mkdir(exist_ok=True)
    header=ROOT/'firmware/arduino_mega/src/ggm_drive_guard.h'
    test=ROOT/'firmware/ggm_drive_v08/test_guard.cpp'
    head_hash=sha(header); test_hash=sha(test)
    build=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I'+str(header.parent),
        str(test),'-o',str(raw/'guard_test')],capture_output=True,text=True,timeout=60)
    if build.returncode: raise RuntimeError(build.stderr)
    run=subprocess.run([str(raw/'guard_test')],capture_output=True,text=True,timeout=30)
    if run.returncode or 'PASS' not in run.stdout: raise RuntimeError(run.stdout+run.stderr)
    if sha(header)!=head_hash or sha(test)!=test_hash: raise ValueError('Guard changed during test')
    proposed=[]
    for row in limits['cases']:
        nominal=contract['protection']['command_limit_gearbox_nm']-row['screw_peak_nm']
        proposed.append({'case':row['case'], 'peak_nm':row['screw_peak_nm'],
            'nominal_trip_margin_nm':nominal,
            'margin_with_positive_calibration_bias_nm':nominal-contract['protection']['assumed_calibration_error_nm'],
            'physical_validation':'NOT_RUN'})
    result={'status':'CONSISTENT_REVIEW_SNAPSHOT', 'machine_release':'HOLD',
        'physical_validation':'NOT_RUN', 'hardware_authorization':'NOT_GRANTED',
        'export_count':len(seen), 'new_drive_interference_count':0,
        'inherited_interference_count':len(geometry['review']['inherited_findings']),
        'full_bbox_mm':full['bbox_mm'], 'full_solid_count':full['solids'],
        'journal_checks':len(lands['journal_checks']), 'key_checks':len(lands['key_checks']),
        'guard_test_output':run.stdout.strip(),
        'guard_source_sha256':head_hash, 'guard_test_sha256':test_hash,
        'process_case_count':len(proposed),'process_trip_margins':proposed,
        'source_sha256':started}
    if any(sha(ROOT/p)!=h for p,h in started.items()): raise ValueError('Snapshot changed')
    (HERE/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
