#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
TARGET={'PLA':(180,195,205,200),'PET':(245,260,270,265)}

def n(v):
 x=float(v)
 if not math.isfinite(x): raise ValueError('non-finite numeric field')
 return x

def yes(v): return str(v).strip().lower() in ('true','yes','1','pass')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('record',type=Path); ap.add_argument('--output',type=Path)
 a=ap.parse_args(); rows=list(csv.DictReader(a.record.open())); result={'status':'NOT_RUN_OR_REJECTED','stage_pass':False,'hardware_authorization':False}
 try:
  if len(rows)<20: raise ValueError('fewer than 20 samples')
  materials={r['material'] for r in rows}
  if len(materials)!=1 or next(iter(materials)) not in TARGET: raise ValueError('record must contain one PLA or PET run')
  mat=next(iter(materials)); targ=TARGET[mat]
  if not rows[0].get('lot_id') or not rows[0].get('drying_record'): raise ValueError('lot/drying record missing')
  start=n(rows[0]['screw_rpm'])
  if not 8.0<=start<=10.0: raise ValueError('start screw rpm outside 8-10')
  cooked=[]
  prev_t=-1.0; prev_mass=-1.0
  for i,r in enumerate(rows):
   if not all(r.get(k,'').strip() for k in ('operator','reviewer','raw_evidence_path')): raise ValueError(f'sample {i} provenance incomplete')
   t=n(r['elapsed_s']); mass=n(r['cumulative_mass_g'])
   if t<=prev_t or mass<prev_mass: raise ValueError('time/mass not monotonic')
   prev_t,prev_mass=t,mass
   temps=[n(r[k]) for k in ('zone1_c','zone2_c','zone3_c','die_c')]
   temp_ok=all(abs(v-target)<=5 for v,target in zip(temps,targ))
   x,y,u=n(r['diameter_x_mm']),n(r['diameter_y_mm']),n(r['diameter_u95_mm'])
   if u<0: raise ValueError('negative diameter U95')
   mean=(x+y)/2; oval=abs(x-y)
   torque=n(r['gearbox_torque_nm']); tu=n(r['gearbox_torque_u95_nm'])
   if tu<0: raise ValueError('negative torque U95')
   hazard=any(yes(r[k]) for k in ('leak','pressure_symptom','guard_contact'))
   stable=yes(r['stable_candidate']) and temp_ok and u<=0.03 and oval<=0.05 and not hazard and not yes(r['torque_trip'])
   if mat=='PET': stable=stable and torque+tu<8.0
   cooked.append({'index':i,'elapsed_s':t,'mass_g':mass,'mean_d':mean,'ovality':oval,'u95':u,'torque':torque,'torque_u95':tu,'stable':stable})
  found=None
  for s in range(len(cooked)-19):
   w=cooked[s:s+20]
   if all(q['stable'] for q in w):
    mean_d=sum(q['mean_d'] for q in w)/20
    if abs(mean_d-1.75)<=0.05:
     found=(s,w,mean_d); break
  if not found: raise ValueError('no 20-consecutive-sample stable window')
  s,w,mean_d=found; dt=w[-1]['elapsed_s']-w[0]['elapsed_s']; dm=w[-1]['mass_g']-w[0]['mass_g']
  if dt<=0 or dm<0: raise ValueError('invalid stable throughput interval')
  throughput=dm/dt*3600.0
  result={'status':'NUMERIC_RECORD_CHECK_PASS','material':mat,'stage':('P10' if mat=='PLA' else 'P11'),'stage_pass':False,'hardware_authorization':False,'stable_window_start_index':s,'stable_window_end_index':s+19,'mean_diameter_mm':mean_d,'mean_error_mm':abs(mean_d-1.75),'max_ovality_mm':max(q['ovality'] for q in w),'max_u95_mm':max(q['u95'] for q in w),'max_torque_plus_u95_nm':max(q['torque']+q['torque_u95'] for q in w),'stable_throughput_g_h':throughput,'note':'Independent physical review and explicit stage release remain required.'}
 except (ValueError,KeyError,TypeError) as e:
  result={'status':'NOT_RUN_OR_REJECTED','stage_pass':False,'hardware_authorization':False,'reason':str(e)}
 text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'; print(text,end='')
 if a.output: a.output.write_text(text)
 raise SystemExit(0 if result['status']=='NUMERIC_RECORD_CHECK_PASS' else 2)
if __name__=='__main__': main()
