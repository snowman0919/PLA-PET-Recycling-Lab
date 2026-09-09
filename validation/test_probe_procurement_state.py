"""생성된 센서 구매 후보를 실측·검증 완료품으로 표시하지 않는다."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
note = (ROOT/'exports/thermal/parts/TH-TC-01/drawing_notes.md').read_text()
assert 'UNSELECTED' in note and 'NOT_RUN' in note
assert 'CAD envelope is not purchased geometry' in note
assert 'insulation verification REQUIRED' in note
assert 'sheath-to-junction insulation verified' not in note
assert 'barrel insertion set to measured blind depth' not in note
print('PROBE_PROCUREMENT_STATE_PASS')
