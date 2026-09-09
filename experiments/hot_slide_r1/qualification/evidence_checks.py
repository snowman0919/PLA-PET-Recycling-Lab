"""Evidence reduction, not certificate authentication or hardware approval."""
from pathlib import Path, PurePosixPath
import hashlib, json, math, re

class EvidenceError(ValueError): pass

def number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise EvidenceError('Non-finite/non-numeric value')
    return float(value)

def interval(value,uncertainty):
    v,u=number(value),number(uncertainty)
    if u<0: raise EvidenceError('Negative uncertainty')
    return v-u,v+u

def artifact(root,record):
    if not isinstance(record,dict): raise EvidenceError('Artifact record required')
    name=record.get('path'); digest=record.get('sha256')
    if not isinstance(name,str) or '\\' in name or not name: raise EvidenceError('Invalid path')
    rel=PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or str(rel)!=name: raise EvidenceError('Unsafe path')
    path=(Path(root)/name).resolve()
    if not path.is_relative_to(Path(root).resolve()): raise EvidenceError('Outside evidence root')
    if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest): raise EvidenceError('Invalid digest')
    try: data=path.read_bytes()
    except OSError as exc: raise EvidenceError('Missing artifact') from exc
    if not data or hashlib.sha256(data).hexdigest()!=digest: raise EvidenceError('Artifact hash mismatch')
    return path

def material_issues(record, requirement, evidence_root):
    """Requires lot/condition/thickness/orientation/temperature-specific values."""
    issues=[]
    if not isinstance(record,dict): return ['Material record missing']
    if record.get('evidence_kind')!='LOT_TEST_REPORT': issues.append('Typical data is not a lot report')
    for key in ('lot_id','material','condition','product_form'):
        if record.get(key)!=requirement.get(key) or not record.get(key): issues.append('Mismatch '+key)
    try:
        if abs(number(record.get('thickness_mm'))-number(requirement['thickness_mm']))>.001:
            issues.append('Wrong product thickness')
        artifact(evidence_root,record.get('raw_report'))
    except EvidenceError as exc: issues.append(str(exc))
    if record.get('final_heat_treatment_dimensions_verified') is not True:
        issues.append('Final heat-treatment dimensions missing')
    tests=record.get('tests',[])
    if not isinstance(tests,list): tests=[]
    for temperature in requirement['temperatures_c']:
        for direction in requirement['orientations']:
            candidates=[]
            for test in tests:
                if not isinstance(test,dict) or test.get('orientation')!=direction: continue
                try:
                    t=number(test.get('temperature_c')); u=number(test.get('temperature_uncertainty_c'))
                    if u<0 or abs(t-temperature)+u>requirement['test_temperature_tolerance_c']: continue
                    if test.get('property')!='RP0.2' or test.get('basis')!='TEST_VALUE_WITH_UNCERTAINTY': continue
                    low,_=interval(test.get('yield_mpa'),test.get('yield_uncertainty_mpa'))
                    candidates.append(low)
                except EvidenceError: continue
            if not candidates or min(candidates)<requirement['minimum_yield_mpa']:
                issues.append(f'Missing/insufficient yield at {temperature}C {direction}')
    return sorted(set(issues))

def friction_summary(rows):
    """Signed, direction-matched tare subtraction; lateral load is not normal force."""
    if not isinstance(rows,list) or len(rows)<4: raise EvidenceError('Insufficient friction samples')
    output=[]; directions=set(); last=-math.inf
    for row in rows:
        t=number(row.get('time_s')); direction=row.get('direction')
        if t<0 or t<=last or isinstance(direction,bool) or direction not in (-1,1):
            raise EvidenceError('Invalid time/direction')
        last=t; directions.add(direction)
        if row.get('phase') not in ('BREAKAWAY','STEADY'): raise EvidenceError('Phase missing')
        if row.get('tare_direction')!=direction or row.get('tare_condition_matches') is not True:
            raise EvidenceError('Tare not matched to direction/condition')
        force=direction*(number(row.get('pull_force_n'))-number(row.get('tare_force_n')))
        force_u=number(row.get('force_uncertainty_n')); tare_u=number(row.get('tare_uncertainty_n'))
        if force_u<0 or tare_u<0: raise EvidenceError('Negative individual uncertainty')
        u=force_u+tare_u
        low,high=interval(force,u)
        if low<0: raise EvidenceError('Drag sign/uncertainty inconsistent')
        item={'time_s':t,'direction':direction,'phase':row['phase'],
              'drag_interval_n':[low,high],'mu_status':'NOT_IDENTIFIABLE'}
        if 'normal_force_sum_n' in row:
            if row.get('normal_force_basis')!='INDEPENDENT_CONTACT_NORMAL_SUM':
                raise EvidenceError('Lateral/assumed normal load cannot identify friction coefficient')
            nlo,nhi=interval(row['normal_force_sum_n'],row.get('normal_force_uncertainty_n'))
            if nlo<=0: raise EvidenceError('Normal force uncertainty includes zero')
            item.update({'mu_status':'INTERVAL_FROM_DECLARED_MEASUREMENTS',
                         'mu_interval':[low/nhi,high/nlo]})
        output.append(item)
    if directions!={-1,1}: raise EvidenceError('Both directions required')
    for d in directions:
        if {r['phase'] for r in output if r['direction']==d}!={'BREAKAWAY','STEADY'}:
            raise EvidenceError('Both friction phases required in each direction')
    return {'status':'REDUCED_DATA_ONLY','machine_release':'HOLD',
            'measurement_authenticity':'REQUIRES_INDEPENDENT_REVIEW',
            'breakaway_upper_n':max(r['drag_interval_n'][1] for r in output if r['phase']=='BREAKAWAY'),
            'steady_upper_n':max(r['drag_interval_n'][1] for r in output if r['phase']=='STEADY'),
            'samples':output}

def review_packet(packet, root, expected_geometry):
    """Presence/integrity review cannot authenticate documents or authorize hardware."""
    base={'machine_release':'HOLD','hardware_authorization':'NOT_GRANTED'}
    if not isinstance(packet,dict) or packet.get('performed') is not True:
        return {**base,'status':'NOT_RUN','issues':['No performed measurements']}
    issues=[]
    if packet.get('evidence_kind')!='MEASURED': issues.append('Not measured evidence')
    if packet.get('geometry_sha256')!=expected_geometry: issues.append('Wrong geometry')
    if not isinstance(expected_geometry,str) or not re.fullmatch('[0-9a-f]{64}',expected_geometry):
        issues.append('Invalid expected geometry identity')
    required=('raw_trace','calibration_report','temperature_trace','alignment_report',
              'preload_relaxation_report','material_report','operator_approval')
    for name in required:
        try: artifact(root,packet.get(name))
        except EvidenceError as exc: issues.append(name+': '+str(exc))
    for key in ('specimen_ids','lot_id','heat_treatment_condition','surface_condition','run_id'):
        if not packet.get(key): issues.append('Missing '+key)
    return {**base,'status':'INTEGRITY_COMPLETE_REVIEW_REQUIRED' if not issues else 'EVIDENCE_INCOMPLETE',
            'issues':issues,'authenticity':'NOT_ESTABLISHED_BY_SOFTWARE',
            'scope':'Document binding only; numerical protocol, lab applicability and engineer approval remain separate'}
