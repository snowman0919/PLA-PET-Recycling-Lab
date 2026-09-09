"""Reject stale or weakened provisional material requirements; synthetic only."""
from pathlib import Path
import hashlib,json,tempfile,unittest
from minimum_requirements import minimum_yield_floor

class FloorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'qualification/results').mkdir(parents=True)
        (self.root/'input.txt').write_text('SYNTHETIC')
        h=hashlib.sha256((self.root/'input.txt').read_bytes()).hexdigest()
        self.base={'proposed_certificate_minimum_mpa_at_actual_service_temperature':1100.,
                   'conservative_combined_screen_requirement_mpa':1054.,'source_sha256':{'input.txt':h}}
        self.extra={'assumed_mu':.25,'runs':[{'result':{'max_von_mises_mpa':100.}},{'result':{'max_von_mises_mpa':106.}}],
                    'strength_requirement_including_assumed_drag_mpa':1054+2*106*474*.25/6/25,
                    'source_sha256':{'input.txt':h}}
        self.write()
    def write(self):
        (self.root/'derived_requirements.json').write_text(json.dumps(self.base))
        (self.root/'qualification/results/axial_drag.json').write_text(json.dumps(self.extra))
        (self.root/'sliding_envelope.json').write_text(json.dumps({'maximum_total_normal_force_per_carrier_n':474.}))
    def tearDown(self): self.tmp.cleanup()
    def test_valid_floor(self): self.assertEqual(minimum_yield_floor(self.root),1222.)
    def test_changed_source(self):
        (self.root/'input.txt').write_text('CHANGED')
        with self.assertRaises(ValueError):minimum_yield_floor(self.root)
    def test_missing_supplement(self):
        (self.root/'qualification/results/axial_drag.json').unlink()
        with self.assertRaises(OSError):minimum_yield_floor(self.root)
    def test_arithmetic_mutation(self):
        self.extra['strength_requirement_including_assumed_drag_mpa']=1100.;self.write()
        with self.assertRaises(ValueError):minimum_yield_floor(self.root)
    def test_wrong_digest(self):
        self.extra['source_sha256']['input.txt']='0'*64;self.write()
        with self.assertRaises(ValueError):minimum_yield_floor(self.root)
    def test_path_escape(self):
        self.extra['source_sha256']['../outside']='0'*64;self.write()
        with self.assertRaises(ValueError):minimum_yield_floor(self.root)
    def test_nonfinite_requirement(self):
        self.base['proposed_certificate_minimum_mpa_at_actual_service_temperature']=float('nan');self.write()
        with self.assertRaises(ValueError):minimum_yield_floor(self.root)
    def test_unsupported_friction_basis(self):
        self.extra['assumed_mu']=.1;self.write()
        with self.assertRaises(ValueError):minimum_yield_floor(self.root)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FloorTests))
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','kind':'SYNTHETIC_SOFTWARE_TESTS_ONLY',
            'count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'physical_validation':'NOT_RUN','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
             for p in [Path(__file__),Path(__file__).with_name('minimum_requirements.py')]}}
    (Path(__file__).parent/'results/strength_floor_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
