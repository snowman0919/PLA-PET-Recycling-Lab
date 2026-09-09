"""Synthetic regression cases for measurement uncertainty and real trace coverage."""
import json
import unittest
from pathlib import Path
from test_protocol import fixture, H
from validate_physical_test import evaluate, TEMPERATURES

class BoundaryTests(unittest.TestCase):
    def check(self, record, good=False, expected_hash=H):
        result = evaluate(record, expected_hash, 1100)
        self.assertEqual(result['status'] == 'MEASURED_DATA_WITHIN_TEST_PROTOCOL', good, result)
        self.assertEqual(result['machine_release'], 'HOLD')
        self.assertEqual(result['hardware_authorization'], 'NOT_GRANTED')
        self.assertEqual(result['measurement_authenticity'], 'NOT_ESTABLISHED_BY_PARSER')
        return result
    def mutate_sample(self, key, value):
        record = fixture(); record['samples'][3][key] = value
        return record
    def hot(self):
        record = fixture()
        for sample in record['samples']:
            for key in TEMPERATURES:
                sample[key] = 150.0
        record.update(heating_approval_reference='SYNTHETIC', independent_thermal_cutoff_verified=True, metal_shield_verified=True, peak_ramp_rate_c_per_min=1.5, ramp_trace_reference='SYNTHETIC')
        return record
    def test_good_bidirectional_cold(self): self.check(fixture(), True)
    def test_good_hot_hold(self): self.check(self.hot(), True)
    def test_not_run(self): self.assertEqual(self.check({'performed': False})['status'], 'NOT_RUN')
    def test_record_not_object(self): self.check([])
    def test_expected_hash_not_string(self): self.check(fixture(), expected_hash=None)
    def test_timestamp_duplicate(self): self.check(self.mutate_sample('time_s', 2))
    def test_timestamp_negative(self): self.check(self.mutate_sample('time_s', -1))
    def test_temperature_upper_uncertainty(self): self.check(self.mutate_sample('barrel_c', 299.9))
    def test_temperature_lower_uncertainty(self): self.check(self.mutate_sample('barrel_c', 20.1))
    def test_travel_uncertainty(self): self.check(self.mutate_sample('travel_mm', 2.999))
    def test_malformed_sample(self):
        r = fixture(); r['samples'][3] = None; self.check(r)
    def test_boolean_measurement(self): self.check(self.mutate_sample('pull_force_n', True))
    def test_nan_measurement(self): self.check(self.mutate_sample('time_s', float('nan')))
    def test_one_way_is_not_round_trip(self):
        r = fixture()
        for i, row in enumerate(r['samples']): row['travel_mm'] = -1.1 + 2.2*i/10
        self.check(r)
    def test_uncertain_stroke_is_insufficient(self):
        r = fixture()
        for row in r['samples']: row['travel_mm'] /= 1.1
        self.check(r)
    def test_lateral_load_lower_bound_not_qualified(self):
        r = fixture()
        for row in r['samples']: row['radial_load_n'] = 24.0
        self.check(r)
    def test_residual_uncertainty(self):
        r = fixture(); r['post_cooldown_residual_offset_mm'] = .019; self.check(r)
    def test_missing_residual_uncertainty(self):
        r = fixture(); r.pop('residual_position_uncertainty_mm'); self.check(r)
    def test_negative_residual_uncertainty(self):
        r = fixture(); r['residual_position_uncertainty_mm'] = -.001; self.check(r)
    def test_negative_ramp_claim(self):
        r = self.hot(); r['peak_ramp_rate_c_per_min'] = -1; self.check(r)
    def test_real_trace_overrides_ramp_claim(self):
        r = self.hot(); r['samples'][3]['barrel_c'] = 151.0; self.check(r)
    def test_heat_can_be_hidden_in_face_channel(self):
        r = fixture()
        for row in r['samples']:
            row['spring_face_a_c'] = row['spring_face_b_c'] = 100
        self.check(r)
    def test_negative_temperature_uncertainty(self): self.check(self.mutate_sample('temperature_uncertainty_c', -1))
    def test_required_strength_nan(self):
        result = evaluate(fixture(), H, float('nan'))
        self.assertEqual(result['status'], 'TEST_REVIEW_REQUIRED')
    def test_cli_data_is_not_hardware_approval(self):
        self.assertEqual(self.check(self.hot(), True)['hardware_authorization'], 'NOT_GRANTED')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'kind': 'SYNTHETIC_SOFTWARE_TESTS_ONLY', 'count': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'physical_validation_state': 'NOT_RUN'}
    (Path(__file__).parent / 'protocol_boundary_results.json').write_text(json.dumps(report, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
