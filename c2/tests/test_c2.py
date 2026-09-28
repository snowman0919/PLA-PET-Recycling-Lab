from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from engineering import (S2,Thermal,design_set,packaging,hook_polygon,transform,kinematics,
                         thermal_run,thermal_duty_run,thermal_capacities_from_cad,
                         equivalent_motor_load,generalized_torque,point_jacobian)
from control import Controller,allocate_power,REQUIRED_SENSORS
from performance import (candidate_hashes,evidence_inventory,validate_evidence_record,
                         validate_record,training_gate,EvidenceError,nondominated,TARGETS)
from costing import evaluate
from pin_constraint import verify

class GeometryTests(unittest.TestCase):
    def test_psu_and_total_budget(self):
        c=json.loads((R/'design/requirements.json').read_text())['user_constraints']
        self.assertEqual((c['psu_V'],c['psu_current_A'],c['psu_nameplate_W'],c['operational_cap_W'],c['psu_current_derived_ceiling_W']),(24,33,800,500,792))
        self.assertEqual(c['psu_body_mm'],[240,120,65])
        self.assertEqual(c['budget_soft_limit_KRW'],100000)
        self.assertFalse(c['motor_M1_frozen'])
    def test_materials_exact(self):
        self.assertEqual(json.loads((R/'design/requirements.json').read_text())['user_constraints']['materials'],['PLA','PET','TPU'])
    def test_lhs_reproducible(self):
        self.assertEqual(design_set(8),design_set(8))
    def test_full_size_study(self):
        self.assertEqual(len(design_set()),257)
    def test_seed_chamber(self):
        self.assertAlmostEqual(S2('C1-SEED').chamber_mm,125.6)
    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):S2('bad',eccentric_mm=-1)
    def test_labeled_motion_closes(self):
        for q in (6,8,16):
            c=S2('test',ratio_denominator=q)
            p=hook_polygon(c)
            self.assertTrue(np.allclose(transform(p,2*np.pi*q,c),transform(p,0,c)))
    def test_one_orbit_does_not_close_labeled_points(self):
        c=S2('test')
        self.assertFalse(np.allclose(transform(hook_polygon(c),2*np.pi,c),transform(hook_polygon(c),0,c)))
    def test_sampled_gap_is_not_smaller_than_bound(self):
        c=S2('test')
        k=kinematics(c,16)
        self.assertGreaterEqual(k['sampled_min_wall_gap_mm'],c.gap_mm-1e-8)
    def test_geometry_does_not_invent_breakage(self):
        k=kinematics(S2('test'),8)
        self.assertIsNone(k['throughput_g_h']);self.assertIsNone(k['cutting_torque_Nm'])
    def test_large_e_needs_larger_sleeve(self):
        a=packaging(S2('a',eccentric_mm=7));b=packaging(S2('b',eccentric_mm=14))
        self.assertLess(a['min_eccentric_sleeve_od_mm'],b['min_eccentric_sleeve_od_mm'])
    def test_high_ratio_not_free_small_cycloid(self):
        a=packaging(S2('a',eccentric_mm=14,ratio_denominator=16))
        self.assertFalse(a['compact_pin_family_possible'])
        self.assertGreater(a['pin_plate_od_screen_mm'],500)
    def test_hooks_not_ratio(self):
        c=S2('a',hooks=6,ratio_denominator=8)
        self.assertNotEqual(c.hooks,c.ratio_denominator)
    def test_c1_pin_reference_clearance(self):
        r=verify(S2('C1-SEED'),positions=97,profile_samples=1440)
        self.assertTrue(r['valid_profile']);self.assertGreater(r['minimum_sampled_pin_clearance_mm'],0)
    def test_speeds_coupled(self):
        c=S2('a',orbit_rpm=120,shear_ratio=3)
        r=kinematics(c,8)
        self.assertEqual(r['s1_rpm'],40)
        self.assertEqual(r['self_rpm'],-15)
    def test_contact_generalized_power_consistency(self):
        c=S2('j')
        p=np.array([55.,0.]);f=np.array([4.,20.]);theta=.71;omega=12.
        dt=1e-6
        velocity=(transform(p.reshape(1,2),theta+omega*dt,c)[0]-transform(p.reshape(1,2),theta-omega*dt,c)[0])/(2*dt)/1000
        self.assertAlmostEqual(generalized_torque(f,p,theta,c)*omega,float(f@velocity),places=7)
    def test_power_sum_not_two_independent_maxima(self):
        x=equivalent_motor_load(18,3,40,120,3000)
        self.assertAlmostEqual(x['motor_shaft_required_W'],x['s1_output_W']/.75+x['s2_output_W']/.8)
        self.assertGreater(x['motor_shaft_required_W'],140)

class ThermalTests(unittest.TestCase):
    def test_energy_conservation(self):
        r=thermal_run(Thermal(),duration_s=120)
        self.assertLess(abs(r['energy_balance_residual_J']),1e-6)
    def test_step_convergence(self):
        a=thermal_run(Thermal(),300,1);b=thermal_run(Thermal(),300,.5)
        self.assertLess(abs(a['final_shell_C']-b['final_shell_C']),.02)
    def test_hot_ambient_not_cooled_below_ambient(self):
        r=thermal_run(Thermal(ambient_C=35,inlet_C=35),300)
        self.assertGreater(r['final_shell_C'],35)
    def test_more_heat_increases_temperature(self):
        a=thermal_run(Thermal(chamber_heat_W=10),300)
        b=thermal_run(Thermal(chamber_heat_W=60),300)
        self.assertGreater(b['final_polymer_C'],a['final_polymer_C'])
    def test_bulk_can_be_hotter_than_wall(self):
        r=thermal_run(Thermal(),300)
        self.assertGreater(r['final_polymer_C'],r['final_shell_C'])
    def test_fan_failure_sensitivity(self):
        a=thermal_run(Thermal(chamber_UA_W_K=4,fan_factor=0),1000)
        b=thermal_run(Thermal(chamber_UA_W_K=4,fan_factor=1),1000)
        self.assertGreater(a['final_shell_C'],b['final_shell_C'])
    def test_hotend_bridge(self):
        a=thermal_run(Thermal(hotend_G_W_K=.005),300)
        b=thermal_run(Thermal(hotend_G_W_K=.1),300)
        self.assertGreater(b['final_shell_C'],a['final_shell_C'])
    def test_not_PETG(self):
        with self.assertRaises(ValueError):Thermal(material='PETG')
    def test_drive_heat_is_separate_from_chamber_heat(self):
        a=thermal_run(Thermal(motor_loss_W=0,gear_loss_W=0),300)
        b=thermal_run(Thermal(motor_loss_W=25,gear_loss_W=10),300)
        self.assertGreater(b['final_motor_C'],a['final_motor_C'])
        self.assertGreater(b['final_gear_C'],a['final_gear_C'])
    def test_repeated_batch_carries_heat_and_fan_fault_is_worse(self):
        segments=[dict(name='run1',duration_s=300,chamber_heat_W=30,motor_loss_W=25,gear_loss_W=10),
                  dict(name='idle',duration_s=120,chamber_heat_W=2,mass_flow_g_h=0),
                  dict(name='run2',duration_s=300,chamber_heat_W=30,motor_loss_W=25,gear_loss_W=10)]
        clean=thermal_duty_run(Thermal(ambient_C=35,inlet_C=35,chamber_UA_W_K=4),segments)
        failed=thermal_duty_run(Thermal(ambient_C=35,inlet_C=35,chamber_UA_W_K=4),
                                [{**x,'fan_factor':0} for x in segments])
        self.assertGreater(clean['segments'][2]['final_state_C'][0],clean['segments'][0]['final_state_C'][0])
        self.assertGreater(failed['peak_node_C'][2],clean['peak_node_C'][2])
    def test_cad_volume_capacity_basis(self):
        r=thermal_capacities_from_cad(json.loads((R/'results/cad_validation.json').read_text()))
        self.assertGreater(r['shear_metal_J_K'],0)
        self.assertGreater(r['shell_spreader_J_K'],0)
        self.assertEqual(r['status'],'CAD_VOLUME_DERIVED_ASSUMED_DENSITY_CP_NOT_MEASURED_MASS')

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(material='PLA',temperatures={k:25. for k in REQUIRED_SENSORS},sensor_age_s=0,
                       estop_closed=True,guards_closed=True,fan_ok=True,jam_detected=False,
                       drive_current_A=1,drive_rpm=120,drive_sample_age_s=0)
    def controller(self):
        return Controller(qualified=True,motor_limit_C=60,gear_limit_C=60,
                          current_limit_A=10,minimum_running_rpm=10)
    def test_default_qualification_hold(self):
        self.assertEqual(Controller().evaluate(**self.args)['state'],'QUALIFICATION_HOLD')
    def test_estop_disables_heat_and_motor(self):
        r=Controller().evaluate(**{**self.args,'estop_closed':False})
        self.assertFalse(r['heat_enable']);self.assertEqual(r['m1_fraction'],0)
    def test_missing_sensor(self):
        a=dict(self.args);a['temperatures']={'ambient':25}
        self.assertEqual(Controller().evaluate(**a)['state'],'FAULT')
    def test_nan_sensor(self):
        a=dict(self.args);a['temperatures']=dict(self.args['temperatures'],s2_shear=float('nan'))
        self.assertEqual(Controller().evaluate(**a)['state'],'FAULT')
    def test_stale_sensor(self):
        self.assertEqual(Controller().evaluate(**{**self.args,'sensor_age_s':2})['state'],'FAULT')
    def test_hot_requires_reset(self):
        c=self.controller()
        a=dict(self.args);a['temperatures']=dict(self.args['temperatures'],s2_shear=51)
        self.assertEqual(c.evaluate(**a)['state'],'FAULT')
        self.assertEqual(c.evaluate(**self.args)['state'],'FAULT')
        r=c.evaluate(**self.args,reset_edge=True)
        self.assertEqual(r['state'],'RESET_WAIT_START');self.assertEqual(r['m1_fraction'],0)
    def test_jam_no_reverse(self):
        r=Controller().evaluate(**{**self.args,'jam_detected':True})
        self.assertEqual(r['reason'],'JAM_NO_AUTOMATIC_REVERSE')
    def test_derate_changes_common_drive(self):
        c=self.controller()
        a=dict(self.args);a['temperatures']=dict(self.args['temperatures'],s2_shear=45)
        r=c.evaluate(**a,start_edge=True,run_request=True)
        self.assertEqual(r['m1_fraction'],.5)
        self.assertEqual(r['coupled_axes'],'S1_AND_S2_COMMON_SPEED_ONLY')
    def test_run_continues_without_repeated_start_edge(self):
        c=self.controller()
        self.assertEqual(c.evaluate(**self.args,start_edge=True,run_request=True)['state'],'RUN')
        self.assertEqual(c.evaluate(**self.args,run_request=True)['state'],'RUN')
        self.assertEqual(c.evaluate(**self.args,run_request=False)['state'],'IDLE')
    def test_hardware_overtemp_chain_is_fail_closed(self):
        r=self.controller().evaluate(**self.args,hardware_overtemp_closed=False)
        self.assertEqual(r['reason'],'HARDWARE_OVERTEMP_CHAIN_OPEN')
    def test_drive_feedback_required_to_run(self):
        a=dict(self.args);a['drive_current_A']=None
        self.assertEqual(self.controller().evaluate(**a,start_edge=True,run_request=True)['reason'],
                         'INVALID_DRIVE_FEEDBACK')
    def test_stale_drive_feedback(self):
        r=self.controller().evaluate(**{**self.args,'drive_sample_age_s':2},start_edge=True,run_request=True)
        self.assertEqual(r['reason'],'STALE_DRIVE_FEEDBACK')
    def test_current_and_rpm_detect_jam_without_reverse(self):
        r=self.controller().evaluate(**{**self.args,'drive_current_A':8.5,'drive_rpm':2},
                                     start_edge=True,run_request=True)
        self.assertEqual(r['reason'],'JAM_NO_AUTOMATIC_REVERSE')
        self.assertEqual(r['m1_fraction'],0)
    def test_operating_budget_derates_heater_without_exceeding_cap(self):
        for a in range(0,601,25):
            for b in range(0,121,20):
                for c in range(0,401,40):
                    r=allocate_power(a,b,30,c)
                    self.assertLessEqual(r['total_W'],500)
                    self.assertLessEqual(r['heater_W'],c)
        self.assertEqual(allocate_power(450,40,0,10)['total_W'],500)
        r=allocate_power(450,40,0,11)
        self.assertEqual((r['heater_W'],r['total_W'],r['reason']),
                         (10,500,'HEATER_DERATED_AT_OPERATING_CAP'))
        self.assertFalse(allocate_power(450,40,30,46)['admitted'])
        self.assertFalse(allocate_power(760,20,20,0)['admitted'])
        with self.assertRaises(ValueError):
            allocate_power(316,0,150,100,budget_W=792)
    def test_reject_phase_current_as_negative_power(self):
        with self.assertRaises(ValueError):allocate_power(-1,10,10,50)

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.design={'candidate_id':'TEST-ONLY','tip_mm':100}
        self.hashes=candidate_hashes([{'design':self.design}])

    def record(self,root,evidence_type='UNCALIBRATED_DEM'):
        raw=root/'raw.csv';raw.write_text('t,torque\n0,0\n')
        deck=root/'input.in';deck.write_text('run 1\n')
        return dict(evidence_type=evidence_type,candidate_id='TEST-ONLY',material='PLA',material_grade='test',material_lot='test',
                    feed_distribution_id='test',cad_revision='C2.0',geometry_sha256=self.hashes['TEST-ONLY'],
                    raw_data_path='raw.csv',raw_data_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                    solver='test-solver',solver_version='1',input_deck_path='input.in',
                    input_deck_sha256=hashlib.sha256(deck.read_bytes()).hexdigest(),outputs={k:0 for k in TARGETS})

    def test_empty_records_do_not_train(self):
        self.assertFalse(training_gate([],R)['trained'])
        self.assertEqual(training_gate([],R)['status'],'BLOCKED_PERFORMANCE_DATA')
    def test_geometric_pseudo_labels_rejected(self):
        with self.assertRaises(EvidenceError):validate_record({'evidence_type':'KINEMATICS'},R)
    def test_uncalibrated_DEM_rejected(self):
        with self.assertRaises(EvidenceError):validate_record({'evidence_type':'UNCALIBRATED_DEM'},R)
    def test_verified_experimental_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r=self.record(root,'PHYSICAL_EXPERIMENT')
            r.update(physical_test_id='run-1',specimen_id='coupon-1',procedure_revision='p1',instrument_ids=['loadcell-1'])
            self.assertEqual(validate_record(r,root,self.hashes,'C2.0'),r)
            r['raw_data_sha256']='bad'
            with self.assertRaises(EvidenceError):validate_record(r,root,self.hashes,'C2.0')
    def test_legitimate_uncalibrated_simulation_is_counted_but_not_qualified(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r=self.record(root)
            self.assertEqual(evidence_inventory([r],root,self.hashes,'C2.0')['actual_dem_runs'],1)
            with self.assertRaises(EvidenceError):validate_record(r,root,self.hashes,'C2.0')
    def test_calibration_promotes_dem_only_with_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r=self.record(root,'CALIBRATED_DEM');r['calibration_id']='cal-1'
            with self.assertRaises(EvidenceError):validate_record(r,root,self.hashes,'C2.0')
            r['calibration_validation_id']='held-out-1'
            self.assertEqual(validate_record(r,root,self.hashes,'C2.0'),r)
    def test_fake_physical_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(EvidenceError):validate_record(self.record(Path(td),'PHYSICAL_EXPERIMENT'),Path(td),self.hashes,'C2.0')
    def test_missing_raw_and_hash_tamper_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r=self.record(root);(root/'raw.csv').unlink()
            with self.assertRaises(EvidenceError):validate_evidence_record(r,root,self.hashes,'C2.0')
            r=self.record(root);r['input_deck_sha256']='bad'
            with self.assertRaises(EvidenceError):validate_evidence_record(r,root,self.hashes,'C2.0')
    def test_old_cad_or_geometry_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r=self.record(root);r['cad_revision']='C1'
            with self.assertRaises(EvidenceError):validate_evidence_record(r,root,self.hashes,'C2.0')
            r=self.record(root);r['geometry_sha256']='bad'
            with self.assertRaises(EvidenceError):validate_evidence_record(r,root,self.hashes,'C2.0')
    def test_synthetic_fixture_is_not_an_actual_run(self):
        r={'fixture_scope':'SYNTHETIC_TEST_ONLY'}
        self.assertEqual(evidence_inventory([r],R,self.hashes,'C2.0')['actual_dem_runs'],0)
    def test_pareto_preserves_tradeoff(self):
        self.assertEqual(nondominated(np.array([[1,3],[2,2],[3,3]])).tolist(),[True,True,False])
    def test_unknown_cost_not_zero_total(self):
        r=evaluate([dict(item_id='motor',owned_verified=False,landed_line_KRW=None)])
        self.assertIsNone(r['total_KRW']);self.assertIsNone(r['within_budget'])
    def test_soft_limit_accounting(self):
        r=evaluate([dict(item_id='motor',owned_verified=False,landed_line_KRW=100001,
                         quote_status='QUOTED_LANDED',source='seller quote')])
        self.assertEqual(r['status'],'OVER_SOFT_LIMIT')
    def test_valid_quote_reduces_unknown_coverage(self):
        r=evaluate([dict(item_id='motor',owned_verified=False,landed_line_KRW=12345,
                         quote_status='QUOTED_LANDED',source='seller quote')])
        self.assertEqual((r['unknown_cost_lines'],r['total_KRW']),([],12345.0))
        with self.assertRaises(ValueError):
            evaluate([dict(item_id='bad',owned_verified=False,landed_line_KRW=True,
                           quote_status='QUOTED_LANDED',source='seller quote')])
    def test_owned_only_does_not_imply_unowned_free(self):
        rows=json.loads((R/'bom/cost_ledger.json').read_text())
        self.assertGreater(len(rows),130)
        self.assertIn('DRV-M2',evaluate(rows)['unknown_cost_lines'])
    def test_jobs_have_no_fake_outputs(self):
        path=R/'experiments/dem_job_manifest.json'
        if path.exists():
            r=json.loads(path.read_text())
            self.assertTrue(all(x['status']=='BLOCKED_CALIBRATION_NOT_RUN' for x in r))
            self.assertTrue(all(v is None for x in r for v in x['outputs'].values()))

if __name__=='__main__':unittest.main()
