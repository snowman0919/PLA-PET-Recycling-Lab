"""Synthetic regression fixtures; no real certificates or measurements."""
import copy,hashlib,json,math,tempfile,unittest
from pathlib import Path
from evidence_checks import EvidenceError,artifact,material_issues,friction_summary,review_packet
from calculate_evidence_bounds import pressure_force,bolt_screen,drag_budget,KSI_MPA

class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        p=self.root/'synthetic.txt';p.write_text('SYNTHETIC SOFTWARE TEST; NOT REAL EVIDENCE')
        self.ref={'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        self.req={'lot_id':'SYNTHETIC','material':'17-7PH','condition':'CH900','product_form':'sheet',
                  'thickness_mm':3.,'temperatures_c':[20,100,200,300],
                  'orientations':['rolling','transverse'],'test_temperature_tolerance_c':3.,'minimum_yield_mpa':1222.}
        self.cert={**self.req,'evidence_kind':'LOT_TEST_REPORT','raw_report':self.ref,
                   'final_heat_treatment_dimensions_verified':True,
                   'tests':[{'temperature_c':t,'temperature_uncertainty_c':1.,'orientation':o,
                             'property':'RP0.2','basis':'TEST_VALUE_WITH_UNCERTAINTY',
                             'yield_mpa':1300.,'yield_uncertainty_mpa':20.}
                            for t in self.req['temperatures_c'] for o in self.req['orientations']]}
        self.rows=[{'time_s':i,'direction':d,'tare_direction':d,'tare_condition_matches':True,
                    'phase':phase,'pull_force_n':d*30.,'tare_force_n':d*2.,
                    'force_uncertainty_n':.5,'tare_uncertainty_n':.25}
                   for i,(d,phase) in enumerate([(1,'BREAKAWAY'),(1,'STEADY'),(-1,'BREAKAWAY'),(-1,'STEADY')])]
    def tearDown(self):self.tmp.cleanup()
    def test_valid_synthetic_material(self):self.assertEqual(material_issues(self.cert,self.req,self.root),[])
    def test_material_typical_not_lot(self):
        self.cert['evidence_kind']='MANUFACTURER_TYPICAL';self.assertTrue(material_issues(self.cert,self.req,self.root))
    def test_room_only_not_hot(self):
        self.cert['tests']=self.cert['tests'][:2];self.assertTrue(material_issues(self.cert,self.req,self.root))
    def test_material_identity(self):
        for key,value in [('lot_id','OTHER'),('condition','TH1050'),('thickness_mm',1.27),('product_form','wire')]:
            with self.subTest(key=key):
                changed=copy.deepcopy(self.cert);changed[key]=value
                self.assertTrue(material_issues(changed,self.req,self.root))
    def test_material_orientations(self):
        self.cert['tests']=[r for r in self.cert['tests'] if r['orientation']=='rolling']
        self.assertTrue(material_issues(self.cert,self.req,self.root))
    def test_material_uncertainty(self):
        self.cert['tests'][0]['yield_uncertainty_mpa']=100
        self.assertTrue(material_issues(self.cert,self.req,self.root))
    def test_material_post_heat_treatment(self):
        self.cert['final_heat_treatment_dimensions_verified']=False
        self.assertTrue(material_issues(self.cert,self.req,self.root))
    def test_material_artifact_missing(self):
        (self.root/'synthetic.txt').unlink();self.assertTrue(material_issues(self.cert,self.req,self.root))
    def test_artifact_mutation(self):
        (self.root/'synthetic.txt').write_text('CHANGED')
        with self.assertRaises(EvidenceError):artifact(self.root,self.ref)
    def test_artifact_path_escape(self):
        for name in ('../secret','/tmp/test','a/../b','a\\b'):
            with self.subTest(name=name),self.assertRaises(EvidenceError):artifact(self.root,{**self.ref,'path':name})
    def test_signed_tare(self):
        result=friction_summary(self.rows);self.assertEqual(result['breakaway_upper_n'],28.75)
        self.assertTrue(all(r['mu_status']=='NOT_IDENTIFIABLE' for r in result['samples']))
    def test_mu_independent_normal(self):
        for row in self.rows:row.update(normal_force_sum_n=100.,normal_force_uncertainty_n=2.,normal_force_basis='INDEPENDENT_CONTACT_NORMAL_SUM')
        result=friction_summary(self.rows);self.assertAlmostEqual(result['samples'][0]['mu_interval'][1],28.75/98.)
    def test_lateral_not_normal(self):
        self.rows[0].update(normal_force_sum_n=25.,normal_force_uncertainty_n=.1,normal_force_basis='CARRIER_LATERAL_LOAD')
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_one_way_friction(self):
        rows=copy.deepcopy(self.rows)
        for r in rows:r.update(direction=1,tare_direction=1,pull_force_n=30,tare_force_n=2)
        with self.assertRaises(EvidenceError):friction_summary(rows)
    def test_direction_matched_tare(self):
        self.rows[0]['tare_direction']=-1
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_missing_breakaway(self):
        for r in self.rows:r['phase']='STEADY'
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_duplicate_time(self):
        self.rows[1]['time_s']=0
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_negative_individual_uncertainty(self):
        self.rows[0]['force_uncertainty_n']=-.1
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_nonfinite_force(self):
        self.rows[0]['pull_force_n']=math.nan
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_uncertain_zero_normal(self):
        self.rows[0].update(normal_force_sum_n=1.,normal_force_uncertainty_n=2.,normal_force_basis='INDEPENDENT_CONTACT_NORMAL_SUM')
        with self.assertRaises(EvidenceError):friction_summary(self.rows)
    def test_drag_budget(self):
        value=drag_budget(1100.,1054.1408425054715,105.93801356390571/25)
        self.assertAlmostEqual(value['conditional_max_drag_per_carrier_n'],32.466502781976786)
    def test_strength_below_baseline(self):
        self.assertFalse(drag_budget(1000.,1054.,4.)['base_strength_feasible'])
    def test_pressure_units(self):self.assertAlmostEqual(pressure_force(1.,2.),math.pi)
    def test_bad_pressure(self):
        for p,d in [(math.nan,16),(-1,16),(6,0),(True,16)]:
            with self.subTest(p=p,d=d),self.assertRaises(ValueError):pressure_force(p,d)
    def test_preload_and_external_both_count(self):
        r=bolt_screen(1500,4200,1,0,.5,5000)
        self.assertAlmostEqual(r['bolt_load_before_separation_n'],4950)
        self.assertAlmostEqual(r['residual_clamp_n'],3450)
    def test_relaxation_separation(self):
        r=bolt_screen(1500,2000,.5,-100,.1,5000)
        self.assertTrue(r['separation_predicted'])
    def test_thermal_preload_exceeds_proof(self):
        self.assertTrue(bolt_screen(1500,4200,1,1000,.5,5000)['above_proof_predicted'])
    def test_invalid_joint_fraction(self):
        with self.assertRaises(ValueError):bolt_screen(1,1,1.1,0,.2,100)
    def test_unit_conversion(self):self.assertAlmostEqual(146*KSI_MPA,1006.634564802528)
    def test_blank_packet(self):self.assertEqual(review_packet({'performed':False},self.root,'a'*64)['status'],'NOT_RUN')
    def test_packet_never_machine_pass(self):
        packet={'performed':True,'evidence_kind':'MEASURED','geometry_sha256':'a'*64,
                'specimen_ids':['SYNTHETIC'],'lot_id':'SYNTHETIC','heat_treatment_condition':'SYNTHETIC',
                'surface_condition':'SYNTHETIC','run_id':'SYNTHETIC'}
        for k in ('raw_trace','calibration_report','temperature_trace','alignment_report',
                  'preload_relaxation_report','material_report','operator_approval'):packet[k]=self.ref
        result=review_packet(packet,self.root,'a'*64)
        self.assertEqual(result['status'],'INTEGRITY_COMPLETE_REVIEW_REQUIRED')
        self.assertEqual(result['machine_release'],'HOLD')
        self.assertEqual(result['hardware_authorization'],'NOT_GRANTED')
    def test_missing_packet_report(self):
        self.assertEqual(review_packet({'performed':True},self.root,'a'*64)['status'],'EVIDENCE_INCOMPLETE')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(QualificationTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','kind':'SYNTHETIC_SOFTWARE_TESTS_ONLY',
            'count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'physical_validation':'NOT_RUN',
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__),Path(__file__).with_name('evidence_checks.py'),Path(__file__).with_name('calculate_evidence_bounds.py')]}}
    (Path(__file__).parent/'results/test_results.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
