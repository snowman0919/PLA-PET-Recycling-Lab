#!/usr/bin/env python3
import csv,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/f'{name}.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
nest=load('profile_nesting'); p1=load('analyze_p1_records'); p2=load('analyze_p2_records'); mount=load('analyze_ggm_mount_compatibility'); p3pre=load('analyze_p3_preflight'); p3=load('analyze_p3_records')

class ExecutionToolsTest(unittest.TestCase):
    def test_p1_fail_closed_and_ggm_pending(self):
        import hashlib
        root=HERE.parents[1]
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d=Path(td); evidence=d/'evidence.txt'; evidence.write_text('measured')
            digest=hashlib.sha256(evidence.read_bytes()).hexdigest(); rel=str(evidence.relative_to(root))
            template=p1.read_csv(HERE/'templates/p1_inventory_record.csv')
            rows=[]
            for source in template:
                row=dict(source)
                if row['planned_state'] in p1.SURVEY_STATES:
                    row.update({'observed_quantity':'1','manufacturer_model_marking':'MODEL',
                        'dimension_or_rating_summary':'checked','condition':'GOOD','instrument_id':'MEAS-P1',
                        'instrument_calibration_ref':'CAL-P1','measured_at':'2026-09-10T13:00+09:00',
                        'operator':'TEST','reviewer':'REVIEW','evidence_path':rel,'sha256':digest,'result':'PASS'})
                rows.append(row)
            pending=p1.evaluate(rows,root)
            self.assertEqual(pending['status'],'P1_STOCK_SURVEY_PASS_GGM_PENDING')
            self.assertEqual(pending['required_item_count'],30)

            def receipt(axis,gear):
                return {'kind':'PHYSICAL_MEASUREMENT','performed':True,'operator':'TEST',
                    'part_serial':'SER-'+axis,'instrument_id':'MEAS-P1','instrument_calibration_ref':'CAL-P1',
                    'measured_at':'2026-09-10T13:10+09:00','raw_files':{rel:digest},
                    'motor_model':'K9DG60N2','gear_model':gear,'readings':{
                        'voltage_v':{'value':24.0,'u95':0.0,'unit':'V'},
                        'shaft_diameter':{'value':11.99,'u95':0.002,'unit':'mm'},
                        'shaft_projection':{'value':32.0,'u95':0.05,'unit':'mm'},
                        'bolt_pcd':{'value':104.0,'u95':0.01,'unit':'mm'},
                        'output_offset':{'value':18.0,'u95':0.01,'unit':'mm'},
                        'case_width':{'value':90.0,'u95':0.1,'unit':'mm'},
                        'rear_length':{'value':209.0,'u95':0.1,'unit':'mm'}}}
            packet={'receipt':{'performed':True,'data':{
                'SH':receipt('SH','K9G75C'),'EX':receipt('EX','K9G150C')}}}
            for row in rows:
                if row['item_id'] in p1.GGM_AXES:
                    row.update({'observed_quantity':'1','manufacturer_model_marking':'K9DG60N2 '+p1.GGM_AXES[row['item_id']][1],
                        'dimension_or_rating_summary':'receipt geometry measured','condition':'GOOD','instrument_id':'MEAS-P1',
                        'instrument_calibration_ref':'CAL-P1','measured_at':'2026-09-10T13:10+09:00',
                        'operator':'TEST','reviewer':'REVIEW','evidence_path':rel,'sha256':digest,'result':'PASS'})
            with self.assertRaises(ValueError): p1.evaluate(rows,root)
            passed=p1.evaluate(rows,root,packet)
            self.assertEqual(passed['status'],'P1_RECORD_CHECK_PASS')
            self.assertEqual(set(passed['ggm_receipt_verified']),{'SH','EX'})

            short=rows[:-1]
            with self.assertRaises(ValueError): p1.evaluate(short,root,packet)
            rows[0]['sha256']='0'*64
            with self.assertRaises(ValueError): p1.evaluate(rows,root,packet)

    def test_p2_authenticated_cold_fit(self):
        import hashlib
        root=HERE.parents[1]
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d=Path(td); evidence=d/'p2.txt'; evidence.write_text('synthetic P2 inspection')
            digest=hashlib.sha256(evidence.read_bytes()).hexdigest(); rel=str(evidence.relative_to(root))
            numeric={
                'frame_base_x':(470.0,.10,'mm'), 'frame_base_y':(700.0,.10,'mm'),
                'frame_diagonal_a':(843.0,.10,'mm'), 'frame_diagonal_b':(843.2,.10,'mm'),
                'rail_squareness_700':(.30,.05,'mm'), 'shredder_min_static_clearance':(2.10,.05,'mm'),
                'shredder_hand_rotation_contacts':(0,0,'count'), 'extruder_cold_axial_travel':(1.70,.05,'mm'),
                'extruder_rear_retainer_endplay':(.20,.02,'mm')}
            rows=[]
            for metric,(value,u95,unit) in numeric.items():
                rows.append({'metric':metric,'value':str(value),'u95':str(u95),'unit':unit,'instrument_id':'MEAS-P2','instrument_calibration_ref':'CAL-P2','operator':'TEST','reviewer':'REVIEW','measured_at':'2026-09-10T15:30+09:00','evidence_path':rel,'sha256':digest})
            for metric in ('frame_rocking','guard_moving_envelope_intrusion','guard_hot_envelope_intrusion'):
                rows.append({'metric':metric,'value':'false','u95':'','unit':'boolean','instrument_id':'','instrument_calibration_ref':'','operator':'TEST','reviewer':'REVIEW','measured_at':'2026-09-10T15:30+09:00','evidence_path':rel,'sha256':digest})
            ok=p2.evaluate_measurements(rows,root)
            self.assertEqual(ok['status'],'PASS')
            by={r['metric']:r for r in rows}
            by['frame_base_x']['value']='470.75'; by['frame_base_x']['u95']='0.10'
            self.assertEqual(p2.evaluate_measurements(rows,root)['status'],'FAIL')
            by['frame_base_x']['value']='470.0'; by['frame_base_x']['u95']='0.10'
            by['frame_diagonal_b']['value']='843.85'
            self.assertEqual(p2.evaluate_measurements(rows,root)['status'],'FAIL')
            by['frame_diagonal_b']['value']='843.2'; by['frame_rocking']['value']='true'
            self.assertEqual(p2.evaluate_measurements(rows,root)['status'],'FAIL')
            by['frame_rocking']['value']='false'; by['rail_squareness_700']['sha256']='0'*64
            with self.assertRaises(ValueError): p2.evaluate_measurements(rows,root)
    def test_ggm_mount_compatibility_from_receipt(self):
        import hashlib
        root=HERE.parents[1]
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            evidence=Path(td)/'receipt.txt'; evidence.write_text('synthetic receipt geometry')
            digest=hashlib.sha256(evidence.read_bytes()).hexdigest(); rel=str(evidence.relative_to(root))
            def rec(axis,gear,pcd=104.0,offset=18.0):
                return {'kind':'PHYSICAL_MEASUREMENT','performed':True,'operator':'TEST','part_serial':'SER-'+axis,
                    'instrument_id':'MEAS-01','instrument_calibration_ref':'TEST','measured_at':'2026-09-10T14:00+09:00',
                    'raw_files':{rel:digest},'motor_model':'K9DG60N2','gear_model':gear,'readings':{
                        'voltage_v':{'value':24.0,'u95':0.0,'unit':'V'},
                        'shaft_diameter':{'value':11.99,'u95':0.002,'unit':'mm'},
                        'shaft_projection':{'value':32.0,'u95':0.05,'unit':'mm'},
                        'bolt_pcd':{'value':pcd,'u95':0.01,'unit':'mm'},
                        'output_offset':{'value':offset,'u95':0.01,'unit':'mm'},
                        'case_width':{'value':90.0,'u95':0.1,'unit':'mm'},
                        'rear_length':{'value':209.0,'u95':0.1,'unit':'mm'}}}
            bindings={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
                'control/ggm_drive_contract.json','analysis/drive_acceptance_v08/manufacturing/drawing_contract.json')}
            packet={'design_sha256':bindings,'receipt':{'performed':True,'data':{'SH':rec('SH','K9G75C'),'EX':rec('EX','K9G150C')}}}
            ok=mount.evaluate(packet)
            self.assertEqual(ok['status'],'AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED'); self.assertFalse(ok['drilling_authorized'])
            packet['receipt']['data']['EX']=rec('EX','K9G150C',offset=18.35)
            hold=mount.evaluate(packet)
            self.assertEqual(hold['status'],'HOLD_REDRAW_REQUIRED'); self.assertTrue(hold['mount_redesign_required'])
            packet['design_sha256']['control/ggm_drive_contract.json']='0'*64
            self.assertEqual(mount.evaluate(packet)['status'],'BLOCKED_STALE_DESIGN_BINDING')
    def test_p3_preflight_authenticated_and_fail_closed(self):
        import hashlib
        root=HERE.parents[1]
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d=Path(td); evidence=d/'p3-preflight.txt'; evidence.write_text('synthetic P3 preflight evidence')
            digest=hashlib.sha256(evidence.read_bytes()).hexdigest(); rel=str(evidence.relative_to(root))
            def rec(axis,gear,offset=18.0):
                return {'kind':'PHYSICAL_MEASUREMENT','performed':True,'operator':'TEST','part_serial':'SER-'+axis,
                    'instrument_id':'MEAS-01','instrument_calibration_ref':'CAL-R','measured_at':'2026-09-10T16:00+09:00',
                    'raw_files':{rel:digest},'motor_model':'K9DG60N2','gear_model':gear,'readings':{
                        'voltage_v':{'value':24.0,'u95':0.0,'unit':'V'},
                        'shaft_diameter':{'value':11.99,'u95':0.002,'unit':'mm'},
                        'shaft_projection':{'value':32.0,'u95':0.05,'unit':'mm'},
                        'bolt_pcd':{'value':104.0,'u95':0.01,'unit':'mm'},
                        'output_offset':{'value':offset,'u95':0.01,'unit':'mm'},
                        'case_width':{'value':90.0,'u95':0.1,'unit':'mm'},
                        'rear_length':{'value':209.0,'u95':0.1,'unit':'mm'}}}
            bindings={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
                'control/ggm_drive_contract.json','analysis/drive_acceptance_v08/manufacturing/drawing_contract.json')}
            packet={'design_sha256':bindings,'receipt':{'performed':True,'data':{'SH':rec('SH','K9G75C'),'EX':rec('EX','K9G150C')}}}
            receipt_file=d/'p3-receipt.json'; receipt_file.write_text(json.dumps(packet,indent=2)+'\n')
            receipt_digest=hashlib.sha256(receipt_file.read_bytes()).hexdigest()
            common={'status':'PASS','operator':'TEST','reviewer':'REVIEW','checked_at':'2026-09-10T16:05+09:00','evidence_path':rel,'sha256':digest,'notes':'synthetic'}
            rows=[{'check_id':check_id,'observed':sorted(accepted)[0],**common} for check_id,accepted in p3pre.EXPECTED.items()]
            p2_release=d/'p2-stage-release.json'; p2_release.write_text('{"stage":"P2","status":"PASS"}\n')
            p2_digest=hashlib.sha256(p2_release.read_bytes()).hexdigest(); p2_rel=str(p2_release.relative_to(root))
            p2row=next(r for r in rows if r['check_id']=='p2_applicable_cold_fit'); p2row['evidence_path']=p2_rel; p2row['sha256']=p2_digest
            p2_ok=lambda _: {'status':'P2_STAGE_RELEASE_VALIDATED','p3_entry_prerequisite':True,
                'motor_energization_authorized':False,'machine_release':'HOLD','ggm_packet_sha256':receipt_digest}
            ok=p3pre.evaluate(rows,packet,root,p2_checker=p2_ok,receipt_packet_sha256=receipt_digest)
            self.assertEqual(ok['status'],'PREPOWER_RECORD_CHECK_PASS')
            self.assertFalse(ok['motor_energization_authorized']); self.assertFalse(ok['stage_p3_pass'])
            self.assertEqual(ok['mount_status'],'AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED')
            self.assertEqual(ok['p2_stage_release']['status'],'P2_STAGE_RELEASE_VALIDATED')
            self.assertEqual(ok['p0_snapshot_head'], p3pre.source_identity(root)[0])
            p2_bad=lambda _: {'status':'NOT_RUN_OR_REJECTED','p3_entry_prerequisite':False,
                'motor_energization_authorized':False,'machine_release':'HOLD','ggm_packet_sha256':receipt_digest}
            with self.assertRaises(ValueError): p3pre.evaluate(rows,packet,root,p2_checker=p2_bad,receipt_packet_sha256=receipt_digest)
            by={r['check_id']:r for r in rows}
            by['extruder_current_channel']['observed']='A8_MOTOR_LEAD'
            with self.assertRaises(ValueError): p3pre.evaluate(rows,packet,root,p2_checker=p2_ok,receipt_packet_sha256=receipt_digest)
            by['extruder_current_channel']['observed']='A9_MOTOR_LEAD'; by['workspace_clear']['sha256']='0'*64
            with self.assertRaises(ValueError): p3pre.evaluate(rows,packet,root,p2_checker=p2_ok,receipt_packet_sha256=receipt_digest)
            by['workspace_clear']['sha256']=digest
            packet['receipt']['data']['EX']=rec('EX','K9G150C',offset=18.35)
            with self.assertRaises(ValueError): p3pre.evaluate(rows,packet,root,p2_checker=p2_ok,receipt_packet_sha256=receipt_digest)

    def test_profile_nesting_synthetic(self):
        import hashlib
        req=nest.requirements()
        ok,plan=nest.solve(req['2020'],[('SYN-2020',14000.0)],2.0)
        self.assertTrue(ok); self.assertEqual(sum(len(x['cuts']) for x in plan),26)
        ok2,_=nest.solve(req['2040'],[('SYN-2040',1000.0)],2.0)
        self.assertFalse(ok2)
        root=HERE.parents[1]
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d=Path(td); evidence=d/'profile.txt'; evidence.write_text('profile measured')
            digest=hashlib.sha256(evidence.read_bytes()).hexdigest(); rel=str(evidence.relative_to(root))
            csv_path=d/'stock.csv'
            fields=['record_id','profile_type','source_asset','usable_length_mm','u95_length_mm','straightness_note','damage_note','instrument_id','instrument_calibration_ref','measured_at','operator','reviewer','evidence_path','sha256','status','notes']
            with csv_path.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                common={'source_asset':'LAB','u95_length_mm':'1.0','straightness_note':'OK','damage_note':'NONE','instrument_id':'MEAS-16','instrument_calibration_ref':'CHECK-1M','measured_at':'2026-09-10T14:30+09:00','operator':'TEST','reviewer':'REVIEW','evidence_path':rel,'sha256':digest,'status':'USABLE','notes':''}
                w.writerow({'record_id':'S2020','profile_type':'2020','usable_length_mm':'14000',**common})
                w.writerow({'record_id':'S2040','profile_type':'2040','usable_length_mm':'1400',**common})
            stock=nest.measured(csv_path)
            self.assertEqual(stock['2020'][0][1],13999.0)
            ok3,_=nest.solve(req['2040'],stock['2040'],2.0); self.assertTrue(ok3)
            output=d/'nesting.json'
            proc=subprocess.run(['python3',str(HERE/'profile_nesting.py'),str(csv_path),'--kerf-mm','2.0','--output',str(output)],capture_output=True,text=True,cwd=root)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            bound=json.loads(output.read_text())
            self.assertEqual(bound['status'],'PASS'); self.assertFalse(bound['cut_authorization'])
            self.assertEqual(bound['measurements_sha256'],hashlib.sha256(csv_path.read_bytes()).hexdigest())
            self.assertEqual(bound['cutlist_sha256'],hashlib.sha256((root/'exports/fabrication/frame_cut_list.csv').read_bytes()).hexdigest())
            self.assertEqual(bound['solver_source_sha256'],hashlib.sha256((HERE/'profile_nesting.py').read_bytes()).hexdigest())
            with csv_path.open(newline='') as f: rows=list(csv.DictReader(f))
            rows[0]['sha256']='0'*64
            with csv_path.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
            with self.assertRaises(ValueError): nest.measured(csv_path)
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
