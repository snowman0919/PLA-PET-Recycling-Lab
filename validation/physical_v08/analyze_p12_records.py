#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,sys
from pathlib import Path

NUM={'puller_slip':('max',1.0),'traverse_usable_width':('min',68.0),'dancer_control_stop_angle':('strict_max',0.36)}
TRUE={'full_1kg_nominal_winding_path_completed','stable_strand_used_for_final_pass'}
FALSE={'traverse_end_collision','dancer_hard_stop_contact','spool_spill','guard_contact','traverse_jam'}

def n(v):
 x=float(v)
 if not math.isfinite(x): raise ValueError('non-finite')
 return x

def prov(r,k):
 if not all(r.get(f,'').strip() for f in ('instrument_id','operator','reviewer','evidence_path')): raise ValueError(k+' provenance')

def main(p:Path):
 rows={r['metric']:r for r in csv.DictReader(p.open())}; out={'status':'PASS','checks':{},'stage_p12_pass':False,'hardware_authorization':False}
 try:
  for k,(mode,lim) in NUM.items():
   r=rows[k]; prov(r,k); v=n(r['value']); u=n(r['u95'])
   if u<0: raise ValueError(k+' negative U95')
   if mode=='max': ok=v+u<=lim
   elif mode=='min': ok=v-u>=lim
   else: ok=v+u<lim
   out['checks'][k]={'value':v,'u95':u,'pass':ok}
   if not ok: out['status']='FAIL'
  for k,expect in [(x,True) for x in TRUE]+[(x,False) for x in FALSE]:
   r=rows[k]; prov(r,k); actual=r['value'].strip().lower() in ('true','yes','1','pass'); ok=actual is expect
   out['checks'][k]={'pass':ok}
   if not ok: out['status']='FAIL'
 except (KeyError,ValueError,TypeError) as e:
  out={'status':'NOT_RUN_OR_REJECTED','stage_p12_pass':False,'hardware_authorization':False,'reason':str(e)}
 print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out['status']=='PASS' else 2
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: analyze_p12_records.py p12_forming_spool.csv')
 raise SystemExit(main(Path(sys.argv[1])))
