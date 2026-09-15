"""Focused arithmetic and trace regressions; never a physical qualification."""
import copy,json,math,unittest
from pathlib import Path
from run_study import independent,scenarios
from verify_study import validate
HERE=Path(__file__).resolve().parent
class SizingTests(unittest.TestCase):
    def setUp(self): self.report=json.loads((HERE/'results.json').read_text())
    def test_all_bound_outputs(self): self.assertTrue(validate(self.report))
    def test_six_base_cases(self): self.assertEqual(len(scenarios()),6)
    def test_recommended_rpm(self):
        refs=[independent(p) for n,p in scenarios() if n.endswith('recommended')]
        self.assertAlmostEqual(refs[0]['screw_rpm'],100/6.209)
        self.assertAlmostEqual(refs[1]['screw_rpm'],100/5.418)
    def test_cut_area_is_total(self):
        p=dict(scenarios()[1][1]);self.assertAlmostEqual(independent(p)['shred_peak_nm'],10.344)
    def test_pressure_work_not_hydraulic_power(self):
        p=scenarios()[1][1];self.assertAlmostEqual(independent(p)['pressure_work_component_nm'],3.946326)
    def test_viscosity_scaling(self):
        p=scenarios()[1][1];a=independent(p);b=independent(dict(p,viscosityPaS=2*p['viscosityPaS']))
        self.assertAlmostEqual(b['viscous_component_nm'],2*a['viscous_component_nm'])
    def test_first_ready_is_latched(self): self.assertTrue(all(0<r['ready_s']<1000 for r in self.report['cases']))
    def test_simulation_is_not_physical(self): self.assertEqual(self.report['physical_validation'],'NOT_RUN')
    def test_rms_lower_than_peak(self): self.assertTrue(all(r['shred_rms_nm']<r['closed_form']['shred_peak_nm'] for r in self.report['cases']))
    def test_high_shear_not_normal(self):
        r=next(r for r in self.report['cases'] if r['case']=='PET_recommended_cut_strength_high')
        self.assertAlmostEqual(r['closed_form']['shred_peak_nm'],14.52)
    def test_cold_lock_and_exclusion(self): self.assertTrue(all(r['no_cold_extrusion'] and r['no_mode_overlap'] for r in self.report['cases']))
    def test_missing_case_rejected(self):
        r=copy.deepcopy(self.report);r['cases'].pop()
        with self.assertRaises(ValueError):validate(r)
    def test_stale_source_rejected(self):
        r=copy.deepcopy(self.report);key=next(iter(r['source_sha256']));r['source_sha256'][key]='0'*64
        with self.assertRaises(ValueError):validate(r)
    def test_rms_miss_rejected(self):
        r=copy.deepcopy(self.report);r['cases'][0]['shred_rms_nm']*=.7
        with self.assertRaises(ValueError):validate(r)
    def test_pretended_physical_pass_rejected(self):
        r=copy.deepcopy(self.report);r['physical_validation']='PASS'
        with self.assertRaises(ValueError):validate(r)
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SizingTests))
    result={'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'kind':'MODEL_IMPLEMENTATION_REGRESSION','physical_validation':'NOT_RUN'}
    (HERE/'test_results.json').write_text(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
