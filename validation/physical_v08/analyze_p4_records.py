#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path

def read_csv(p):
    with p.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def yes(v): return str(v).strip().upper() in {'YES','TRUE','PASS','1'}
def no(v): return str(v).strip().upper() in {'NO','FALSE','NONE','0'}
def num(v):
    x=float(v)
    if not math.isfinite(x): raise ValueError('non-finite numeric field')
    return x

def check_p3(path:Path):
    d=json.loads(path.read_text())
    if d.get('stage')!='P3' or d.get('status')!='PASS': raise ValueError('P3 physical release is not PASS')
    for k in ('approved_by','reviewed_at','raw_evidence_manifest','raw_evidence_manifest_sha256'):
        if not d.get(k): raise ValueError('P3 release missing '+k)
    evidence=(path.parent/d['raw_evidence_manifest']).resolve() if not Path(d['raw_evidence_manifest']).is_absolute() else Path(d['raw_evidence_manifest'])
    if not evidence.is_file(): raise ValueError('P3 evidence manifest missing')
    if hashlib.sha256(evidence.read_bytes()).hexdigest()!=d['raw_evidence_manifest_sha256']: raise ValueError('P3 evidence hash mismatch')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('dir',type=Path); ap.add_argument('--p3-release',type=Path,required=True); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); d=a.dir
    try:
        check_p3(a.p3_release)
        pre=read_csv(d/'preflight_inspection.csv'); torque=read_csv(d/'gate1_results.csv'); jam=read_csv(d/'jam_recovery_results.csv'); chip=read_csv(d/'chip_size_results.csv')
        if len(pre)<14 or any(r.get('pass_fail','').strip().upper()!='PASS' for r in pre): raise ValueError('P4 preflight incomplete/fail')
        if any(not r.get('operator') or not r.get('reviewer') or not r.get('evidence_path') for r in pre): raise ValueError('preflight provenance incomplete')
        if len(torque)<25: raise ValueError('quasi-static characterization coverage incomplete')
        for r in torque:
            for k in ('operator','reviewer','photo_video_path','raw_log_path'):
                if not r.get(k): raise ValueError('torque provenance incomplete')
            if not no(r.get('permanent_damage')): raise ValueError('permanent damage in torque characterization')
            if r.get('calculated_peak_Nm') and r.get('peak_N') and r.get('radius_m'):
                calc=num(r['peak_N'])*num(r['radius_m'])
                if abs(calc-num(r['calculated_peak_Nm']))>0.05: raise ValueError('torque arithmetic mismatch')
        if len(jam)!=6 or sum(r['material']=='PLA' for r in jam)!=3 or sum(r['material']=='PET' for r in jam)!=3: raise ValueError('jam replicate coverage')
        for r in jam:
            if not r.get('operator') or not r.get('reviewer') or not r.get('photo_video_path') or not r.get('raw_log_path'): raise ValueError('jam provenance incomplete')
            if not no(r.get('permanent_damage')): raise ValueError('permanent damage during jam')
            retries=int(float(r['retry_count']))
            if retries>3: raise ValueError('reverse retry limit exceeded')
            if not yes(r.get('guard_lockout_required_for_reset')): raise ValueError('reset lockout not enforced')
            if not yes(r.get('jam_cleared')) and not yes(r.get('latched_fault_after_third_failure')): raise ValueError('uncleared jam did not latch fault')
        if len(chip)!=2 or {r['material'] for r in chip}!={'PLA','PET'}: raise ValueError('chip batch coverage')
        for r in chip:
            if int(float(r['oversize_recirc_count']))>1: raise ValueError('recirculation count exceeded')
            f36=num(r['fraction_3_6_percent']); f20=num(r['fraction_gt20_percent']); fines=num(r['fines_percent']); rec=num(r['recovery_percent'])
            if f36<70 or f20>2 or fines>15 or rec<95: raise ValueError(r['material']+' chip-size acceptance')
            if not r.get('operator') or not r.get('reviewer') or not r.get('photo_path') or not r.get('scale_log_path'): raise ValueError('chip provenance incomplete')
        result={'status':'NUMERIC_RECORD_CHECK_PASS','stage_p4_pass':False,'hardware_authorization':False,'note':'Independent review and explicit stage release are still required.'}
    except (ValueError,KeyError,FileNotFoundError) as e:
        result={'status':'NOT_RUN_OR_REJECTED','stage_p4_pass':False,'hardware_authorization':False,'reason':str(e)}
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'; print(text,end='')
    if a.output: a.output.write_text(text)
    raise SystemExit(0 if result['status']=='NUMERIC_RECORD_CHECK_PASS' else 2)
if __name__=='__main__': main()
