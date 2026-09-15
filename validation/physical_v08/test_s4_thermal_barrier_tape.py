#!/usr/bin/env python3
import csv,hashlib,importlib.util,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('s4',HERE/'analyze_s4_thermal_barrier_tape.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
def write(p,fields,rows):
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def make(run):
 e=run/'evidence.txt';e.write_text('synthetic S4 tape evidence');digest=hashlib.sha256(e.read_bytes()).hexdigest();rel=str(e.relative_to(ROOT))
 with (HERE/'templates/s4_thermal_barrier_tape_smoke.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f));fields=list(rows[0])
 numeric={'datasheet_continuous_service_rating':(220,0),'coupon_interface_peak':(185,1),'coupon_outer_surface_peak':(70,1),'qualification_hot_dwell':(605,1),'post_cool_edge_lift_max':(.5,.05)}
 for r in rows:
  m=r['metric']
  if m in numeric:r['value'],r['u95']=map(str,numeric[m]);r['instrument_id']='SYN';r['calibration_ref']='SYN-CAL'
  else:r['value']='YES' if m in M.BOOL_TRUE else 'NO';r['instrument_id']='N/A';r['calibration_ref']='N/A'
  r['measured_at']='2026-09-11T14:30:00+09:00';r['operator']='TECH-A';r['reviewer']='REVIEW-B';r['evidence_path']=rel;r['sha256']=digest
 p=run/'s4.csv';write(p,fields,rows);return p
class S4Test(unittest.TestCase):
 def test_pass_stays_non_authorizing(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   r=M.evaluate(make(Path(td)));self.assertEqual(r['status'],'S4_THERMAL_BARRIER_TAPE_SMOKE_PASS');self.assertTrue(r['p9_tape_smoke_prerequisite']);self.assertFalse(r['installation_authorized']);self.assertFalse(r['heater_energization_authorized'])
 def test_rejects_rating_margin(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   p=make(Path(td));
   with p.open(encoding='utf-8') as f: rows=list(csv.DictReader(f));fields=list(rows[0]);
   next(r for r in rows if r['metric']=='coupon_interface_peak')['value']='195';write(p,fields,rows);self.assertIn('qualification temperature window',M.evaluate(p)['reason'])
 def test_rejects_280c_as_continuous_basis(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   p=make(Path(td));
   with p.open(encoding='utf-8') as f: rows=list(csv.DictReader(f));fields=list(rows[0]);
   next(r for r in rows if r['metric']=='datasheet_continuous_service_rating')['value']='280';write(p,fields,rows);self.assertIn('fixed 220 C',M.evaluate(p)['reason'])
 def test_rejects_smoke(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   p=make(Path(td));
   with p.open(encoding='utf-8') as f: rows=list(csv.DictReader(f));fields=list(rows[0]);
   next(r for r in rows if r['metric']=='visible_smoke')['value']='YES';write(p,fields,rows);self.assertIn('visible_smoke',M.evaluate(p)['reason'])
 def test_rejects_wrong_surface(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   p=make(Path(td));
   with p.open(encoding='utf-8') as f: rows=list(csv.DictReader(f));fields=list(rows[0]);
   next(r for r in rows if r['metric']=='direct_heater_barrel_die_wrap_used')['value']='YES';write(p,fields,rows);self.assertIn('direct_heater',M.evaluate(p)['reason'])
if __name__=='__main__':unittest.main()
