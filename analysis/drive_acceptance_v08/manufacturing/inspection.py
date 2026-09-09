"""Offline record checks only. Never enables hardware or executes a test."""
from pathlib import Path
import json,math,hashlib,datetime
H=Path(__file__).resolve().parent
R=H.parents[2]

def number(v):
    if type(v) not in (int,float) or not math.isfinite(v): raise ValueError('finite numeric value required')
    return float(v)
def interval(row,low,high,unit):
    if row.get('unit')!=unit: raise ValueError('unit mismatch')
    v,u=number(row['value']),number(row['u95'])
    if u<0 or v-u<low or v+u>high: raise ValueError('uncertainty interval outside requirement')
    return v

def evidence(record):
    if record.get('kind')!='PHYSICAL_MEASUREMENT' or record.get('performed') is not True: raise ValueError('not a physical record')
    for field in ('operator','instrument_id','instrument_calibration_ref','measured_at','part_serial'):
        if not isinstance(record.get(field),str) or not record[field].strip(): raise ValueError('missing '+field)
    datetime.datetime.fromisoformat(record['measured_at'].replace('Z','+00:00'))
    files=record.get('raw_files',{})
    if not files: raise ValueError('missing raw measurement evidence')
    for name,digest in files.items():
        p=(R/name).resolve()
        if not p.is_relative_to(R) or not p.is_file(): raise ValueError('invalid evidence path')
        if len(digest)!=64 or hashlib.sha256(p.read_bytes()).hexdigest()!=digest: raise ValueError('stale raw evidence')

RECEIPT={'voltage_v':(24,24,'V'),'shaft_diameter':(11.982,12.000,'mm'),
 'shaft_projection':(31.80,32.20,'mm'),'bolt_pcd':(103.90,104.10,'mm'),
 'output_offset':(17.90,18.10,'mm'),'case_width':(89,91,'mm'),'rear_length':(208,210,'mm')}
ALIGN={'coupling_offset':(0,.030,'mm'),'coupling_angle':(0,.050,'deg'),
 'sprocket_plane_offset':(0,.250,'mm'),'shaft_tir':(0,.030,'mm'),
 'sprocket_tir':(0,.100,'mm'),'coupling_face_gap':(.30,.50,'mm'),
 'jack_endplay':(.05,.20,'mm'),'radial_bearing_endplay':(.05,.20,'mm')}

def receipt(data):
    seen=set()
    for axis,gear in (('SH','K9G75C'),('EX','K9G150C')):
        r=data[axis]; evidence(r)
        if r.get('motor_model')!='K9DG60N2' or r.get('gear_model')!=gear: raise ValueError('wrong motor/gear')
        if r['part_serial'] in seen: raise ValueError('duplicate motor identity')
        seen.add(r['part_serial'])
        for key,limits in RECEIPT.items(): interval(r['readings'][key],*limits)
    return {'motor_records':2,'basis':'project receiving limits; not manufacturer guarantees'}

def alignment(data):
    evidence(data)
    for key,limits in ALIGN.items(): interval(data['readings'][key],*limits)
    return {'checks':len(ALIGN),'assembly_revision':data.get('assembly_revision')}

def pins(data):
    evidence(data); rows=data['samples']; groups={('SH','F'):[],('SH','R'):[],('EX','F'):[]}
    seen=set()
    for row in rows:
        key=(row['axis'],row['direction'])
        if key not in groups or row['coupon_id'] in seen: raise ValueError('coupon identity/direction')
        seen.add(row['coupon_id']); groups[key].append(interval(row['release_torque'],8.8,9.3,'N.m'))
        if not row.get('material_lot') or not row.get('drawing_revision'): raise ValueError('coupon binding missing')
    if any(len(v)<3 for v in groups.values()): raise ValueError('three independent coupons per permitted direction required')
    return {'coupons':len(rows),'minimum_nm':min(v for a in groups.values() for v in a),'maximum_nm':max(v for a in groups.values() for v in a)}
def fit_line(points):
    n=len(points)
    if n<3: raise ValueError('insufficient calibration points')
    xm=sum(x for x,y in points)/n; ym=sum(y for x,y in points)/n
    xx=sum((x-xm)**2 for x,y in points)
    if xx<=1e-10: raise ValueError('zero calibration span')
    slope=sum((x-xm)*(y-ym) for x,y in points)/xx
    return slope,ym-slope*xm

def currents(data):
    output={}
    for axis in ('SH','EX'):
        rec=data[axis]; evidence(rec)
        if rec.get('current_location')!='motor_lead' or rec.get('units')!={'current':'A','torque':'N.m','speed':'rpm','adc':'count'}: raise ValueError('calibration units/location')
        adc=rec['adc_samples']
        if any(number(r['u95_a'])<0 for r in adc): raise ValueError('negative current uncertainty')
        points=[(number(r['adc']),number(r['reference_a'])) for r in adc]
        if len(points)<5 or max(y for x,y in points)<4.6: raise ValueError('ADC coverage insufficient')
        if any(x<=8 or x>=1015 or abs(y)>6 for x,y in points): raise ValueError('saturated ADC or overcurrent record')
        a,b=fit_line(points)
        if not 0<a<.1: raise ValueError('invalid current gain')
        err=max(abs(a*x+b-y)+number(r['u95_a']) for (x,y),r in zip(points,adc))
        if err>.10: raise ValueError('current calibration error')
        no_load=rec['no_load_a']
        if len(no_load)<3 or any(number(v)<0 for v in no_load): raise ValueError('no-load samples missing')
        idle=sum(number(v) for v in no_load)/len(no_load)
        if not 0<=idle<4.6: raise ValueError('invalid no-load current')
        samples=rec['torque_samples']; ids=[r['sample_id'] for r in samples]
        if len(ids)!=len(set(ids)): raise ValueError('reused load sample')
        train=[r for r in samples if r['subset']=='fit']; check=[r for r in samples if r['subset']=='holdout']
        if len(train)<5 or len(check)<3: raise ValueError('independent holdout required')
        rows=[]
        for row in samples:
            measured_i=a*number(row['adc'])+b; torque=number(row['reference_nm'])
            if abs(measured_i)>6 or torque<0 or torque>9.3: raise ValueError('outside calibration envelope')
            if number(row['u95_nm'])<0 or row['direction'] not in ('F','R'): raise ValueError('invalid torque uncertainty/direction')
            if axis=='EX' and row['direction']=='R': raise ValueError('extruder reverse not approved')
            rpm=number(row['rpm'])
            if not (10<=rpm<=40 if axis=='SH' else 5<=rpm<=20): raise ValueError('wrong output-axis speed')
            rows.append((row,max(0,abs(measured_i)-idle),torque))
        den=sum(x*x for r,x,y in rows if r['subset']=='fit')
        if den<=0: raise ValueError('zero load span')
        k=sum(x*y for r,x,y in rows if r['subset']=='fit')/den
        if not 0<k<10: raise ValueError('invalid torque gain')
        if max(y for r,x,y in rows)<7.5: raise ValueError('torque coverage below protection region')
        directions={r['direction'] for r in check}
        if axis=='SH' and directions!={'F','R'}: raise ValueError('forward/reverse holdout coverage')
        bound=max(abs(k*x-y)+number(r['u95_nm'])+k*err for r,x,y in rows if r['subset']=='holdout')
        if bound>.4: raise ValueError('current-to-torque bound exceeds0.4Nm')
        output[axis]={'amps_per_adc':a,'zero_adc':-b/a,'gearbox_nm_per_amp':k,
                      'no_load_current_a':idle,'holdout_error_bound_nm':bound,
                      'write_firmware':False,'profile_enabled':False}
    return output

def inspect(packet):
    report={'physical_test_executed_by_this_tool':False,'hardware_authorization':'NOT_GRANTED',
      'machine_release':'HOLD','authenticity':'NOT_ESTABLISHED_BY_PARSER','domains':{}}
    needed=['control/ggm_drive_contract.json',str((H/'drawing_contract.json').relative_to(R))]
    bindings=packet.get('design_sha256',{})
    binding_ok=all(bindings.get(k)==hashlib.sha256((R/k).read_bytes()).hexdigest() for k in needed)
    for name,fn in [('receipt',receipt),('alignment',alignment),('protection_pin',pins),('current_calibration',currents)]:
        row=packet.get(name,{})
        if row.get('performed') is not True:
            report['domains'][name]={'status':'NOT_RUN'}; continue
        if not binding_ok:
            report['domains'][name]={'status':'REJECTED','reason':'missing or stale design binding'}; continue
        try: report['domains'][name]={'status':'NUMERIC_RECORD_CHECK_PASS','result':fn(row['data'])}
        except (KeyError,ValueError,TypeError,ZeroDivisionError) as e:
            report['domains'][name]={'status':'REJECTED','reason':str(e)}
    return report

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description='Offline evidence arithmetic only; no physical actions')
    ap.add_argument('packet',type=Path); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    result=inspect(json.loads(args.packet.read_text()))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v['status'] for k,v in result['domains'].items()}))
    raise SystemExit(2 if any(v['status']=='REJECTED' for v in result['domains'].values()) else 0)
