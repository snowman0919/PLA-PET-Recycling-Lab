"""Review pressureless test records; never operates or approves the machine."""
import json,math,re,sys
from pathlib import Path

def number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def evaluate(record,geometry_sha256,required_yield_mpa):
    issues=[]
    if record.get('performed') is not True:
        return {'status':'NOT_RUN','machine_release':'HOLD','issues':['No performed measurement record']}
    if record.get('evidence_kind')!='MEASURED':issues.append('Not a measured record')
    if record.get('geometry_sha256')!=geometry_sha256:issues.append('Wrong geometry')
    if not re.fullmatch('[0-9a-f]{64}',geometry_sha256):issues.append('Invalid expected geometry hash')
    if record.get('pressure_applied') is not False or record.get('powered_rotation') is not False:issues.append('Outside pressureless stationary scope')
    for name in ('operator','approval_reference','force_calibration_reference','position_calibration_reference','material_certificate_reference'):
        if not isinstance(record.get(name),str) or not record[name].strip():issues.append('Missing '+name)
    if record.get('independent_mechanical_stops_verified') is not True:issues.append('No positive travel stops')
    samples=record.get('samples',[])
    if not isinstance(samples,list) or len(samples)<10:issues.append('At least ten measured samples required');samples=[]
    last=-math.inf;positions=[];hot=False
    keys=('time_s','travel_mm','pull_force_n','radial_load_n','centre_x_mm','centre_y_mm','barrel_c','spring_inner_c','spring_outer_c','spring_face_a_c','spring_face_b_c','temperature_uncertainty_c','endplay_mm','force_uncertainty_n','position_uncertainty_mm')
    for i,row in enumerate(samples):
        if not isinstance(row,dict) or any(not number(row.get(k)) for k in keys):issues.append('Invalid sample '+str(i));continue
        if row['time_s']<last:issues.append('Time reversal')
        last=row['time_s'];positions.append(row['travel_mm'])
        if row['force_uncertainty_n']<0 or row['position_uncertainty_mm']<0:issues.append('Negative uncertainty')
        if abs(row['pull_force_n'])+row['force_uncertainty_n']>300:issues.append('Breakaway/drag exceeds prototype bound')
        if abs(row['radial_load_n'])+row['force_uncertainty_n']>25:issues.append('Radial load exceeds model scope')
        if math.hypot(row['centre_x_mm'],row['centre_y_mm'])+row['position_uncertainty_mm']>.10:issues.append('Centreline drift exceeds test criterion')
        if abs(row['travel_mm'])>3:issues.append('Travel stop bound exceeded')
        temps=[row[k] for k in ('barrel_c','spring_inner_c','spring_outer_c')]
        if min(temps)<20 or max(temps)>300:issues.append('Temperature outside analysis bounds')
        if row['temperature_uncertainty_c']<0 or abs(row['spring_face_a_c']-row['spring_face_b_c'])+2*row['temperature_uncertainty_c']>10:issues.append('Through-thickness thermal gradient outside test bound')
        temps += [row['spring_face_a_c'],row['spring_face_b_c']]
        if min(temps)<20 or max(temps)>300:issues.append('Face temperature outside analysis bounds')
        is_hot=max(temps)>40;hot|=is_hot
        lo,hi=(.10,.50) if is_hot else (.25,.35)
        if row['endplay_mm']-row['position_uncertainty_mm']<lo or row['endplay_mm']+row['position_uncertainty_mm']>hi:issues.append('Stack axial clearance outside acceptance')
    if not any(isinstance(r,dict) and number(r.get('radial_load_n')) and abs(r['radial_load_n'])>=24 for r in samples):issues.append('No near-envelope lateral-load measurement')
    if not positions or max(positions)-min(positions)<2:issues.append('Insufficient measured travel')
    if hot and (not isinstance(record.get('heating_approval_reference'),str) or not record.get('heating_approval_reference','').strip() or record.get('independent_thermal_cutoff_verified') is not True or record.get('metal_shield_verified') is not True):issues.append('Hot-test authorization/protection incomplete')
    if hot and (not number(record.get('peak_ramp_rate_c_per_min')) or record.get('peak_ramp_rate_c_per_min',999)>2 or not record.get('ramp_trace_reference')):issues.append('Qualified slow-ramp trace missing')
    supplied=record.get('certified_yield_mpa_at_peak_temperature')
    if not number(required_yield_mpa) or required_yield_mpa<=0 or not number(supplied) or supplied<required_yield_mpa:issues.append('Material strength evidence below required model bound')
    residual=record.get('post_cooldown_residual_offset_mm')
    if not number(residual) or residual<0 or residual>.02:issues.append('Permanent-set check missing or failed')
    return {'status':'MEASURED_DATA_WITHIN_TEST_PROTOCOL' if not issues else 'TEST_REVIEW_REQUIRED','machine_release':'HOLD','scope':'Protocol screening only; not fatigue, pressure or machine qualification','issues':sorted(set(issues))}

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('usage: validate_physical_test.py RECORD_JSON GEOMETRY_SHA256 REQUIRED_YIELD_MPA')
    record=json.loads(Path(sys.argv[1]).read_text())
    result=evaluate(record,sys.argv[2],float(sys.argv[3]));print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='MEASURED_DATA_WITHIN_TEST_PROTOCOL' else 1)
