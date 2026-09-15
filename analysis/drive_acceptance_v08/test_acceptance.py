"""Negative evidence tests; no changes to production files or hardware."""
import hashlib, json, tempfile, unittest
from pathlib import Path
import verify_snapshot as v

class Tests(unittest.TestCase):
    def test_valid_declared_source(self):
        p=v.HERE/'geometry_review.json'
        v.check_bindings({'source_sha256':{str(p.relative_to(v.ROOT)):v.sha(p)}})
    def test_empty_bindings_rejected(self):
        with self.assertRaises(ValueError): v.check_bindings({})
    def test_changed_digest_rejected(self):
        p=v.HERE/'geometry_review.json'
        with self.assertRaises(ValueError):
            v.check_bindings({'source_sha256':{str(p.relative_to(v.ROOT)):'0'*64}})
    def test_malformed_digest_rejected(self):
        with self.assertRaises(ValueError): v.check_bindings({'source_sha256':{'a':'PASS'}})
    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError): v.bound_path(v.HERE,'../../../../etc/passwd')
    def test_declared_local_path(self):
        self.assertEqual(v.bound_path(v.HERE,'geometry_review.json'),v.HERE/'geometry_review.json')
    def test_process_results_not_physical(self):
        r=json.loads((v.HERE/'process_limits.json').read_text())
        self.assertEqual(r['physical_validation'],'NOT_RUN'); self.assertEqual(r['case_count'],8)
    def test_high_viscosity_stop_not_pass(self):
        r=json.loads((v.HERE/'process_limits.json').read_text())
        row=next(c for c in r['cases'] if c['case']=='PET_selected_high_viscosity')
        self.assertEqual(row['expected_guard_response'],'OVERLOAD_STOP_EXPECTED')
    def test_journals_have_full_round_section(self):
        r=json.loads((v.HERE/'geometry_review.json').read_text())
        self.assertEqual(len(r['journal_checks']),3)
        self.assertTrue(all(x['missing_round_journal_mm3']<1e-4 for x in r['journal_checks']))
    def test_not_automatic_derating(self):
        r=json.loads((v.HERE/'process_limits.json').read_text())
        self.assertTrue(all(not c['automatic_derating_implemented'] for c in r['cases']))

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    report={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),
            'status':'PASS' if r.wasSuccessful() else 'FAIL','physical_validation':'NOT_RUN'}
    (v.HERE/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
