#!/usr/bin/env python3
import csv,hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/f'{name}.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

P5=load('analyze_p5_records')
P5REL=load('validate_p5_stage_release')

def write_csv(path,fieldnames,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,lineterminator='\n'); w.writeheader(); w.writerows(rows)

def synthetic_packet(dst, bad_barrel_case=False):
    ev=dst/'evidence'; ev.mkdir()
    evidence={}
    for name,text in [('supplier.pdf','synthetic supplier capability'),('metrology.csv','synthetic metrology evidence'),('cert.pdf','synthetic certificate evidence')]:
        path=ev/name; path.write_text(text); evidence[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    with (HERE/'templates/p5_supplier_capability.csv').open(newline='',encoding='utf-8') as f: cap=list(csv.DictReader(f))
    for r in cap:
        if r['gate_class']=='HARD_GATE' or r['id']=='CAP-10':
            r['supplier_response']='YES'; r['evidence_path']=str((dst/'evidence/supplier.pdf').relative_to(HERE.parents[1])); r['sha256']=evidence['supplier.pdf']
        if r['id']=='CAP-10': r['proposed_deviation']='NONE'
        if r['id']=='CAP-11': r['supplier_response']='UNAVAILABLE'
    write_csv(dst/'p5_supplier_capability.csv',cap[0].keys(),cap)

    with (HERE/'templates/p5_coupon_measurements.csv').open(newline='',encoding='utf-8') as f: ms=list(csv.DictReader(f))
    nominal={
      ('EX-CPN-SCR','length'):48.0,('EX-CPN-SCR','flight_OD'):15.91,('EX-CPN-SCR','pitch'):16.0,
      ('EX-CPN-SCR','land'):1.60,('EX-CPN-SCR','root_OD'):10.88,('EX-CPN-SCR','end_perpendicularity'):0.01,
      ('EX-CPN-SCR','flight_OD_Ra'):0.60,('EX-CPN-SCR','root_flank_Ra'):1.20,
      ('EX-CPN-BAR','length'):60.0,('EX-CPN-BAR','OD'):34.0,('EX-CPN-BAR','bore_ID'):16.21,
      ('EX-CPN-BAR','end_perpendicularity'):0.01,('EX-CPN-BAR','bore_Ra'):0.60,
    }
    for r in ms:
        r['value']=str(nominal[(r['part_id'],r['characteristic'])]); r['u95_or_mpe']='0.001'
        if r['characteristic'].endswith('_Ra'): r['u95_or_mpe']='0.02'
        r['temperature_c']='20'; r['instrument_id']='SYN-MET'; r['calibration_ref']='SYN-CAL'
        r['measured_at']='2026-09-10T10:00:00+09:00'; r['operator']='SYNTHETIC'
        r['evidence_path']=str((dst/'evidence/metrology.csv').relative_to(HERE.parents[1])); r['sha256']=evidence['metrology.csv']
    write_csv(dst/'p5_coupon_measurements.csv',ms[0].keys(),ms)

    with (HERE/'templates/p5_coupon_certificates.csv').open(newline='',encoding='utf-8') as f: cert=list(csv.DictReader(f))
    vals={
      ('EX-CPN-SCR','material_grade'):'SCM440 JIS G4105',('EX-CPN-BAR','material_grade'):'SCM440 JIS G4105',
      ('EX-CPN-SCR','heat_lot_id'):'SYN-HEAT-S',('EX-CPN-BAR','heat_lot_id'):'SYN-HEAT-B',
      ('EX-CPN-SCR','qt_core_hardness'):'30',('EX-CPN-BAR','qt_core_hardness'):'30',
      ('EX-CPN-SCR','surface_hardness'):'1000',('EX-CPN-BAR','surface_hardness'):'1000',
      ('EX-CPN-SCR','final_effective_case_depth'):'0.40',('EX-CPN-BAR','nitride_process_case_target'):'0.40',
      ('EX-CPN-BAR','final_effective_case_depth'):'0.254' if bad_barrel_case else '0.30',
      ('EX-CPN-BAR','final_hone_removed_on_diameter'):'0.06',
    }
    for r in cert:
        r['value']=vals[(r['part_id'],r['characteristic'])]
        r['u95_or_mpe']='0.005' if r['unit']=='mm' else ('1' if r['unit'] in {'HRC','HV0.3'} else '')
        r['method_or_standard']='SYN-METHOD' if r['characteristic'] not in {'material_grade','heat_lot_id','final_hone_removed_on_diameter'} else ''
        r['certificate_id']='SYN-CERT'; r['provider']='SYN-LAB'; r['evidence_path']=str((dst/'evidence/cert.pdf').relative_to(HERE.parents[1])); r['sha256']=evidence['cert.pdf']
    # Text rows do not use numeric uncertainty.
    for r in cert:
        if r['characteristic'] in {'material_grade','heat_lot_id'}: r['u95_or_mpe']=''
    write_csv(dst/'p5_coupon_certificates.csv',cert[0].keys(),cert)

class P5ExecutionTest(unittest.TestCase):
    def run_packet(self,bad=False):
        td=tempfile.TemporaryDirectory(dir=HERE); d=Path(td.name); synthetic_packet(d,bad)
        proc=subprocess.run(['python3',str(HERE/'analyze_p5_records.py'),str(d)],capture_output=True,text=True)
        return td,proc
    def test_p5_synthetic_pass(self):
        td,proc=self.run_packet(False)
        try:
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            out=json.loads(proc.stdout); self.assertEqual(out['status'],'NUMERIC_RECORD_CHECK_PASS')
            self.assertFalse(out['full_part_order_authorized']); self.assertFalse(out['stage_p5_pass'])
            self.assertAlmostEqual(out['measurements']['clearance_min_nominal_mm'],0.30,places=6)
        finally: td.cleanup()
    def test_stage_release_revalidates_exact_records(self):
        td=tempfile.TemporaryDirectory(dir=HERE); d=Path(td.name)
        try:
            synthetic_packet(d,False)
            result=P5.evaluate(d); self.assertEqual(result['status'],'NUMERIC_RECORD_CHECK_PASS')
            result_path=d/'p5_result.json'; result_path.write_text(json.dumps(result,indent=2)+'\n')
            release={
                'stage':'P5','status':'PASS','release_scope':'P5_COUPON_COMPLETE_P6_REVIEW_ONLY',
                'approved_by':'ENGINEER-A','independent_reviewer':'REVIEWER-B','reviewed_at':'2026-09-10T17:30:00+09:00',
                'records_dir':str(d.relative_to(ROOT)),'p5_result':result_path.name,
                'p5_result_sha256':hashlib.sha256(result_path.read_bytes()).hexdigest(),
                'p6_entry_review':True,'action_state':'HOLD','machine_release':'HOLD'}
            release_path=d/'p5_stage_release.json'; release_path.write_text(json.dumps(release,indent=2)+'\n')
            checked=P5REL.validate(release_path); self.assertEqual(checked['status'],'P5_STAGE_RELEASE_VALIDATED')
            self.assertTrue(checked['p6_entry_prerequisite']); self.assertEqual(checked['action_state'],'HOLD')
            release['p5_result_sha256']='0'*64; release_path.write_text(json.dumps(release,indent=2)+'\n')
            with self.assertRaises(ValueError): P5REL.validate(release_path)
        finally: td.cleanup()
    def test_barrel_case_uncertainty_rejects_edge(self):
        td,proc=self.run_packet(True)
        try:
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('final_effective_case_depth below limit',proc.stdout)
        finally: td.cleanup()
if __name__=='__main__': unittest.main()
