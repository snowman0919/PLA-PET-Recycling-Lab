#!/usr/bin/env python3
"""Authenticate S4 TH-INS-01 material coupon smoke evidence; never authorizes hot-zone power."""
from __future__ import annotations
import argparse,csv,datetime,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'control/thermal_barrier_tape_contract.json'
NUMERIC={
 'datasheet_continuous_service_rating':('positive',None,'C'),
 'coupon_interface_peak':('positive_or_zero',None,'C'),
 'coupon_outer_surface_peak':('positive_or_zero',None,'C'),
 'post_cool_edge_lift_max':('max',2.0,'mm'),
}
BOOL_TRUE={'same_lot_as_final_install','representative_metal_shield_surface'}
BOOL_FALSE={'direct_heater_barrel_die_wrap_used','visible_smoke','visible_charring','melting_or_shrink_failure','adhesive_flow_or_drip','loose_delamination','safety_function_claimed'}

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p:Path):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def num(v,name):
 if v is None or not str(v).strip(): raise ValueError(name+': blank numeric')
 x=float(v)
 if not math.isfinite(x): raise ValueError(name+': non-finite numeric')
 return x
def stamp(v):
 x=datetime.datetime.fromisoformat(str(v).replace('Z','+00:00'))
 if x.tzinfo is None: raise ValueError('measured_at must include timezone')
def auth(r,numeric):
 required=['operator','reviewer','measured_at','evidence_path','sha256']
 if numeric: required += ['instrument_id','calibration_ref']
 missing=[k for k in required if not str(r.get(k,'')).strip()]
 if missing: raise ValueError('missing evidence metadata: '+','.join(missing))
 if r['operator'].strip()==r['reviewer'].strip(): raise ValueError('independent reviewer must differ from operator')
 stamp(r['measured_at'])
 e=(ROOT/r['evidence_path']).resolve()
 if not e.is_relative_to(ROOT) or not e.is_file(): raise ValueError('invalid evidence path')
 if len(r['sha256'].strip())!=64 or sha(e)!=r['sha256'].strip().lower(): raise ValueError('evidence hash mismatch')
def boolean(r,name):
 t=r.get('value','').strip().upper()
 if t not in {'TRUE','FALSE','YES','NO','1','0','PASS'}: raise ValueError(name+': invalid boolean')
 return t in {'TRUE','YES','1','PASS'}

def evaluate(path:Path)->dict:
 out={'status':'S4_NOT_RUN_OR_REJECTED','p9_tape_smoke_prerequisite':False,'installation_authorized':False,'heater_energization_authorized':False,'machine_release':'HOLD'}
 try:
  path=path.resolve()
  if not path.is_relative_to(ROOT) or not path.is_file(): raise ValueError('S4 record must be an existing repository file')
  contract=json.loads(CONTRACT.read_text(encoding='utf-8'))
  if contract.get('part_id')!='TH-INS-01' or contract.get('safety_role')!='NONE' or contract.get('coupon_smoke',{}).get('required_before_final_hot_zone_use') is not True: raise ValueError('thermal barrier tape contract drift')
  data=rows(path); by={r.get('metric','').strip():r for r in data}; required=set(NUMERIC)|BOOL_TRUE|BOOL_FALSE
  if len(data)!=len(required) or set(by)!=required: raise ValueError('S4 tape smoke metric set mismatch')
  checks={}
  for m,(mode,limit,unit) in NUMERIC.items():
   r=by[m];auth(r,True)
   if r.get('unit','').strip()!=unit: raise ValueError(m+': unit mismatch')
   v=num(r.get('value'),m);u=num(r.get('u95'),m+' U95')
   if u<0: raise ValueError(m+': negative U95')
   if mode=='positive' and v-u<=0: raise ValueError(m+': positive rating required')
   if mode=='positive_or_zero' and v-u<0: raise ValueError(m+': nonnegative temperature required')
   if mode=='max' and v+u>float(limit): raise ValueError(m+': maximum acceptance failed')
   checks[m]={'value':v,'u95':u,'unit':unit,'pass':True}
  rating=checks['datasheet_continuous_service_rating']['value']
  interface=checks['coupon_interface_peak']
  margin=float(contract['installed_p9_acceptance']['continuous_rating_margin_c'])
  if interface['value']+interface['u95']+margin>rating: raise ValueError('S4 tape continuous-service temperature margin failed')
  checks['continuous_rating_margin']={'rating_c':rating,'interface_peak_plus_u95_c':interface['value']+interface['u95'],'required_margin_c':margin,'remaining_margin_c':rating-interface['value']-interface['u95'],'pass':True}
  for m,expected in [(x,True) for x in BOOL_TRUE]+[(x,False) for x in BOOL_FALSE]:
   r=by[m];auth(r,False);actual=boolean(r,m)
   if actual is not expected: raise ValueError(m+': boolean acceptance failed')
   checks[m]={'value':actual,'pass':True}
  out.update({'status':'S4_THERMAL_BARRIER_TAPE_SMOKE_PASS','p9_tape_smoke_prerequisite':True,'record_sha256':sha(path),'contract_sha256':sha(CONTRACT),'checks':checks,'note':'Material coupon smoke passed; final-machine installation and heater power remain separately gated.'})
 except (ValueError,KeyError,TypeError,FileNotFoundError,json.JSONDecodeError) as e: out['reason']=str(e)
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('record',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();r=evaluate(a.record);text=json.dumps(r,ensure_ascii=False,indent=2)+'\n';print(text,end='');
 if a.output:a.output.write_text(text,encoding='utf-8')
 raise SystemExit(0 if r['status']=='S4_THERMAL_BARRIER_TAPE_SMOKE_PASS' else 2)
if __name__=='__main__':main()
