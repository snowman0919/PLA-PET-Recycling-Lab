"""불완전/성긴 시계열이 이전 검증 summary를 남기지 않아야 한다."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation/openmodelica/postprocess'))
import summarize_chain_rerun as summary

with tempfile.TemporaryDirectory() as folder:
    output = Path(folder)/'summary.json'
    for times in ([0,17],[0,18],[0,-1,18]):
        output.write_text('{"status":"HOLD","cases":{"stale":{}}}')
        with patch.object(sys,'argv',['summary',folder,str(output)]), patch.object(
                summary.base,'load',return_value=[{'time':t} for t in times]):
            try:
                summary.main()
            except AssertionError:
                pass
            else:
                raise AssertionError('invalid time coverage accepted')
        result = json.loads(output.read_text())
        assert result['status']=='INCOMPLETE' and 'cases' not in result
print('GROUP_RERUN_TIME_EVIDENCE_PASS')
