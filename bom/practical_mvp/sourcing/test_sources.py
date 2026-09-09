"""Cost records cannot invent inventory or a completed checkout."""
import copy,json,unittest
from pathlib import Path
from check_sources import read,validate
HERE=Path(__file__).resolve().parent
class SourceTests(unittest.TestCase):
    def setUp(self):self.parts=read('minimum_confirmation_bom.csv');self.prices=read('price_observations.csv')
    def test_current(self):self.assertEqual(validate(self.parts,self.prices)['confirmation_groups'],13)
    def test_no_invented_stock(self):
        self.parts[0]['confirmed_available_quantity']='0'
        with self.assertRaises(ValueError):validate(self.parts,self.prices)
    def test_no_order_quantity_before_reply(self):
        self.parts[0]['purchase_quantity']='1'
        with self.assertRaises(ValueError):validate(self.parts,self.prices)
    def test_quote_is_not_zero_price(self):
        next(r for r in self.prices if r['tax_basis']=='QUOTE_REQUIRED')['display_price_krw']='0'
        with self.assertRaises(ValueError):validate(self.parts,self.prices)
    def test_unknown_source(self):
        self.parts[0]['source_ids']='INVENTED'
        with self.assertRaises(ValueError):validate(self.parts,self.prices)
    def test_no_live_checkout_claim(self):
        self.prices[0]['evidence_scope']='CHECKOUT_VERIFIED'
        with self.assertRaises(ValueError):validate(self.parts,self.prices)
    def test_no_duplicate_bom(self):
        self.parts.append(copy.deepcopy(self.parts[0]))
        with self.assertRaises(ValueError):validate(self.parts,self.prices)
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceTests))
    (HERE/'tests.json').write_text(json.dumps({'status':'PASS' if r.wasSuccessful() else 'FAIL','count':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'kind':'SYNTHETIC_RECORD_TESTS_ONLY'},indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
