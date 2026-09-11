"""A selected probe reference must not be promoted to received hardware."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
note = (ROOT/'exports/thermal/parts/TH-TC-01/drawing_notes.md').read_text()
assert 'Tempco MTA1' in note and 'ungrounded' in note
assert 'NOT_RUN' in note and 'HOLD' in note
assert 'exact MPN assigned after quote' in note
assert 'supplier drawing/insulation/calibration/thermal-response receipt evidence HOLD' in note
assert 'sheath-to-junction insulation verified' not in note
assert 'barrel insertion set to measured blind depth' not in note
print('PROBE_PROCUREMENT_STATE_PASS')
