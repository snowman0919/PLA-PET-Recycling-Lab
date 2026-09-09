"""불완전/비유한 이력과 잘못된 고장 주입을 거부하고 과거 요약을 무효화한다."""
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/final_validation'))
import summarize_die_pilot_thermal as screen


def main():
    source = ROOT/'analysis/final_validation/results/v0.8'
    for filename, field, value in (('PilotPET_res.csv','T1','nan'),
                                   ('PilotPET_res.csv','fuseBlown','2'),
                                   ('PilotPETDieOpen_res.csv','powerDie','60')):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            out = root/'analysis/final_validation/results/v0.8'
            out.mkdir(parents=True)
            for path in source.glob('PilotPET*_res.csv'):
                shutil.copyfile(path,out/path.name)
            path = out/filename
            with path.open() as stream:
                reader = csv.DictReader(stream)
                fields, rows = reader.fieldnames,list(reader)
            rows[0][field] = value
            with path.open('w',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=fields)
                writer.writeheader(); writer.writerows(rows)
            report = out/'die_pilot_thermal.json'
            report.write_text('{"status":"HOLD","cases":["stale"]}')
            with patch.object(screen,'ROOT',root):
                try:
                    screen.main(out)
                except AssertionError:
                    pass
                else:
                    raise AssertionError('invalid trajectory accepted')
            assert json.loads(report.read_text())['status']=='INCOMPLETE'
            assert 'cases' not in json.loads(report.read_text())
    print('DIE_PILOT_THERMAL_INVALID_EVIDENCE_REJECTION_PASS cases=3')


if __name__ == '__main__':
    main()
