"""R2: reject semantically invalid receipt declarations, not just stale hashes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import analyze_p1_records as p1
from p1_test_fixtures import fill_semantics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

class P1SemanticsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE)
        self.folder=Path(self.tmp.name)
        raw=self.folder/'synthetic.txt';raw.write_text('SYNTHETIC TEST ONLY - no physical inspection')
        self.rows=p1.read_csv(HERE/'templates/p1_inventory_record.csv')
        for row in self.rows:
            if row['planned_state'] not in p1.SURVEY_STATES: continue
            row.update(result='PASS',observed_quantity='1',manufacturer_model_marking='SYNTHETIC '+row['item_id'],
                       dimension_or_rating_summary='Synthetic label and geometry check',condition='GOOD',
                       instrument_id='TEST-INSTRUMENT',instrument_calibration_ref='TEST-CAL',
                       measured_at='2026-09-12T01:00:00+09:00',operator='TEST-A',reviewer='TEST-B',
                       evidence_path=raw.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
        fill_semantics(self.rows,ROOT,self.folder)
    def tearDown(self): self.tmp.cleanup()
    def row(self,rows,item): return next(r for r in rows if r['item_id']==item)
    def test_valid_survey_still_no_authorization(self):
        result=p1.evaluate(self.rows,ROOT)
        self.assertEqual(result['status'],'P1_STOCK_SURVEY_PASS_GGM_PENDING')
        self.assertFalse(result['hardware_authorization'])
        self.assertFalse(result['stage_p1_pass'])
    def test_exact_counts_reject_invalid_short_surplus(self):
        for value in ('0','-1','2','4','3.1','nan','inf','-inf','1e309','','three',True):
            with self.subTest(value=value):
                rows=copy.deepcopy(self.rows);self.row(rows,'STOCK-6201')['observed_quantity']=value
                with self.assertRaises(ValueError):p1.evaluate(rows,ROOT)
    def test_identity_and_condition_are_not_free_text_passes(self):
        for key,values in {'manufacturer_model_marking':['','UNKNOWN','N/A','미확인'],
                           'condition':['DAMAGED','BAD','GOOD BUT CRACKED','UNKNOWN'],
                           'identity_check':['','PENDING'], 'quantity_unit':['kg',''],
                           'inspection_power_state':['USB','MAINS','']}.items():
            for value in values:
                with self.subTest(key=key,value=value):
                    rows=copy.deepcopy(self.rows);self.row(rows,'ASSET-PSU')[key]=value
                    with self.assertRaises(ValueError):p1.evaluate(rows,ROOT)
    def test_legacy_review_counterexample_rejected(self):
        rows=copy.deepcopy(self.rows)
        for row in rows:
            if row['result']=='PASS':row.update(observed_quantity='0',manufacturer_model_marking='',condition='DAMAGED')
        with self.assertRaises(ValueError):p1.evaluate(rows,ROOT)
    def mutate_detail(self,item,mutation):
        rows=copy.deepcopy(self.rows);row=self.row(rows,item);path=ROOT/row['detail_path']
        data=json.loads(path.read_text());mutation(data,row)
        path.write_text(json.dumps(data));row['detail_sha256']=p1.sha(path)
        with self.assertRaises(ValueError):p1.evaluate(rows,ROOT)
    def test_valid_hash_does_not_hide_missing_set_component(self):
        self.mutate_detail('STOCK-CHAIN',lambda d,r:d['entries'].pop())
    def test_valid_hash_does_not_hide_damaged_nested_stock(self):
        self.mutate_detail('MAT-PLATE',lambda d,r:d['entries'][0].update(condition='DAMAGED'))
    def test_valid_hash_does_not_hide_zero_bulk_quantity(self):
        self.mutate_detail('ASSET-HW',lambda d,r:d['entries'][0].update(quantity=0))
    def test_short_profile_total_is_rejected(self):
        def change(data,row):
            data['entries'][0]['quantity']=100
            row['observed_quantity']='100'
        self.mutate_detail('ASSET-2020',change)
    def test_wrong_requirement_binding_is_rejected(self):
        self.mutate_detail('ASSET-ABS',lambda d,r:d.update(inventory_control_sha256='0'*64))
    def test_duplicate_entry_is_rejected(self):
        self.mutate_detail('MAT-SHAFT',lambda d,r:d['entries'].append(dict(d['entries'][0])))
    def test_unreviewed_bulk_cannot_be_passed(self):
        self.mutate_detail('MAT-GASKET',lambda d,r:d.update(requirements_review='PENDING'))
    def test_same_person_differing_case_is_rejected(self):
        rows=copy.deepcopy(self.rows);row=self.row(rows,'ASSET-PSU');row['reviewer']=row['operator'].lower()
        with self.assertRaises(ValueError):p1.evaluate(rows,ROOT)
    def test_missing_details_rejected(self):
        rows=copy.deepcopy(self.rows);self.row(rows,'ASSET-2020')['detail_path']=''
        with self.assertRaises(ValueError):p1.evaluate(rows,ROOT)
    def test_blank_template_never_passes(self):
        result=p1.evaluate(p1.read_csv(HERE/'templates/p1_inventory_record.csv'),ROOT)
        self.assertEqual(result['status'],'P1_SURVEY_INCOMPLETE')
        self.assertFalse(result['stage_p1_pass'])

if __name__=='__main__':unittest.main()
