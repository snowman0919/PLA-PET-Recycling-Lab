"""Geometry evidence and drive arithmetic regressions; not physical tests."""
from pathlib import Path
import unittest,json,hashlib,copy
from engineering import calculate
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'exports/final/drive_ggm_v08'

def verify(report):
    if report['status']!='NEW_DRIVE_CLEARANCE_PASS' or report['review']['new_interference']:raise ValueError('New collision')
    if report['machine_release']!='HOLD' or report['physical_validation']!='NOT_RUN':raise ValueError('False physical claim')
    required={'GGM-FULL-ASM.step','GGM_SH_Mount.step','GGM_EX_Mount.step','Screw-GGM.step','ThrustPlate-GGM.step'}
    if not required.issubset({r['file'] for r in report['exports']}):raise ValueError('Missing core output')
    for r in report['exports']:
        if r['status']!='REIMPORT_PASS' or hashlib.sha256((OUT/r['file']).read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Stale export')
    for p,h in report['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('Stale source')
    return True

class Tests(unittest.TestCase):
    def setUp(self):self.c=json.loads((ROOT/'control/ggm_drive_contract.json').read_text())
    def test_real_export_set(self):self.assertTrue(verify(json.loads((OUT/'manifest.json').read_text())))
    def test_no_false_physics(self):
        r=json.loads((OUT/'manifest.json').read_text());r['physical_validation']='PASS'
        with self.assertRaises(ValueError):verify(r)
    def test_missing_part(self):
        r=json.loads((OUT/'manifest.json').read_text());r['exports']=[]
        with self.assertRaises(ValueError):verify(r)
    def test_changed_hash(self):
        r=json.loads((OUT/'manifest.json').read_text());r['exports'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):verify(r)
    def test_envelope(self):
        r=json.loads((OUT/'manifest.json').read_text())['exports'][0]
        self.assertTrue(all(a<=b for a,b in zip(r['bbox_mm'],[500,750,1000])))
    def test_reaction_balance(self):
        r=calculate(self.c);self.assertAlmostEqual(sum(r['bearing_reactions_n']),r['chain_radial_load_n'])
    def test_moment_balance(self):
        r=calculate(self.c);self.assertAlmostEqual(r['bearing_reactions_n'][1]*.030,r['chain_radial_load_n']*.013)
    def test_local_strength_bound(self):self.assertGreater(calculate(self.c)['conditional_shaft_factor'],2)
    def test_protection_order(self):self.assertTrue(calculate(self.c)['protection_order_pass'])
    def test_old_fuse_rejected(self):
        self.c['protection']['mechanical_release_acceptance_nm']=[10.35,11]
        self.assertFalse(calculate(self.c)['protection_order_pass'])
    def test_power_reservation(self):self.assertEqual(calculate(self.c)['peak_dc_power_w'],495)
    def test_pin_blank_not_authorized(self):self.assertFalse(calculate(self.c)['pin_blank_installable'])
    def test_source_cache(self):
        folder=HERE/'raw/source';m=json.loads((folder/'manifest.json').read_text())
        self.assertTrue(all(hashlib.sha256((folder/(r['name']+'.brep')).read_bytes()).hexdigest()==r['brep_sha256'] for r in m['objects']))
    def test_receipt_default(self):
        text=(ROOT/'firmware/ggm_drive_v08/ggm_commissioning.h').read_text()
        self.assertIn('RECEIPT_LIMITER_CURRENT_AND_WIRING_VERIFIED = false',text)
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    (HERE/'test_result.json').write_text(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'physical_validation':'NOT_RUN','status':'PASS' if r.wasSuccessful() else 'FAIL'},indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
