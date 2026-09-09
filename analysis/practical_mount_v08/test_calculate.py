"""Small, decision-relevant regression tests; no physical measurements."""
import json, math, unittest
from pathlib import Path
from calculate import gap, growth, thrust

class PracticalAuditTests(unittest.TestCase):
    def test_pressure_units(self):
        self.assertAlmostEqual(thrust(6.,16.22),1239.7748770270393)
    def test_force_is_not_twelve_tonnes(self):
        self.assertLess(thrust(6.,16.22)/9806.65,.13)
    def test_actual_guide_span(self):
        self.assertAlmostEqual(growth(102.,17e-6,280.),.48552)
    def test_front_travel_is_different_quantity(self):
        self.assertAlmostEqual(growth(272.,17e-6,280.),1.29472)
        self.assertGreater(growth(272.,17e-6,280.),growth(102.,17e-6,280.))
    def test_front_nominal_gap(self):
        self.assertAlmostEqual(gap(34.6,34.,17e-6,300.,12e-6,20.),.43816)
    def test_rear_interference_not_waived(self):
        self.assertLess(gap(34.1,34.,17e-6,300.,12e-6,20.),0)
    def test_counterbore_interference_not_waived(self):
        self.assertLess(gap(44.1,44.,17e-6,300.,12e-6,20.),0)
    def test_warmed_support_changes_gap(self):
        self.assertGreater(gap(34.1,34.,12.3e-6,270.,12e-6,100.),0)
    def test_invalid_inputs(self):
        for value in (True,0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                thrust(value,16.22)
    def test_no_physical_pass(self):
        result=json.loads(Path(__file__).with_name('result.json').read_text())
        self.assertEqual(result['physical_validation'],'NOT_RUN')
        self.assertEqual(result['machine_release'],'HOLD')

if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PracticalAuditTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    output={'status':'PASS' if result.wasSuccessful() else 'FAIL',
            'count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'kind':'SYNTHETIC_SOFTWARE_TESTS_ONLY','physical_validation':'NOT_RUN'}
    Path(__file__).with_name('test_result.json').write_text(json.dumps(output,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
