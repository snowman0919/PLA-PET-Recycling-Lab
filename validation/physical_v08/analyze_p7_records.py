#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,sys
from pathlib import Path

LIMITS={
 'pe_bond_worst':('max',0.10),'insulation_resistance':('min',1.0),'insulation_test_voltage':('range',(500.0,500.0)),
 'logic_rail_voltage':('range',(22.8,25.2)),'logic_startup_current':('max',0.5),'hazardous_enable_count_after_reset':('max',0.0),
}
BOOL_TRUE={'electronics_disconnected_for_megger','estop_k0_deenergized','lid_k0_deenergized','service_k0_deenergized','thermal_k0_deenergized','motor_heater_permission_removed_on_open','fuse_ids_match_schedule','point_to_point_wiring_match'}
BOOL_FALSE={'automatic_restart_after_power_restore'}

def n(v):
 x=float(v)
 if not math.isfinite(x): raise ValueError('non-finite')
 return x

def main(p:Path):
 rows={r['metric']:r for r in csv.DictReader(p.open())}; out={'status':'PASS','checks':{},'stage_p7_pass':False,'hardware_authorization':False}
 try:
  for k,(mode,lim) in LIMITS.items():
   r=rows[k]; v=n(r['value']); u=n(r['u95'])
   if u<0: raise ValueError(k+' negative U95')
   if not all(r.get(f,'').strip() for f in ('instrument_id','operator','reviewer','evidence_path')): raise ValueError(k+' provenance')
   ok=(v+u<=lim) if mode=='max' else (v-u>=lim) if mode=='min' else (v-u>=lim[0] and v+u<=lim[1])
   out['checks'][k]={'value':v,'u95':u,'pass':ok}
   if not ok: out['status']='FAIL'
  for k,expect in [(x,True) for x in BOOL_TRUE]+[(x,False) for x in BOOL_FALSE]:
   r=rows[k]
   if not all(r.get(f,'').strip() for f in ('operator','reviewer','evidence_path')): raise ValueError(k+' provenance')
   actual=r['value'].strip().lower() in ('true','yes','1','pass'); ok=actual is expect
   out['checks'][k]={'pass':ok}
   if not ok: out['status']='FAIL'
 except (KeyError,ValueError,TypeError) as e:
  out={'status':'NOT_RUN_OR_REJECTED','stage_p7_pass':False,'hardware_authorization':False,'reason':str(e)}
 print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out['status']=='PASS' else 2
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: analyze_p7_records.py p7_electrical_safety.csv')
 raise SystemExit(main(Path(sys.argv[1])))
