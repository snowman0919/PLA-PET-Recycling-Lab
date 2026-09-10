#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,sys
from pathlib import Path

LIMITS={
 'screw_barrel_clearance_min':('min',0.28),'screw_barrel_clearance_max':('max',0.32),
 'bearing_pocket_diametral_clearance':('range',(0.30,0.35)),'thrust_loaded_endplay':('range',(0.05,0.15)),
 'hand_rotation_contacts':('max',0.0),'drive_coaxiality':('max',0.05),
 'front_guide_cold_axial_travel':('min',1.50),'rear_retainer_cold_endplay':('range',(0.12,0.28)),
}
BOOL_TRUE={'thrust_washer_orientation_ok'}; BOOL_FALSE={'printed_shim_used'}

def n(v):
 x=float(v)
 if not math.isfinite(x): raise ValueError('non-finite')
 return x

def main(p:Path):
 rows={r['metric']:r for r in csv.DictReader(p.open())}; out={'status':'PASS','checks':{},'stage_p6_pass':False,'hardware_authorization':False}
 try:
  for k,(mode,lim) in LIMITS.items():
   r=rows[k]; v=n(r['value']); u=n(r['u95'])
   if u<0: raise ValueError(k+' negative U95')
   if not all(r.get(f,'').strip() for f in ('instrument_id','operator','reviewer','evidence_path')): raise ValueError(k+' provenance')
   ok=(v-u>=lim) if mode=='min' else (v+u<=lim) if mode=='max' else (v-u>=lim[0] and v+u<=lim[1])
   out['checks'][k]={'value':v,'u95':u,'pass':ok}
   if not ok: out['status']='FAIL'
  for k,expect in [(x,True) for x in BOOL_TRUE]+[(x,False) for x in BOOL_FALSE]:
   r=rows[k]
   if not all(r.get(f,'').strip() for f in ('operator','reviewer','evidence_path')): raise ValueError(k+' provenance')
   actual=r['value'].strip().lower() in ('true','yes','1','pass'); ok=actual is expect
   out['checks'][k]={'pass':ok}
   if not ok: out['status']='FAIL'
 except (KeyError,ValueError,TypeError) as e:
  out={'status':'NOT_RUN_OR_REJECTED','stage_p6_pass':False,'hardware_authorization':False,'reason':str(e)}
 print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out['status']=='PASS' else 2
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: analyze_p6_records.py p6_cold_extruder.csv')
 raise SystemExit(main(Path(sys.argv[1])))
