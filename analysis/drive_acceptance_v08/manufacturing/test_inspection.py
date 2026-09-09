"""Synthetic records test rejection rules, not real components or measurements."""
from pathlib import Path
import unittest,copy,json,hashlib
import inspection as I
H=Path(__file__).resolve().parent
RAW=H/'raw/synthetic_record.txt'
RAW.write_text('SYNTHETIC SOFTWARE TEST DATA - NOT A PHYSICAL TEST\n')
def meta(serial='test-only'):
    return {'kind':'PHYSICAL_MEASUREMENT','performed':True,'operator':'SYNTHETIC_TEST',
      'part_serial':serial,'instrument_id':'SYNTHETIC','instrument_calibration_ref':'SYNTHETIC',
      'measured_at':'2026-09-10T00:00:00Z','raw_files':{str(RAW.relative_to(I.R)):hashlib.sha256(RAW.read_bytes()).hexdigest()}}
def reading(v,unit='mm',u=0):return {'value':v,'u95':u,'unit':unit}
def receipts():
    output={}
    for axis,gear in [('SH','K9G75C'),('EX','K9G150C')]:
        r=meta(axis);r.update(motor_model='K9DG60N2',gear_model=gear)
        r['readings']={k:reading((a+b)/2,u=0,unit=unit) for k,(a,b,unit) in I.RECEIPT.items()};output[axis]=r
    return output

def current_records():
    result={}
    for axis in ('SH','EX'):
        r=meta(axis);r.update(current_location='motor_lead',units={'current':'A','torque':'N.m','speed':'rpm','adc':'count'})
        r['adc_samples']=[{'adc':200+100*a,'reference_a':a,'u95_a':.01} for a in (0,.5,1,2,3,4,5)]
        r['no_load_a']=[.5,.5,.5];r['torque_samples']=[]
        for group,loads in [('fit',[0,2,4,6,8]),('holdout',[1,3,5,7.8])]:
            for j,t in enumerate(loads):r['torque_samples'].append({'sample_id':group+str(j),'subset':group,
              'adc':250+50*t,'reference_nm':t,'u95_nm':.04,'rpm':40 if axis=='SH' else 18,
              'direction':'R' if axis=='SH' and j%2 else 'F'})
        result[axis]=r
    return result
def pin_record():
    r=meta();r['samples']=[]
    for axis,direction in [('SH','F'),('SH','R'),('EX','F')]:
        for i in range(3):r['samples'].append({'axis':axis,'direction':direction,'coupon_id':axis+direction+str(i),
          'material_lot':'SYNTHETIC','drawing_revision':'TEST','release_torque':reading(9.05,'N.m',.05)})
    return r
class Tests(unittest.TestCase):
    def test_no_records_stay_not_run(self):
        r=I.inspect({});self.assertTrue(all(x['status']=='NOT_RUN' for x in r['domains'].values()));self.assertEqual(r['machine_release'],'HOLD')
    def test_actual_receipt_not_inferred(self):self.assertEqual(I.receipt(receipts())['motor_records'],2)
    def test_boolean_is_not_number(self):
        with self.assertRaises(ValueError):I.number(True)
    def test_nonfinite_rejected(self):
        for x in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):I.number(x)
    def test_unit_rejected(self):
        with self.assertRaises(ValueError):I.interval(reading(9,'kgf.cm'),8.8,9.3,'N.m')
    def test_uncertainty_bounds(self):
        with self.assertRaises(ValueError):I.interval(reading(.029,u=.002),0,.03,'mm')
    def test_negative_uncertainty(self):
        with self.assertRaises(ValueError):I.interval(reading(.01,u=-.002),0,.03,'mm')
    def test_raw_file_required(self):
        r=meta();r['raw_files']={}
        with self.assertRaises(ValueError):I.evidence(r)
    def test_stale_raw_rejected(self):
        r=meta();r['raw_files']={str(RAW.relative_to(I.R)):'0'*64}
        with self.assertRaises(ValueError):I.evidence(r)
    def test_wrong_motor(self):
        r=receipts();r['EX']['gear_model']='K9G75C'
        with self.assertRaises(ValueError):I.receipt(r)
    def test_duplicate_motor(self):
        r=receipts();r['EX']['part_serial']='SH'
        with self.assertRaises(ValueError):I.receipt(r)
    def test_alignment_gap(self):
        r=meta();r['readings']={k:reading((a+b)/2,unit=unit) for k,(a,b,unit) in I.ALIGN.items()}
        self.assertEqual(I.alignment(r)['checks'],8);r['readings']['coupling_face_gap']=reading(0)
        with self.assertRaises(ValueError):I.alignment(r)
    def test_pin_synthetic_numeric(self):self.assertEqual(I.pins(pin_record())['coupons'],9)
    def test_pin_above_range(self):
        r=pin_record();r['samples'][0]['release_torque']=reading(9.5,'N.m')
        with self.assertRaises(ValueError):I.pins(r)
    def test_duplicate_coupon(self):
        r=pin_record();r['samples'][1]['coupon_id']=r['samples'][0]['coupon_id']
        with self.assertRaises(ValueError):I.pins(r)
    def test_pin_direction_coverage(self):
        r=pin_record();r['samples']=r['samples'][:3]
        with self.assertRaises(ValueError):I.pins(r)
    def test_current_fit(self):
        r=I.currents(current_records());self.assertAlmostEqual(r['SH']['gearbox_nm_per_amp'],2);self.assertFalse(r['EX']['write_firmware'])
    def test_bus_current_rejected(self):
        r=current_records();r['SH']['current_location']='psu_input'
        with self.assertRaises(ValueError):I.currents(r)
    def test_saturated_adc(self):
        r=current_records();r['SH']['adc_samples'][0]['adc']=1023
        with self.assertRaises(ValueError):I.currents(r)
    def test_current_uncertainty(self):
        r=current_records();r['SH']['adc_samples'][0]['u95_a']=-.1
        with self.assertRaises(ValueError):I.currents(r)
    def test_holdout_is_required(self):
        r=current_records();r['SH']['torque_samples']=r['SH']['torque_samples'][:5]
        with self.assertRaises(ValueError):I.currents(r)
    def test_reverse_holdout(self):
        r=current_records()
        for row in r['SH']['torque_samples']:row['direction']='F'
        with self.assertRaises(ValueError):I.currents(r)
    def test_torque_error(self):
        r=current_records();r['SH']['torque_samples'][-1]['reference_nm']+=1
        with self.assertRaises(ValueError):I.currents(r)
    def test_wrong_current_units(self):
        r=current_records();r['SH']['units']['current']='mA'
        with self.assertRaises(ValueError):I.currents(r)
    def test_zero_adc_span(self):
        with self.assertRaises(ValueError):I.fit_line([(1,0),(1,1),(1,2)])
    def test_extruder_reverse(self):
        r=current_records();r['EX']['torque_samples'][0]['direction']='R'
        with self.assertRaises(ValueError):I.currents(r)
    def test_no_load_samples(self):
        r=current_records();r['EX']['no_load_a']=[]
        with self.assertRaises(ValueError):I.currents(r)
    def test_missing_design_binding(self):
        r=I.inspect({'receipt':{'performed':True,'data':receipts()}})
        self.assertEqual(r['domains']['receipt']['status'],'REJECTED')
    def test_stale_design_binding(self):
        r=I.inspect({'design_sha256':{'control/ggm_drive_contract.json':'0'*64},'receipt':{'performed':True,'data':receipts()}})
        self.assertEqual(r['domains']['receipt']['status'],'REJECTED')
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    (H/'tests.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'scope':'SYNTHETIC_RECORD_VALIDATION_ONLY','physical_tests':0},indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
