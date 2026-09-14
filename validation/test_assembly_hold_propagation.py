"""미검증 체결품이 숫자 토크를 갖더라도 조립 합격/후속 진행을 차단한다."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'release'))
import build_final_documents as documents


def main():
    rows = {r['step_number']:r for r in documents.assembly_rows()}
    assert {n for n,r in rows.items() if any('HOLD' in (value or '') for value in r.values())} == {'2','7','10','12','13'}
    assert 'GGM_SH_Mount' in rows['7']['part_ids_quantity'] and 'GGM_SH_Jackshaft' in rows['7']['part_ids_quantity']
    assert 'GGM_SH_CouplingGuard' in rows['8']['part_ids_quantity'] and 'GGM_SH_Mount' not in rows['8']['part_ids_quantity']
    assert 'GGM_EX_Mount' in rows['12']['part_ids_quantity']
    assert '8.8–9.3 N·m' in rows['7']['inspection_method'] or 'P3 current/torque/protection evidence' in rows['7']['inspection_method']
    serialized = str(rows)
    for stale in ('DRV-F01P', 'donor adapter', '14 N·m', '18 N·m', '22 N·m'):
        assert stale not in serialized, stale
    assert '470±0.8 mm' in rows['2']['clearance_tolerance'] and '700±0.8 mm' in rows['2']['clearance_tolerance']
    assert 'U95_A+U95_B≤1.0 mm' in rows['2']['pass_fail']
    assert 'SYS-12' in rows['10']['fasteners'] and rows['10']['pass_fail'].startswith('HOLD')
    assert rows['13']['pass_fail'].startswith('HOLD')
    assert 'cold axial free travel≥1.50 mm' in rows['11']['clearance_tolerance']
    assert 'hot calculated endplay' not in rows['11']['clearance_tolerance']
    assert 'SYS-04: 1.5 N·m' in rows['13']['torque']
    assert 'M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1' in rows['13']['fasteners']
    assert 'physical receipt/leak/first thermal cycle remains NOT_RUN' in rows['13']['inspection_method']
    assert '진행 금지' in rows['13']['next_prerequisite']
    die_joint = next(j for j in documents.fasteners() if j['joint_id'] == 'SYS-04')
    assert die_joint['specification'].startswith('M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1')
    assert die_joint['torque_Nm'] == '1.5'
    assert die_joint['verification_state'] == 'RELEASED_DIGITAL_PHYSICAL_NOT_RUN'
    assert 'engagement6.82-7.40' in die_joint['inspection']
    assert 'thread-bottom clearance0.60-1.18' in die_joint['inspection']
    joints = [dict(j) for j in documents.fasteners()]
    joint = next(j for j in joints if j['joint_id']=='SYS-01')
    joint['verification_state'] = 'HOLD_SYNTHETIC_UNQUALIFIED'
    joint['inspection'] = 'synthetic reason must reach manual'
    with patch.object(documents,'fasteners',return_value=joints):
        held = {r['step_number']:r for r in documents.assembly_rows()}['2']
    assert held['pass_fail'].startswith('HOLD')
    assert '진행 금지' in held['next_prerequisite']
    assert 'synthetic reason must reach manual' in held['inspection_method']
    assert rows['2']['inspection_method'] != held['inspection_method']
    released = [dict(j) for j in joints]
    for entry in released:
        if documents.fastener_step_number(entry) == 2:
            entry['verification_state'] = 'RELEASED_DIGITAL_PHYSICAL_NOT_RUN'
    with patch.object(documents, 'fasteners', return_value=released):
        baseline = {r['step_number']: r for r in documents.assembly_rows()}['2']
    assert not baseline['pass_fail'].startswith('HOLD')
    assert baseline['pass_fail'] != held['pass_fail']
    print('ASSEMBLY_HOLD_PROPAGATION_PASS SYS04_DIGITAL_PASS_PHYSICAL_HOLD')


if __name__ == '__main__':
    main()
