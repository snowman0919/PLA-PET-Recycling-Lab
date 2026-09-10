#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path

REQ = {
    'rail_squareness_700': ('max', 0.50),
    'shredder_min_static_clearance': ('min', 1.90),
    'shredder_hand_rotation_contacts': ('max', 0.0),
    'extruder_cold_axial_travel': ('min', 1.50),
    'extruder_rear_retainer_endplay': ('range', (0.12, 0.28)),
}
BOOL_FALSE = {'guard_moving_envelope_intrusion','guard_hot_envelope_intrusion'}

def num(s):
    v=float(s)
    if not math.isfinite(v): raise ValueError('non-finite')
    return v

def main(path: Path):
    rows={r['metric']:r for r in csv.DictReader(path.open())}
    out={'status':'PASS','checks':{},'physical_result':True}
    for k,(mode,lim) in REQ.items():
        r=rows[k]; v=num(r['value']); u=num(r['u95'])
        if u < 0: raise ValueError(f'{k}: negative U95')
        if not all(r.get(f,'').strip() for f in ('instrument_id','operator','reviewer','evidence_path')): raise ValueError(f'{k}: incomplete provenance')
        ok = (v+u <= lim) if mode=='max' else (v-u >= lim) if mode=='min' else (v-u >= lim[0] and v+u <= lim[1])
        out['checks'][k]={'value':v,'u95':u,'pass':ok}
        out['status']='FAIL' if not ok else out['status']
    for k in BOOL_FALSE:
        r=rows[k]
        if not all(r.get(f,'').strip() for f in ('operator','reviewer','evidence_path')): raise ValueError(f'{k}: incomplete provenance')
        ok=r['value'].strip().lower() in ('false','0','no')
        out['checks'][k]={'pass':ok}
        out['status']='FAIL' if not ok else out['status']
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out['status']=='PASS' else 2

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: analyze_p2_records.py p2_cold_fit.csv')
    raise SystemExit(main(Path(sys.argv[1])))
