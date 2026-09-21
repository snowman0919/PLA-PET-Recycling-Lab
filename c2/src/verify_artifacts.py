"""Check active C2 evidence and CAD integrity without authorizing hardware."""
from pathlib import Path
import json,hashlib
from costing import evaluate
from performance import ALLOWED_EVIDENCE,candidate_hashes,evidence_inventory,training_gate
R=Path(__file__).resolve().parents[1]
req=json.loads((R/'design/requirements.json').read_text())
s=json.loads((R/'results/summary.json').read_text())
cad=json.loads((R/'results/cad_validation.json').read_text())
records=json.loads((R/'experiments/performance_records.json').read_text())
candidates=json.loads((R/'results/s2_candidates.json').read_text())
hashes=candidate_hashes(candidates)
inventory=evidence_inventory(records,R/'experiments',hashes,req['revision'])
qualified=[r for r in records if r.get('evidence_type') in ALLOWED_EVIDENCE]
gate=training_gate(qualified,R/'experiments',geometry_hashes=hashes,expected_cad_revision=req['revision'])
cost=evaluate(json.loads((R/'bom/cost_ledger.json').read_text()),req['user_constraints']['budget_soft_limit_KRW'])
assert req['user_constraints']['shredder_motor_count']==1
assert req['user_constraints']['motor_M1_frozen'] is False
assert req['user_constraints']['budget_soft_limit_KRW']==100000
assert s['actual_dem_runs']==inventory['actual_dem_runs']
assert s['actual_physical_tests']==inventory['actual_physical_tests']
assert s['candidates']==257 and s['geometrically_feasible']==106
assert s['diverse_dem_designs']==48 and s['material_specific_dem_jobs']==144
assert s['unknown_cost_lines']==len(cost['unknown_cost_lines'])
assert s['total_confirmed_cost_KRW']==cost['total_KRW']
assert json.loads((R/'results/cost_status.json').read_text())==cost
assert json.loads((R/'results/performance_gate.json').read_text())==gate
assert len(cad['records'])==12 and cad['module_instances']==12
assert not cad['static_overlaps_in_module']
for rec in cad['records']:
 p=R/'cad'/(rec['part_id']+'.step')
 assert p.is_file(),str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'],str(p)
 assert rec['valid'] and rec['solids']==1 and rec['step_relative_volume_error']<1e-7
for stage in ('procurement','fabrication','energization'):
 assert cad[stage]=='HOLD' and req['deployment'][stage]=='HOLD'
models=[json.loads((R/file).read_text()) for file in
        ['results/model_run/training_status.json','results/mlp_run/training_status.json']]
assert s['performance_models_trained']==sum(p['trained'] is True for p in models)
for p in models:
 assert (p['trained'] and p['status']=='RESEARCH_TRAINING_COMPLETE_NOT_RELEASED' and gate['status']=='READY_FOR_GROUP_SPLIT') or (not p['trained'] and p['status']=='BLOCKED_PERFORMANCE_DATA')
coupon=json.loads((R/'results/coupon_fe_summary.json').read_text())
assert coupon['status']=='UNCALIBRATED_COUPON_SOLVER_RUN_NOT_SHREDDING_PERFORMANCE'
assert coupon['qualification']=='DID_RUN_SOLVER; DID_NOT_RUN_DEM_OR_PHYSICAL_TEST; NOT_A_PERFORMANCE_LABEL'
assert len(coupon['runs'])==9 and set(coupon['relative_force_change_8_to_16'])=={'PLA','PET','TPU'}
for run in coupon['runs']:
 name=f"{run['material'].lower()}_{run['elements']}"
 assert run['return_code']==0 and run['reaction_force_N']>0
 for suffix,key in (('.inp','input_sha256'),('.dat','dat_sha256'),('.frd','frd_sha256')):
  path=R/'experiments/raw/coupon_fe'/(name+suffix)
  assert path.is_file(),str(path)
  assert hashlib.sha256(path.read_bytes()).hexdigest()==run[key],str(path)
p5=json.loads((R/'results/p5_thermal_control.json').read_text())
assert p5['status']=='UNCALIBRATED_DIGITAL_SENSITIVITY_AND_CONTROL_LOGIC_ONLY'
assert p5['cad_capacity_basis']['status']=='CAD_VOLUME_DERIVED_ASSUMED_DENSITY_CP_NOT_MEASURED_MASS'
assert len(p5['thermal_cases'])==s['p5_thermal_cases']==9
assert len(p5['control_cases'])==s['p5_control_cases']==7
assert all(abs(x['energy_balance_residual_J']) < 1e-5 for x in p5['thermal_cases'])
thermal={(x['material'],x['airflow']):x for x in p5['thermal_cases']}
for material in ('PLA','PET','TPU'):
 assert thermal[(material,'FAN_FAILED_NATURAL_ONLY')]['peak_node_C'][2] > thermal[(material,'CLEAN_FILTER_ASSUMED')]['peak_node_C'][2]
states={x['name']:(x['state'],x['reason']) for x in p5['control_cases']}
assert states['normal_reference']==('RUN',None)
assert states['buffer_full']==('BUFFER_HOLD',None)
assert states['high_current_low_rpm']==('FAULT','JAM_NO_AUTOMATIC_REVERSE')
assert states['hardware_overtemp_open']==('FAULT','HARDWARE_OVERTEMP_CHAIN_OPEN')
assert set(p5['did_not_run']) >= {'physical_thermal_test','firmware_flash','energization'}
assert s['p5_status']=='DIGITAL_SENSITIVITY_COMPLETE_PHYSICAL_QUALIFICATION_HOLD'
print('C2 numerical/CAD artifact contracts passed. Hardware gates remain HOLD.')
