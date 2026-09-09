"""Catalogue selection checks, not hardware approval."""
from pathlib import Path
import json,math,unittest
from select_motors import conservative_catalog_nm,output
HERE=Path(__file__).resolve().parent
class SelectionTests(unittest.TestCase):
    def setUp(self):self.r=json.loads((HERE/'motor_selection.json').read_text())
    def test_kgf_conversion_not_rounded_up(self):self.assertAlmostEqual(conservative_catalog_nm(10,100),9.80665)
    def test_selected_quantities(self):self.assertEqual([r['quantity'] for r in self.r['selected']],[1,1])
    def test_shredder_ratio(self):self.assertEqual(self.r['selected'][0]['output']['rpm'],16)
    def test_screw_ratio(self):self.assertEqual(self.r['selected'][1]['output']['rpm'],20)
    def test_rated_demand_covered(self):self.assertTrue(all(r['matches_declared_demand_torque'] for r in self.r['selected']))
    def test_price_includes_gear(self):self.assertEqual(self.r['total_motor_and_gear_price_krw'],2*(53840+47410))
    def test_no_controller_purchase(self):self.assertEqual(self.r['protection_integration']['additional_driver_purchase'],0)
    def test_unknown_controllers_excluded(self):self.assertEqual(self.r['protection_integration']['unidentified_controllers'],'EXCLUDED_FROM_BASELINE')
    def test_old_fuse_not_reused(self):self.assertFalse(self.r['protection_integration']['legacy_fuse_reuse_allowed'])
    def test_mismatched_current_not_written(self):self.assertIsNone(self.r['protection_integration']['new_trip_current_a'])
    def test_combined_corner_not_hidden(self):self.assertFalse(self.r['joint_corner_covered_by_selected_extruder'])
    def test_no_fake_full_power(self):self.assertTrue(self.r['power_integration']['full_360w_heat_plus_rated_motor_exceeds_500w'])
    def test_no_physical_or_purchase_claim(self):
        self.assertEqual(self.r['physical_validation'],'NOT_RUN');self.assertFalse(self.r['purchase_performed'])
    def test_reduction_does_not_create_power(self):self.assertAlmostEqual(output(2,30,3,.85)['shaft_power_w'],output(2,30,5,.85)['shaft_power_w'])
    def test_bad_efficiency(self):
        with self.assertRaises(ValueError):output(2,30,3,1.1)
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelectionTests))
    (HERE/'selection_tests.json').write_text(json.dumps({'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'physical_validation':'NOT_RUN'},indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
