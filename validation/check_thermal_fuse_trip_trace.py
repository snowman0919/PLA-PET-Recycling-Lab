"""실행된 Modelica 퓨즈 trace의 차단·래치 검사. 물리 퓨즈 검증 아님."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation/openmodelica/postprocess'))
import summarize_results as s

s.RAW = ROOT/'analysis/final_validation/results/v0.8'
output = s.RAW/'thermal_fuse_trip_trace.json'
output.write_text('{"status":"INCOMPLETE","physical_validation_state":"NOT_RUN"}\n')
rows = s.load('ThermalFuseTripProbe')
assert rows[0]['time']==0 and rows[-1]['time']==6000
assert all(0<=b['time']-a['time']<=1.000001 for a,b in zip(rows,rows[1:]))
index = next(i for i,r in enumerate(rows) if r['fuseBlown']>.5)
assert index>0 and any(r['power3']>99 for r in rows[:index])
assert all(r['fuseBlown']>.5 and abs(r['duty3']-1)<1e-9 for r in rows[index:])
assert all(abs(r[k])<1e-9 for r in rows[index:] for k in ('power1','power2','power3','powerDie'))
assert max(rows[-1][k] for k in ('T1','T2','T3','Tdie'))<299
files = [Path(__file__),Path(s.__file__),s.RAW/'ThermalFuseTripProbe_res.csv',
         ROOT/'simulation/openmodelica/scripts/check_thermal_fuse_trip.mos',
         ROOT/'simulation/openmodelica/PLA_PET_Recycler/Systems/ThermalExtruderSystem.mo']
result = {'status':'HOLD','trace_checks':'PASS','physical_validation_state':'NOT_RUN',
          'assumed_ambient_c':200,'trip_time_s':rows[index]['time'],
          'final_max_temperature_c':max(rows[-1][k] for k in ('T1','T2','T3','Tdie')),
          'scope':'Ideal 300C threshold and instantaneous fuse isolation only; no real fuse location, delay, tolerance, interrupt rating or thermal contact qualification',
          'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
output.write_text(json.dumps(result,indent=2)+'\n')
print('THERMAL_FUSE_TRACE_HOLD',result['trip_time_s'],result['final_max_temperature_c'])
