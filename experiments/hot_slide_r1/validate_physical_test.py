"""Screen pressureless measurement records; never operate or authorize hardware."""
import json
import math
import re
import sys
from pathlib import Path

TEMPERATURES = ('barrel_c', 'spring_inner_c', 'spring_outer_c', 'spring_face_a_c', 'spring_face_b_c')
SAMPLE_KEYS = ('time_s', 'travel_mm', 'pull_force_n', 'radial_load_n', 'centre_x_mm', 'centre_y_mm', *TEMPERATURES, 'temperature_uncertainty_c', 'endplay_mm', 'force_uncertainty_n', 'position_uncertainty_mm')

def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def outcome(status, issues):
    return {'status': status, 'machine_release': 'HOLD', 'hardware_authorization': 'NOT_GRANTED', 'measurement_authenticity': 'NOT_ESTABLISHED_BY_PARSER', 'scope': 'Record screening only; not physical approval, fatigue or pressure qualification', 'issues': sorted(set(issues))}

def evaluate(record, geometry_sha256, required_yield_mpa):
    if not isinstance(record, dict):
        return outcome('TEST_REVIEW_REQUIRED', ['Measurement record must be an object'])
    if record.get('performed') is not True:
        return outcome('NOT_RUN', ['No performed measurement record'])
    issues = []
    if record.get('evidence_kind') != 'MEASURED':
        issues.append('Not a measured record')
    if not isinstance(geometry_sha256, str) or not re.fullmatch('[0-9a-f]{64}', geometry_sha256):
        issues.append('Invalid expected geometry hash')
    if record.get('geometry_sha256') != geometry_sha256:
        issues.append('Wrong geometry')
    if record.get('pressure_applied') is not False or record.get('powered_rotation') is not False:
        issues.append('Outside pressureless stationary scope')
    for key in ('operator', 'approval_reference', 'force_calibration_reference', 'position_calibration_reference', 'material_certificate_reference'):
        if not isinstance(record.get(key), str) or not record[key].strip():
            issues.append('Missing ' + key)
    if record.get('independent_mechanical_stops_verified') is not True:
        issues.append('No positive travel stops')
    samples = record.get('samples')
    if not isinstance(samples, list) or len(samples) < 10:
        issues.append('At least ten measured samples required')
        samples = []
    valid = []; last = None; hot = False; near_envelope = False
    for index, row in enumerate(samples):
        if not isinstance(row, dict) or any(not number(row.get(k)) for k in SAMPLE_KEYS):
            issues.append('Invalid sample ' + str(index)); continue
        valid.append(row)
        if row['time_s'] < 0 or (last is not None and row['time_s'] <= last['time_s']):
            issues.append('Time must be nonnegative and strictly increasing')
        uncertainties = [row[k] for k in ('force_uncertainty_n', 'position_uncertainty_mm', 'temperature_uncertainty_c')]
        if min(uncertainties) < 0:
            issues.append('Negative uncertainty')
        if abs(row['pull_force_n']) + row['force_uncertainty_n'] > 300:
            issues.append('Breakaway/drag exceeds prototype bound')
        if abs(row['radial_load_n']) + row['force_uncertainty_n'] > 25:
            issues.append('Radial load exceeds model scope')
        near_envelope |= abs(row['radial_load_n']) - row['force_uncertainty_n'] >= 24
        if math.hypot(row['centre_x_mm'], row['centre_y_mm']) + row['position_uncertainty_mm'] > .10:
            issues.append('Centreline drift exceeds test criterion')
        if abs(row['travel_mm']) + row['position_uncertainty_mm'] > 3:
            issues.append('Travel stop bound exceeded')
        temps = [row[k] for k in TEMPERATURES]
        u = row['temperature_uncertainty_c']
        if min(temps) - u < 20 or max(temps) + u > 300:
            issues.append('Temperature uncertainty interval outside analysis bounds')
        if abs(row['spring_face_a_c'] - row['spring_face_b_c']) + 2 * u > 10:
            issues.append('Through-thickness thermal gradient outside test bound')
        is_hot = max(temps) + u > 40
        hot |= is_hot
        lo, hi = (.10, .50) if is_hot else (.25, .35)
        if row['endplay_mm'] - row['position_uncertainty_mm'] < lo or row['endplay_mm'] + row['position_uncertainty_mm'] > hi:
            issues.append('Stack axial clearance outside acceptance')
        if last is not None and row['time_s'] > last['time_s']:
            minutes = (row['time_s'] - last['time_s']) / 60
            heating_rate = max((row[k] - last[k]) / minutes for k in TEMPERATURES)
            if (is_hot or max(last[k] for k in TEMPERATURES) > 40) and heating_rate > 2:
                issues.append('Measured sample interval exceeds heating ramp bound')
        last = row
    if not near_envelope:
        issues.append('No uncertainty-qualified near-envelope lateral-load measurement')
    if len(valid) != len(samples):
        issues.append('Incomplete numeric trace')
    if valid:
        lower = min(r['travel_mm'] + r['position_uncertainty_mm'] for r in valid)
        upper = max(r['travel_mm'] - r['position_uncertainty_mm'] for r in valid)
        if upper - lower < 2:
            issues.append('Insufficient uncertainty-qualified measured travel')
        movements = [(b['travel_mm'] - a['travel_mm'], a['position_uncertainty_mm'] + b['position_uncertainty_mm']) for a, b in zip(valid, valid[1:])]
        if not any(d > u for d, u in movements) or not any(d < -u for d, u in movements):
            issues.append('Bidirectional travel not demonstrated')
    else:
        issues.append('Insufficient measured travel')
    if hot:
        if not isinstance(record.get('heating_approval_reference'), str) or not record['heating_approval_reference'].strip() or record.get('independent_thermal_cutoff_verified') is not True or record.get('metal_shield_verified') is not True:
            issues.append('Hot-test authorization/protection incomplete')
        rate = record.get('peak_ramp_rate_c_per_min')
        if not number(rate) or not 0 <= rate <= 2 or not isinstance(record.get('ramp_trace_reference'), str) or not record['ramp_trace_reference'].strip():
            issues.append('Qualified slow-ramp trace missing')
    supplied = record.get('certified_yield_mpa_at_peak_temperature')
    if not number(required_yield_mpa) or required_yield_mpa <= 0 or not number(supplied) or supplied < required_yield_mpa:
        issues.append('Material strength evidence below required model bound')
    residual = record.get('post_cooldown_residual_offset_mm')
    uncertainty = record.get('residual_position_uncertainty_mm')
    if not number(residual) or not number(uncertainty) or residual < 0 or uncertainty < 0 or residual + uncertainty > .02:
        issues.append('Uncertainty-qualified permanent-set check missing or failed')
    return outcome('MEASURED_DATA_WITHIN_TEST_PROTOCOL' if not issues else 'TEST_REVIEW_REQUIRED', issues)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('usage: validate_physical_test.py RECORD_JSON GEOMETRY_SHA256 REQUIRED_YIELD_MPA')
    root = Path(__file__).resolve().parent
    from qualification.minimum_requirements import minimum_yield_floor
    try:
        floor = minimum_yield_floor(root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(outcome('TEST_REVIEW_REQUIRED', ['Strength evidence unavailable, stale or invalid: ' + type(exc).__name__])))
        raise SystemExit(1)
    requested = float(sys.argv[3])
    if not number(floor) or floor <= 0 or not number(requested) or requested < floor:
        print(json.dumps(outcome('TEST_REVIEW_REQUIRED', ['Requested material threshold below recorded requirement'])))
        raise SystemExit(1)
    record = json.loads(Path(sys.argv[1]).read_text())
    result = evaluate(record, sys.argv[2], requested)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'MEASURED_DATA_WITHIN_TEST_PROTOCOL' else 1)
