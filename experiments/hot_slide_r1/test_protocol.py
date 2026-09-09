"""Synthetic validator regression tests; none are physical test evidence."""
import copy,json
from pathlib import Path
from validate_physical_test import evaluate
H='a'*64

def fixture():
    return {'performed':True,'evidence_kind':'MEASURED','geometry_sha256':H,
        'pressure_applied':False,'powered_rotation':False,'operator':'SYNTHETIC',
        'approval_reference':'SYNTHETIC','force_calibration_reference':'SYNTHETIC',
        'position_calibration_reference':'SYNTHETIC','material_certificate_reference':'SYNTHETIC',
        'certified_yield_mpa_at_peak_temperature':1200,
        'independent_mechanical_stops_verified':True,'post_cooldown_residual_offset_mm':.005,
        'samples':[{'time_s':i,'travel_mm':-1+2*i/9,'pull_force_n':20,'radial_load_n':24,
                    'centre_x_mm':.01,'centre_y_mm':.02,'barrel_c':25,'spring_inner_c':25,
                    'spring_outer_c':25,'spring_face_a_c':25,'spring_face_b_c':25,'temperature_uncertainty_c':.5,'endplay_mm':.30,'force_uncertainty_n':.2,
                    'position_uncertainty_mm':.005} for i in range(10)]}

def main():
    results=[]
    def check(name,data,good=False):
        value=evaluate(data,H,900)
        assert (value['status']=='MEASURED_DATA_WITHIN_TEST_PROTOCOL')==good,(name,value)
        assert value['machine_release']=='HOLD'
        results.append({'name':name,'status':'PASS','observed':value['status']})
    check('valid_synthetic_cold_record',fixture(),True)
    for name,key,value in [('not_run','performed',False),('fixture_is_not_measured','evidence_kind','SIMULATION'),('wrong_hash','geometry_sha256','b'*64),('pressure','pressure_applied',True),('rotation','powered_rotation',True),('no_approval','approval_reference',''),('weak_material','certified_yield_mpa_at_peak_temperature',700),('no_stops','independent_mechanical_stops_verified',False),('residual_set','post_cooldown_residual_offset_mm',.04),('empty_samples','samples',[])]:
        f=fixture();f[key]=value;check(name,f)
    for name,key,value in [('nonfinite','pull_force_n',float('nan')),('excess_force','pull_force_n',301),('excess_radial','radial_load_n',26),('axis_drift','centre_x_mm',.11),('overtravel','travel_mm',4),('too_hot','barrel_c',301),('cold_stack_clamped','endplay_mm',0),('negative_uncertainty','force_uncertainty_n',-1)]:
        f=fixture();f['samples'][3][key]=value;check(name,f)
    f=fixture();f['samples'][2]['time_s']=-1;check('time_reversal',f)
    f=fixture()
    for r in f['samples']:r['travel_mm']=0
    check('no_travel',f)
    f=fixture()
    for r in f['samples']:r['radial_load_n']=0
    check('no_lateral_proof',f)
    f=fixture();f['samples'][3]['barrel_c']=150;check('heat_without_approval',f)
    f['heating_approval_reference']='SYNTHETIC';f['independent_thermal_cutoff_verified']=True;f['metal_shield_verified']=True
    f['peak_ramp_rate_c_per_min']=1.5;f['ramp_trace_reference']='SYNTHETIC'
    check('synthetic_hot_protocol_record',f,True)
    f['heating_approval_reference']='';check('empty_hot_approval',f)
    f=fixture();f['samples'][3]['spring_face_a_c']=100;check('through_face_gradient',f)
    output={'status':'PASS','kind':'SYNTHETIC_SOFTWARE_TESTS_ONLY','count':len(results),'tests':results,'physical_validation_state':'NOT_RUN'}
    (Path(__file__).parent/'protocol_test_results.json').write_text(json.dumps(output,indent=2))
    print('PROTOCOL_UNIT_TESTS_PASS',len(results))
if __name__=='__main__':main()
