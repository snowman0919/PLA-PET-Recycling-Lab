"""Software checks of units and rated-point comparison, not motor tests."""
import json, math, unittest
from pathlib import Path
from check_motors import operating_point, envelope, KGF_CM_TO_NM
HERE = Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_units(self):
        self.assertAlmostEqual(20 * KGF_CM_TO_NM, 1.96133)
    def test_shredder_chain(self):
        p = operating_point(20 * KGF_CM_TO_NM, 100, 2.5, .85)
        self.assertEqual(p['output_rpm'], 40)
        self.assertAlmostEqual(p['output_torque_nm'], 4.16782625)
    def test_extruder_three_to_one(self):
        p = operating_point(19 * KGF_CM_TO_NM, 46, 3, .85)
        self.assertAlmostEqual(p['output_rpm'], 46/3)
        self.assertAlmostEqual(p['output_torque_nm'], 4.751321925)
    def test_reduction_preserves_power_less_losses(self):
        self.assertAlmostEqual(operating_point(2, 100, 2, .85)['output_power_w'], operating_point(2, 100, 10, .85)['output_power_w'])
    def test_no_extra_margin(self):
        self.assertTrue(envelope(10, 50, 20, [20,25], 1)['rated_point_can_meet_current_envelope'])
    def test_shredder_even_ideal_is_short(self):
        self.assertFalse(envelope(20*KGF_CM_TO_NM,100,14,[20,40],1)['rated_point_can_meet_current_envelope'])
    def test_extruder_even_ideal_is_short(self):
        self.assertFalse(envelope(19*KGF_CM_TO_NM,46,15,[14,28],1)['rated_point_can_meet_current_envelope'])
    def test_negative(self):
        with self.assertRaises(ValueError): operating_point(-1,10,2,.85)
    def test_impossible_efficiency(self):
        with self.assertRaises(ValueError): operating_point(1,10,2,1.1)
    def test_nonfinite(self):
        with self.assertRaises(ValueError): operating_point(1,math.nan,2,.85)
    def test_bad_interval(self):
        with self.assertRaises(ValueError): envelope(1,20,2,[30,10],.85)
    def test_vendor_fields_not_measured(self):
        source = json.loads((HERE/'source_rows.json').read_text())
        self.assertEqual(source['exact_aliexpress_order_identity'],'NOT_CONFIRMED')
        self.assertEqual(source['physical_validation'],'NOT_RUN')
    def test_power_column_not_shaft_power(self):
        p = operating_point(19*KGF_CM_TO_NM,46,1,1)
        self.assertLess(p['output_power_w'],10)
    def test_stock_quantity_not_invented(self):
        record = json.loads((HERE/'user_reply.json').read_text())
        self.assertIsNone(record['stock']['BTS7960']['quantity'])
        self.assertEqual(record['motor_ownership'],'NOT_CONFIRMED_BY_PRODUCT_SCREENSHOT')
if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    report = {'status':'PASS' if result.wasSuccessful() else 'FAIL', 'count':result.testsRun,
              'failures':len(result.failures), 'errors':len(result.errors),
              'kind':'SOFTWARE_RATED_POINT_CHECKS_ONLY','physical_validation':'NOT_RUN'}
    (HERE/'test_result.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
