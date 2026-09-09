"""미검증 체결품이 숫자 토크를 갖더라도 조립 합격/후속 진행을 차단한다."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'release'))
import build_final_documents as documents


def main():
    rows = {r['step_number']:r for r in documents.assembly_rows()}
    assert {n for n,r in rows.items() if any('HOLD' in (value or '') for value in r.values())} == {'7','10','12','13'}
    assert 'SYS-12' in rows['10']['fasteners'] and rows['10']['pass_fail'].startswith('HOLD')
    assert rows['13']['pass_fail'].startswith('HOLD')
    assert 'SYS-04: HOLD' in rows['13']['torque']
    assert 'M4x40 class 10.9' in rows['13']['fasteners']
    assert '4.12–4.80' in rows['13']['inspection_method']
    assert '3.20–3.88' in rows['13']['inspection_method']
    assert 'M4×45' not in rows['13']['fasteners']
    assert '진행 금지' in rows['13']['next_prerequisite']
    die_joint = next(j for j in documents.fasteners() if j['joint_id'] == 'SYS-04')
    assert die_joint['specification'].startswith('M4x40 class 10.9')
    assert die_joint['verification_state'] == 'HOLD_GASKET_AND_HOT_PRELOAD_UNQUALIFIED'
    joints = [dict(j) for j in documents.fasteners()]
    joint = next(j for j in joints if j['joint_id']=='SYS-01')
    joint['verification_state'] = 'HOLD_SYNTHETIC_UNQUALIFIED'
    joint['inspection'] = 'synthetic reason must reach manual'
    with patch.object(documents,'fasteners',return_value=joints):
        held = {r['step_number']:r for r in documents.assembly_rows()}['2']
    assert held['pass_fail'].startswith('HOLD')
    assert '진행 금지' in held['next_prerequisite']
    assert 'synthetic reason must reach manual' in held['inspection_method']
    assert rows['2']['pass_fail'] != held['pass_fail']
    print('ASSEMBLY_HOLD_PROPAGATION_PASS M4x40_bottoming_clear_torque_hold')


if __name__ == '__main__':
    main()
