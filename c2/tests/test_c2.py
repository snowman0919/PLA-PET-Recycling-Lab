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
from engineering import S2,Thermal,design_set,packaging,hook_polygon,transform,kinematics,thermal_run,equivalent_motor_load,generalized_torque,point_jacobian
from control import Controller,allocate_power,REQUIRED_SENSORS
from performance import validate_record,training_gate,EvidenceError,nondominated,TARGETS
from costing import evaluate
from pin_constraint import verify

class GeometryTests(unittest.TestCase):
    def test_psu_and_total_budget(self):
        c=json.loads((R/'design/requirements.json').read_text())['user_constraints']
        self.assertEqual((c['psu_V'],c['psu_rated_W'],c['operational_cap_W']),(24,800,500))
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
        a=thermal_run(Thermal(chamber_UA_W_K=.5),1000)
        b=thermal_run(Thermal(chamber_UA_W_K=4),1000)
        self.assertGreater(a['final_shell_C'],b['final_shell_C'])
    def test_hotend_bridge(self):
        a=thermal_run(Thermal(hotend_G_W_K=.005),300)
        b=thermal_run(Thermal(hotend_G_W_K=.1),300)
        self.assertGreater(b['final_shell_C'],a['final_shell_C'])
    def test_not_PETG(self):
        with self.assertRaises(ValueError):Thermal(material='PETG')

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(material='PLA',temperatures={k:25. for k in REQUIRED_SENSORS},sensor_age_s=0,
                       estop_closed=True,guards_closed=True,fan_ok=True,jam_detected=False)
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
        c=Controller(qualified=True,motor_limit_C=60,gear_limit_C=60)
        a=dict(self.args);a['temperatures']=dict(self.args['temperatures'],s2_shear=51)
        self.assertEqual(c.evaluate(**a)['state'],'FAULT')
        self.assertEqual(c.evaluate(**self.args)['state'],'FAULT')
        r=c.evaluate(**self.args,reset_edge=True)
        self.assertEqual(r['state'],'RESET_WAIT_START');self.assertEqual(r['m1_fraction'],0)
    def test_jam_no_reverse(self):
        r=Controller().evaluate(**{**self.args,'jam_detected':True})
        self.assertEqual(r['reason'],'JAM_NO_AUTOMATIC_REVERSE')
    def test_derate_changes_common_drive(self):
        c=Controller(qualified=True,motor_limit_C=60,gear_limit_C=60)
        a=dict(self.args);a['temperatures']=dict(self.args['temperatures'],s2_shear=45)
        r=c.evaluate(**a,start_edge=True,run_request=True)
        self.assertEqual(r['m1_fraction'],.5)
        self.assertEqual(r['coupled_axes'],'S1_AND_S2_COMMON_SPEED_ONLY')
    def test_run_continues_without_repeated_start_edge(self):
        c=Controller(qualified=True,motor_limit_C=60,gear_limit_C=60)
        self.assertEqual(c.evaluate(**self.args,start_edge=True,run_request=True)['state'],'RUN')
        self.assertEqual(c.evaluate(**self.args,run_request=True)['state'],'RUN')
        self.assertEqual(c.evaluate(**self.args,run_request=False)['state'],'IDLE')
    def test_power_cap_many_cases(self):
        for a in range(0,601,25):
            for b in range(0,121,20):
                for c in range(0,401,40):
                    r=allocate_power(a,b,30,c)
                    self.assertLessEqual(r['total_W'],500)
    def test_reject_phase_current_as_negative_power(self):
        with self.assertRaises(ValueError):allocate_power(-1,10,10,50)

class EvidenceTests(unittest.TestCase):
    def test_empty_records_do_not_train(self):
        self.assertFalse(training_gate([],R)['trained'])
        self.assertEqual(training_gate([],R)['status'],'BLOCKED_PERFORMANCE_DATA')
    def test_geometric_pseudo_labels_rejected(self):
        with self.assertRaises(EvidenceError):validate_record({'evidence_type':'KINEMATICS'},R)
    def test_uncalibrated_DEM_rejected(self):
        with self.assertRaises(EvidenceError):validate_record({'evidence_type':'UNCALIBRATED_DEM'},R)
    def test_verified_experimental_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'raw.csv';p.write_text('t,torque\n0,0\n')
            r=dict(evidence_type='PHYSICAL_EXPERIMENT',candidate_id='TEST-ONLY',material='PLA',material_grade='test',material_lot='test',
                   feed_distribution_id='test',calibration_id='test',cad_revision='test',raw_data_path='raw.csv',
                   raw_data_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),outputs={k:0 for k in TARGETS})
            self.assertEqual(validate_record(r,Path(td)),r)
            r['raw_data_sha256']='bad'
            with self.assertRaises(EvidenceError):validate_record(r,Path(td))
    def test_pareto_preserves_tradeoff(self):
        self.assertEqual(nondominated(np.array([[1,3],[2,2],[3,3]])).tolist(),[True,True,False])
    def test_unknown_cost_not_zero_total(self):
        r=evaluate([dict(item_id='motor',owned_verified=False,landed_line_KRW=None)])
        self.assertIsNone(r['total_KRW']);self.assertIsNone(r['within_budget'])
    def test_soft_limit_accounting(self):
        r=evaluate([dict(item_id='motor',owned_verified=False,landed_line_KRW=100001)])
        self.assertEqual(r['status'],'OVER_SOFT_LIMIT')
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
