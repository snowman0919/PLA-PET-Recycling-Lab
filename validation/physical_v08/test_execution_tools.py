#!/usr/bin/env python3
import csv,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/f'{name}.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
nest=load('profile_nesting'); p3=load('analyze_p3_records')

class ExecutionToolsTest(unittest.TestCase):
    def test_profile_nesting_synthetic(self):
        req=nest.requirements()
        ok,plan=nest.solve(req['2020'],[('SYN-2020',14000.0)],2.0)
        self.assertTrue(ok); self.assertEqual(sum(len(x['cuts']) for x in plan),26)
        ok2,_=nest.solve(req['2040'],[('SYN-2040',1000.0)],2.0)
        self.assertFalse(ok2)
    def test_p3_numeric_synthetic(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            with (d/'p3_current_sensor_calibration.csv').open('w',newline='') as f:
                w=csv.writer(f); w.writerow(['axis','point','adc_count','reference_current_a','u95_a'])
                for ax in ('SH','EX'):
                    for i,I in enumerate((0.0,1.0,2.0,3.0,4.0,5.0),1): w.writerow([ax,i,100+100*I,I,0.01])
            with (d/'p3_no_load.csv').open('w',newline='') as f:
                w=csv.writer(f); w.writerow(['axis','trial','direction','output_rpm','reference_current_a'])
                for ax,rpm in (('SH',30),('EX',15)):
                    for i in range(3): w.writerow([ax,i+1,'F',rpm,0.5])
            with (d/'p3_torque_map.csv').open('w',newline='') as f:
                w=csv.writer(f); w.writerow(['axis','sample_id','subset','direction','target_nm','force_n','u95_force_n','arm_mm','u95_arm_mm','rpm','adc_count'])
                fit=[1.5,3.0,4.5,6.0,7.8]; hold=[2.25,5.25,7.2]
                for ax,rpm in (('SH',30),('EX',15)):
                    for i,T in enumerate(fit,1):
                        di='R' if ax=='SH' and i==4 else 'F'; I=0.5+T/2; w.writerow([ax,f'{ax}F{i}','fit',di,T,4*T,0.02,250,0.1,rpm,100+100*I])
                    for i,T in enumerate(hold,1):
                        di=('F','R','F')[i-1] if ax=='SH' else 'F'; I=0.5+T/2; w.writerow([ax,f'{ax}H{i}','holdout',di,T,4*T,0.02,250,0.1,rpm,100+100*I])
            with (d/'p3_pin_release.csv').open('w',newline='') as f:
                w=csv.writer(f); w.writerow(['coupon_id','axis','direction','force_n','u95_force_n','arm_mm','u95_arm_mm','free_after_release','hub_key_damage'])
                for ax,di,prefix in (('SH','F','A'),('SH','R','B'),('EX','F','C')):
                    for i in range(3): w.writerow([f'{prefix}{i}',ax,di,36.2,0.02,250,0.1,'YES','NO'])
            cur=p3.read(d/'p3_current_sensor_calibration.csv'); nl=p3.read(d/'p3_no_load.csv'); tm=p3.read(d/'p3_torque_map.csv'); pins=p3.read(d/'p3_pin_release.csv')
            self.assertLessEqual(p3.current_fit(cur,'SH')[2],0.10)
            proc=subprocess.run(['python3',str(HERE/'analyze_p3_records.py'),str(d)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['status'],'NUMERIC_RECORD_CHECK_PASS')
if __name__=='__main__': unittest.main()
