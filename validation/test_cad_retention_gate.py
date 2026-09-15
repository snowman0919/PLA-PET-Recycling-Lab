"""접촉만으로 미검증 축방향 고정 성능을 합격 처리하지 않는다."""
from final_v08_cad import release_status

assert release_status(False,'PASS')=='FAIL'
assert release_status(False,'HOLD')=='FAIL'
for missing in ('HOLD','FAIL','',None):
    assert release_status(True,missing)=='HOLD'
assert release_status(True,'PASS')=='PASS'
print('CAD_RETENTION_GATE_PASS')
