"""Sourcing-policy regressions, not structural or physical qualification."""
import copy, json, unittest
from pathlib import Path
from build_plan import build, route
HERE = Path(__file__).resolve().parent
class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((HERE/'policy.json').read_text())
        self.row = {'part_id':'PPR-C01','description':'cover','make_or_buy':'MAKE_3D_PRINT'}
        self.prints = [{'part_id':'PPR-C01','name':'cover','quantity':'1','material':'PLA'}]
        self.frame = [{'part_id':'FR-08','stock':'20x40 aluminum profile','quantity':'2'}]
    def test_pla_default_does_not_invent_new_slicing(self):
        _,p,_ = build([self.row],self.prints,self.frame,self.policy)
        self.assertEqual(p[0]['target_material'],'PLA')
        self.assertIn('MATCH_NOT_PHYSICALLY',p[0]['state'])
    def test_2040_retained_without_section_swap(self):
        _,_,f = build([self.row],self.prints,self.frame,self.policy)
        self.assertEqual(f[0]['change_state'],'RETAIN_SECTION_STOCK_LENGTH_PENDING')
        self.assertEqual(f[0]['stock'],'20x40 aluminum profile')
    def test_reference_not_double_counted(self):
        self.assertEqual(route(dict(self.row,make_or_buy='REFERENCE_ONLY'))[0],'REFERENCE_ONLY')
    def test_hot_shield_not_abs(self):
        self.assertEqual(route(dict(self.row,part_id='EX-SH-01'))[0],'CUT_SHEET_DRILL_BEND')
    def test_pressure_body_keeps_precision(self):
        self.assertEqual(route(dict(self.row,part_id='EX-BAR-01'))[0],'RETAIN_FUNCTIONAL_PRECISION')
    def test_unknown_part_not_approved(self):
        self.assertEqual(route(dict(self.row,part_id='UNKNOWN',make_or_buy='MAKE_TO_DRAWING'))[0],'REVIEW_EXISTING_ROUTE')
    def test_duplicate_part_rejected(self):
        with self.assertRaises(ValueError): build([self.row,self.row],self.prints,self.frame,self.policy)
    def test_legacy_abs_no_physical_claim(self):
        _,p,_ = build([self.row],[dict(self.prints[0],part_id='PPR-C05',material='ABS')],[],self.policy)
        self.assertIn('NOT_PHYSICALLY_VERIFIED',p[0]['state'])
    def test_input_unchanged(self):
        before = copy.deepcopy((self.row,self.prints,self.frame))
        build([self.row],self.prints,self.frame,self.policy)
        self.assertEqual((self.row,self.prints,self.frame),before)
    def test_stock_is_not_grade_certification(self):
        stock = self.policy['fastener_stock']
        self.assertEqual(stock['nominal_diameters_mm'],[2,3,4,5,6])
        self.assertEqual(stock['length_pitch_grade_quantity'],'NOT_ENUMERATED')
    def test_donor_model_not_invented(self):
        self.assertEqual(self.policy['donor_printer']['model'],'Anycubic Chiron')
        self.assertEqual(self.policy['donor_printer']['controller_board'],'FAULT_REPORTED_NOT_ASSIGNED')
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    output = {'status':'PASS' if result.wasSuccessful() else 'FAIL', 'count':result.testsRun,
              'failures':len(result.failures), 'errors':len(result.errors),
              'kind':'SOFTWARE_POLICY_TESTS_ONLY','physical_validation':'NOT_RUN'}
    (HERE/'test_result.json').write_text(json.dumps(output,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
