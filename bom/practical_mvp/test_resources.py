"""Prevent budget claims from becoming hardware acceptance."""
import copy,json,unittest
from pathlib import Path
from resource_budget import calculate
from build_plan import read_csv
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads((HERE/'policy.json').read_text())
        self.rows=read_csv(ROOT/'exports/final/print/print_manifest.csv')
        self.power=json.loads((ROOT/'cad/parameters/baseline.json').read_text())['power']
    def run_calc(self):return calculate(self.policy,self.rows,self.power)
    def test_actual_masses(self):
        out=self.run_calc();self.assertEqual(out['material_g'],{'ABS':209.11,'PLA':712.33})
        self.assertEqual(out['abs_unallocated_after_reserve_g'],190.89)
    def test_rating_is_not_new_limit(self):
        p=self.run_calc()['power'];self.assertEqual(p['controller_cap_w'],500)
        self.assertEqual(p['extrusion_phase_w'],490);self.assertEqual(p['shredding_phase_w'],477)
        self.assertFalse(p['physical_output_verified'])
    def test_second_supply_rejected(self):
        self.policy['psu']['double_count_as_second_psu']=True
        with self.assertRaises(ValueError):self.run_calc()
    def test_no_automatic_800w_limit(self):
        self.policy['psu']['controller_continuous_limit_w']=800
        with self.assertRaises(ValueError):self.run_calc()
    def test_no_free_ac_power_credit(self):
        self.policy['ptc']['selected_for_mvp']=True
        with self.assertRaises(ValueError):self.run_calc()
    def test_low_abs_stock_not_pass(self):
        self.policy['housing']['available_abs_g']=300
        self.assertEqual(self.run_calc()['status'],'MATERIAL_BUDGET_EXCEEDED')
    def test_material_relabel_rejected(self):
        self.policy['housing']['abs_part_ids'].append('PPR-C01')
        with self.assertRaises(ValueError):self.run_calc()
    def test_missing_slicing_rejected(self):
        self.rows[0]['slicer_status']='NOT_RUN'
        with self.assertRaises(ValueError):self.run_calc()
    def test_negative_or_nan_mass_rejected(self):
        for value in ('-1','nan','inf'):
            self.rows[0]['slicer_mass_total_g']=value
            with self.assertRaises(ValueError):self.run_calc()
    def test_overload_rejected(self):
        self.power['heater_peak_w']=700
        with self.assertRaises(ValueError):self.run_calc()
    def test_no_mutation_or_physical_pass(self):
        before=copy.deepcopy((self.policy,self.rows,self.power));out=self.run_calc()
        self.assertEqual(before,(self.policy,self.rows,self.power))
        self.assertEqual(out['machine_release'],'HOLD')
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResourceTests))
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'physical_validation':'NOT_RUN'}
    (HERE/'resource_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
