#!/usr/bin/env python3
"""Offline P5 process-coupon record analyzer. Never authorizes an order or fabrication."""
from __future__ import annotations
import argparse,csv,json,math,re
from pathlib import Path

HERE=Path(__file__).resolve().parent
CONTRACT=json.loads((HERE/'p5_coupon_contract.json').read_text(encoding='utf-8'))

def read(path):
    with path.open(newline='',encoding='utf-8') as fh: return list(csv.DictReader(fh))
def num(value, field='value'):
    if value is None or str(value).strip()=='': raise ValueError('blank '+field)
    x=float(value)
    if not math.isfinite(x): raise ValueError('non-finite '+field)
    return x
def maybe(value):
    return None if value is None or str(value).strip()=='' else num(value)
def yes(v): return str(v).strip().upper() in {'YES','Y','PASS','TRUE','APPROVED'}
def hashish(v): return bool(re.fullmatch(r'[0-9a-fA-F]{64}',str(v).strip()))

def interval(row):
    value=num(row['value']); u=num(row['u95_or_mpe'],'u95_or_mpe')
    if u<0: raise ValueError('negative uncertainty')
    lo=maybe(row.get('lower_limit')); hi=maybe(row.get('upper_limit'))
    if lo is not None and value-u < lo-1e-12: raise ValueError(f"{row['part_id']} {row['characteristic']} below lower bound")
    if hi is not None and value+u > hi+1e-12: raise ValueError(f"{row['part_id']} {row['characteristic']} above upper bound")
    return value,u

def check_capability(rows):
    by={r['id']:r for r in rows}
    hard=[r for r in rows if r['gate_class']=='HARD_GATE']
    for r in hard:
        if not yes(r['supplier_response']): raise ValueError(r['id']+' supplier hard gate not YES')
        if not r['evidence_path'].strip() or not hashish(r['sha256']): raise ValueError(r['id']+' supplier evidence missing')
    dev=by['CAP-10']
    if not yes(dev['supplier_response']): raise ValueError('CAP-10 deviation declaration missing')
    deviation=dev['proposed_deviation'].strip()
    baseline=deviation.upper() in {'','NONE','NO DEVIATION','N/A'}
    if not baseline:
        hp=by['CAP-11']
        if not yes(hp['supplier_response']) or not hp['evidence_path'].strip() or not hashish(hp['sha256']):
            raise ValueError('material/process deviation requires high-temperature property evidence and re-analysis')
        raise ValueError('declared deviation requires separate engineering re-analysis before P5 acceptance')
    return {'hard_gates':len(hard),'baseline_route':True,'hot_properties_hard_gate':False}

def check_measurements(rows):
    values={}
    screw_od=[]; barrel_id=[]
    required_meta=('instrument_id','calibration_ref','measured_at','operator','evidence_path','sha256')
    for r in rows:
        if any(not str(r.get(k,'')).strip() for k in required_meta): raise ValueError(f"{r['part_id']} {r['characteristic']} measurement metadata missing")
        if not hashish(r['sha256']): raise ValueError('measurement sha256 invalid')
        t=num(r['temperature_c'],'temperature_c')
        if t<18 or t>22: raise ValueError('dimensional/roughness inspection outside 18-22 C')
        value,u=interval(r)
        key=(r['part_id'],r['characteristic']); values.setdefault(key,[]).append((value,u,r))
        if key==('EX-CPN-SCR','flight_OD'): screw_od.append((value,u))
        if key==('EX-CPN-BAR','bore_ID'): barrel_id.append((value,u))
    counts={('EX-CPN-SCR','flight_OD'):3,('EX-CPN-SCR','pitch'):3,('EX-CPN-SCR','land'):3,
            ('EX-CPN-SCR','root_OD'):3,('EX-CPN-BAR','bore_ID'):4}
    for key,n in counts.items():
        if len(values.get(key,[]))<n: raise ValueError(f'{key} measurement coverage')
    # Conservative min/max clearance including uncertainty of the limiting pair.
    min_id=min(barrel_id,key=lambda x:x[0]); max_id=max(barrel_id,key=lambda x:x[0])
    min_od=min(screw_od,key=lambda x:x[0]); max_od=max(screw_od,key=lambda x:x[0])
    cmin=min_id[0]-max_od[0]; umin=math.hypot(min_id[1],max_od[1])
    cmax=max_id[0]-min_od[0]; umax=math.hypot(max_id[1],min_od[1])
    if cmin-umin<0.28-1e-12 or cmax+umax>0.32+1e-12:
        raise ValueError(f'matched clearance with uncertainty outside 0.28-0.32 mm: {cmin:.5f}±{umin:.5f}, {cmax:.5f}±{umax:.5f}')
    return {'measurement_rows':len(rows),'clearance_min_nominal_mm':cmin,'clearance_min_u95_mm':umin,
            'clearance_max_nominal_mm':cmax,'clearance_max_u95_mm':umax}

def check_certificates(rows):
    by={(r['part_id'],r['characteristic']):r for r in rows}
    for part in ('EX-CPN-SCR','EX-CPN-BAR'):
        grade=by[(part,'material_grade')]
        text=grade['value'].upper().replace(' ','')
        if 'SCM440' not in text or 'G4105' not in text: raise ValueError(part+' material grade/MTC mismatch')
        if not grade['certificate_id'].strip() or not grade['evidence_path'].strip() or not hashish(grade['sha256']): raise ValueError(part+' MTC evidence missing')
        lot=by[(part,'heat_lot_id')]
        if not lot['value'].strip() or not lot['certificate_id'].strip() or not lot['evidence_path'].strip() or not hashish(lot['sha256']): raise ValueError(part+' heat/lot ID evidence missing')
    numeric=[]
    for r in rows:
        if r['characteristic'] in {'material_grade','heat_lot_id'}: continue
        if not r['certificate_id'].strip() or not r['provider'].strip() or not r['evidence_path'].strip() or not hashish(r['sha256']):
            raise ValueError(f"{r['part_id']} {r['characteristic']} certificate metadata missing")
        if r['characteristic'] in {'qt_core_hardness','surface_hardness','final_effective_case_depth','nitride_process_case_target'} and not r.get('method_or_standard','').strip():
            raise ValueError(f"{r['part_id']} {r['characteristic']} method/test-load definition missing")
        value=num(r['value']); u=num(r['u95_or_mpe'],'u95_or_mpe')
        if u<0: raise ValueError('negative certificate uncertainty')
        lo=maybe(r['lower_limit']); hi=maybe(r['upper_limit'])
        if lo is not None and value-u<lo-1e-12: raise ValueError(f"{r['part_id']} {r['characteristic']} below limit")
        if hi is not None and value+u>hi+1e-12: raise ValueError(f"{r['part_id']} {r['characteristic']} above limit")
        numeric.append(r)
    return {'certificate_rows':len(rows),'numeric_certificate_rows':len(numeric),
            'screw_final_case_mm':num(by[('EX-CPN-SCR','final_effective_case_depth')]['value']),
            'barrel_final_case_mm':num(by[('EX-CPN-BAR','final_effective_case_depth')]['value']),
            'barrel_hone_removed_diameter_mm':num(by[('EX-CPN-BAR','final_hone_removed_on_diameter')]['value'])}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('dir',type=Path); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); d=a.dir
    files={'capability':'p5_supplier_capability.csv','measurements':'p5_coupon_measurements.csv','certificates':'p5_coupon_certificates.csv'}
    result={'status':'NOT_RUN_OR_REJECTED','stage_p5_pass':False,'full_part_order_authorized':False,'physical_action_authorized':False}
    try:
        if CONTRACT['purchase_or_manufacturing_authorized'] is not False: raise ValueError('contract authorization invariant')
        data={k:read(d/v) for k,v in files.items()}
        result.update({'status':'NUMERIC_RECORD_CHECK_PASS','capability':check_capability(data['capability']),
                       'measurements':check_measurements(data['measurements']),
                       'certificates':check_certificates(data['certificates']),
                       'note':'Coupon record arithmetic/document completeness passed. Engineering review and explicit user approval are still required before any production order.'})
    except (ValueError,KeyError,ZeroDivisionError) as e:
        result['reason']=str(e)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output: a.output.write_text(text)
    print(text,end='')
    raise SystemExit(0 if result['status']=='NUMERIC_RECORD_CHECK_PASS' else 2)
if __name__=='__main__': main()
