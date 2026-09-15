"""명목 센서 구멍 계산만으로 제작 합격을 주장하지 않는다."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'calculations'))
from run_engineering import thermocouple_bore_screening

bore = thermocouple_bore_screening()
assert bore['selected_status']=='HOLD' and bore['physical_status']=='NOT_RUN'
assert all(row['status']=='HOLD' for row in bore['candidates'])
assert bore['candidates'][-1]['screening_status']=='PASS'
saved = json.loads((ROOT/'simulation/engineering_summary.json').read_text())
assert saved['thermocouple_bore']==bore
line = next(line for line in (ROOT/'calculations/engineering_report.md').read_text().splitlines() if line.startswith('- thermocouple bore:'))
assert 'HOLD' in line and 'PASS' not in line
print('BORE_SCREENING_HOLD_PASS')
