"""Check numerical artifact honesty and recorded CAD roundtrip, never authorize hardware."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
req=json.loads((R/'design/requirements.json').read_text())
s=json.loads((R/'results/summary.json').read_text())
cad=json.loads((R/'results/cad_validation.json').read_text())
assert req['user_constraints']['shredder_motor_count']==1
assert req['user_constraints']['motor_M1_frozen'] is False
assert req['user_constraints']['budget_soft_limit_KRW']==100000
assert s['actual_dem_runs']==s['actual_physical_tests']==s['performance_models_trained']==0
assert s['candidates']==257 and s['geometrically_feasible']==106
assert s['diverse_dem_designs']==48 and s['material_specific_dem_jobs']==144
assert s['unknown_cost_lines']==125 and s['total_confirmed_cost_KRW'] is None
assert len(cad['records'])==12 and cad['module_instances']==12
assert not cad['static_overlaps_in_module']
for rec in cad['records']:
 p=R/'cad'/(rec['part_id']+'.step')
 assert p.is_file(),str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'],str(p)
 assert rec['valid'] and rec['solids']==1 and rec['step_relative_volume_error']<1e-7
for stage in ('procurement','fabrication','energization'):
 assert cad[stage]=='HOLD' and req['deployment'][stage]=='HOLD'
for file in ['results/model_run/training_status.json','results/mlp_run/training_status.json']:
 p=json.loads((R/file).read_text())
 assert p['trained'] is False and p['status']=='BLOCKED_PERFORMANCE_DATA'
print('C2 numerical/CAD artifact contracts passed. Hardware gates remain HOLD.')
