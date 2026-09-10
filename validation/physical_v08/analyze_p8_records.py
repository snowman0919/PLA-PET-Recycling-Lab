#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,sys
from pathlib import Path

LIMITS={'screw_start_rpm':('max',10.0),'screw_max_rpm':('max',20.0)}
BOOL_TRUE={'shredder_speed_expectation_reviewed','normal_stop_removes_command','estop_removes_command','tach_loss_removes_command'}
BOOL_FALSE={'screw_reverse_commanded','abnormal_bearing_or_coupling_temp_trend','abnormal_vibration_or_noise','automatic_restart_after_recovery'}

def n(v):
 x=float(v)
 if not math.isfinite(x): raise ValueError('non-finite')
 return x

def provenance(r,k):
 if not all(r.get(f,'').strip() for f in ('instrument_id','operator','reviewer','evidence_path')): raise ValueError(k+' provenance')

def main(p:Path):
 rows={r['metric']:r for r in csv.DictReader(p.open())}; out={'status':'PASS','checks':{},'stage_p8_pass':False,'hardware_authorization':False}
 try:
  r=rows['shredder_cutter_rpm']; provenance(r,'shredder_cutter_rpm'); rpm=n(r['value']); u=n(r['u95'])
  if u<0 or rpm-u<=0: raise ValueError('invalid shredder rpm record')
  out['checks']['shredder_cutter_rpm']={'value':rpm,'u95':u,'design_expectation_rpm':16.0,'pass':True}
  for k,(mode,lim) in LIMITS.items():
   r=rows[k]; provenance(r,k); v=n(r['value']); u=n(r['u95'])
   if u<0: raise ValueError(k+' negative U95')
   ok=v+u<=lim; out['checks'][k]={'value':v,'u95':u,'pass':ok}
   if not ok: out['status']='FAIL'
  for k,expect in [(x,True) for x in BOOL_TRUE]+[(x,False) for x in BOOL_FALSE]:
   r=rows[k]; provenance(r,k); actual=r['value'].strip().lower() in ('true','yes','1','pass'); ok=actual is expect
   out['checks'][k]={'pass':ok}
   if not ok: out['status']='FAIL'
 except (KeyError,ValueError,TypeError) as e:
  out={'status':'NOT_RUN_OR_REJECTED','stage_p8_pass':False,'hardware_authorization':False,'reason':str(e)}
 print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out['status']=='PASS' else 2
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: analyze_p8_records.py p8_motor_dry_run.csv')
 raise SystemExit(main(Path(sys.argv[1])))
