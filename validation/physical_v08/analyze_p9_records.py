#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

TARGETS={('PLA','Z1'):180,('PLA','Z2'):195,('PLA','Z3'):205,('PLA','DIE'):200,('PET','Z1'):245,('PET','Z2'):260,('PET','Z3'):270,('PET','DIE'):265}
NUM={'cold_axial_travel_reference':('min',1.50),'die_fastener_length_min':('min',42.4),'die_fastener_length_max':('max',42.6)}
TRUE={'t1_t5_mapping_correct','sensor_open_short_fault_detected','independent_thermal_chain_removes_heater_energy','die_fasteners_dry_1p50Nm_setting'}
FALSE={'hot_mount_hard_stop_contact','polymer_leak_evaluated_in_p9'}

def n(v):
 x=float(v)
 if not math.isfinite(x): raise ValueError('non-finite')
 return x

def prov(r,fields):
 if not all(r.get(f,'').strip() for f in fields): raise ValueError('missing provenance')

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('thermal',type=Path); ap.add_argument('safety',type=Path); ap.add_argument('--output',type=Path)
 a=ap.parse_args(); out={'status':'PASS','stage_p9_pass':False,'hardware_authorization':False,'thermal':{},'safety':{}}
 try:
  trows=list(csv.DictReader(a.thermal.open())); seen=set()
  for r in trows:
   key=(r['profile'],r['zone']); seen.add(key)
   if key not in TARGETS: raise ValueError('unexpected thermal profile/zone')
   prov(r,('logger_id','operator','reviewer','evidence_path')); mean=n(r['measured_mean_c']); u=n(r['u95_c']); target=TARGETS[key]
   if u<0: raise ValueError('negative thermal U95')
   ok=(mean-u>=target-5) and (mean+u<=target+5)
   out['thermal'][f'{key[0]}-{key[1]}']={'mean_c':mean,'u95_c':u,'target_c':target,'pass':ok}
   if not ok: out['status']='FAIL'
  if seen!=set(TARGETS): raise ValueError('incomplete thermal profile coverage')
  srows={r['metric']:r for r in csv.DictReader(a.safety.open())}
  for k,(mode,lim) in NUM.items():
   r=srows[k]; prov(r,('instrument_id','operator','reviewer','evidence_path')); v=n(r['value']); u=n(r['u95'])
   if u<0: raise ValueError(k+' negative U95')
   ok=(v-u>=lim) if mode=='min' else (v+u<=lim)
   out['safety'][k]={'value':v,'u95':u,'pass':ok}
   if not ok: out['status']='FAIL'
  for k,expect in [(x,True) for x in TRUE]+[(x,False) for x in FALSE]:
   r=srows[k]; prov(r,('operator','reviewer','evidence_path')); actual=r['value'].strip().lower() in ('true','yes','1','pass'); ok=actual is expect
   out['safety'][k]={'pass':ok}
   if not ok: out['status']='FAIL'
 except (KeyError,ValueError,TypeError,FileNotFoundError) as e:
  out={'status':'NOT_RUN_OR_REJECTED','stage_p9_pass':False,'hardware_authorization':False,'reason':str(e)}
 text=json.dumps(out,ensure_ascii=False,indent=2)+'\n'; print(text,end='')
 if a.output: a.output.write_text(text)
 raise SystemExit(0 if out['status']=='PASS' else 2)
if __name__=='__main__': main()
