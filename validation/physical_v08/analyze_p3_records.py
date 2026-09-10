#!/usr/bin/env python3
"""Numeric-only P3 analyzer. It never authorizes or controls hardware."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

def read(p):
    with p.open(newline='',encoding='utf-8') as fh: return list(csv.DictReader(fh))
def num(v):
    if v is None or str(v).strip()=='': raise ValueError('blank physical field')
    x=float(v)
    if not math.isfinite(x): raise ValueError('non-finite value')
    return x
def fit_line(points):
    xm=sum(x for x,y in points)/len(points); ym=sum(y for x,y in points)/len(points)
    den=sum((x-xm)**2 for x,y in points)
    if den<=0: raise ValueError('zero ADC span')
    a=sum((x-xm)*(y-ym) for x,y in points)/den; b=ym-a*xm
    return a,b
def current_fit(rows,axis):
    q=[r for r in rows if r['axis']==axis]
    pts=[(num(r['adc_count']),num(r['reference_current_a'])) for r in q]
    if len(pts)<5 or max(y for x,y in pts)<4.6: raise ValueError(axis+' current coverage')
    a,b=fit_line(pts)
    err=max(abs(a*x+b-y)+num(r['u95_a']) for (x,y),r in zip(pts,q))
    if not 0<a<0.1 or err>0.10: raise ValueError(axis+' current fit')
    return a,b,err
def torque(force,uf,arm,uarm):
    t=force*arm/1000.0
    u=math.hypot((arm/1000.0)*uf, force*(uarm/1000.0))
    return t,u
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('dir',type=Path); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); d=a.dir
    names=['p3_current_sensor_calibration.csv','p3_no_load.csv','p3_torque_map.csv','p3_pin_release.csv']
    if any(not (d/n).exists() for n in names): raise SystemExit('missing P3 record file')
    cur,nl,tm,pins=[read(d/n) for n in names]
    try:
        cf={ax:current_fit(cur,ax) for ax in ('SH','EX')}
        idle={}
        for ax in ('SH','EX'):
            rows=[r for r in nl if r['axis']==ax]
            if len(rows)<3: raise ValueError(ax+' no-load repeats')
            vals=[num(r['reference_current_a']) for r in rows]
            rpms=[num(r['output_rpm']) for r in rows]
            if ax=='EX' and any(r['direction']!='F' for r in rows): raise ValueError('EX reverse forbidden')
            idle[ax]=sum(vals)/len(vals)
        maps={}
        for ax in ('SH','EX'):
            rows=[r for r in tm if r['axis']==ax]; cooked=[]
            for r in rows:
                F,uF,arm,uarm=num(r['force_n']),num(r['u95_force_n']),num(r['arm_mm']),num(r['u95_arm_mm'])
                T,uT=torque(F,uF,arm,uarm); rpm=num(r['rpm']); adc=num(r['adc_count']); aa,bb,ce=cf[ax]
                I=aa*adc+bb; x=max(0,abs(I)-idle[ax])
                if not (10<=rpm<=40 if ax=='SH' else 5<=rpm<=20): raise ValueError(ax+' rpm envelope')
                if ax=='EX' and r['direction']!='F': raise ValueError('EX reverse torque point')
                cooked.append((r,x,T,uT))
            fit=[x for x in cooked if x[0]['subset']=='fit']; hold=[x for x in cooked if x[0]['subset']=='holdout']
            if len(fit)<5 or len(hold)<3: raise ValueError(ax+' fit/holdout count')
            den=sum(x*x for r,x,t,u in fit)
            k=sum(x*t for r,x,t,u in fit)/den
            if max(t for r,x,t,u in cooked)<7.5: raise ValueError(ax+' torque coverage')
            if ax=='SH' and {r['direction'] for r,x,t,u in hold}!={'F','R'}: raise ValueError('SH holdout directions')
            bound=max(abs(k*x-t)+u+k*cf[ax][2] for r,x,t,u in hold)
            if bound>0.40: raise ValueError(ax+' holdout >0.40 Nm')
            maps[ax]={'gearbox_nm_per_amp':k,'holdout_error_bound_nm':bound,'no_load_current_a':idle[ax]}
        groups={('SH','F'):[],('SH','R'):[],('EX','F'):[]}
        for r in pins:
            key=(r['axis'],r['direction'])
            if key not in groups: raise ValueError('invalid pin axis/direction')
            T,u=torque(num(r['force_n']),num(r['u95_force_n']),num(r['arm_mm']),num(r['u95_arm_mm']))
            if T-u<8.8 or T+u>9.3: raise ValueError(r['coupon_id']+' release interval')
            if r['free_after_release'].strip().upper() not in {'YES','PASS','TRUE'} or r['hub_key_damage'].strip().upper() not in {'NO','NONE','0'}: raise ValueError(r['coupon_id']+' post-release condition')
            groups[key].append((T,u))
        if any(len(v)<3 for v in groups.values()): raise ValueError('pin replicate count')
        result={'status':'NUMERIC_RECORD_CHECK_PASS','hardware_authorization':False,'stage_p3_pass':False,'current_fit':{ax:{'amps_per_adc':cf[ax][0],'offset_a':cf[ax][1],'max_error_with_u95_a':cf[ax][2]} for ax in cf},'torque_map':maps,'pin_groups':{f'{k[0]}-{k[1]}':len(v) for k,v in groups.items()},'note':'Use inspection.py with authenticated raw evidence and explicit physical authorization for actual P3 state.'}
    except (ValueError,KeyError,ZeroDivisionError) as e:
        result={'status':'NOT_RUN_OR_REJECTED','hardware_authorization':False,'stage_p3_pass':False,'reason':str(e)}
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output: a.output.write_text(text)
    print(text,end='')
    raise SystemExit(0 if result['status']=='NUMERIC_RECORD_CHECK_PASS' else 2)
if __name__=='__main__': main()
