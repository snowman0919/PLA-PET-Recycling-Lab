"""뜨거운 구역에 가려진 변동과 fuse 플래그만의 허위 합격을 거부한다."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulation/openmodelica/postprocess'))
import summarize_results as s

keys = 'power1 power2 power3 powerDie netFlowGPH screwRPM meltPressureMPa rawPressureMPa motorTorque motorCurrent ready driveTripped fuseBlown reliefState reliefFlowGPH'.split()
def check(oscillate=False,fused=False,power=0):
    rows = [{**dict.fromkeys(keys,0),'T1':200.,'T2':240.,'T3':250.,'Tdie':290.,
             'fuseBlown':int(fused),'power1':power} for _ in range(100)]
    if oscillate:
        rows[-1]['T1']=210.
    item, failures = {},[]
    s.evaluate_thermal('MOSFETStuckOn',rows,item,failures)
    return failures,item
assert not check()[0]
assert 'stuck-on equilibrium/fuse' in check(oscillate=True)[0]
assert 'stuck-on equilibrium/fuse' in check(fused=True,power=100)[0]
assert not check(fused=True)[0] and check(fused=True)[1]['fuse_power_cut_verified']
print('THERMAL_PROTECTION_EVIDENCE_PASS')
