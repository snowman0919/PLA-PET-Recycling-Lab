"""Check published rated operating points; not physical motor acceptance."""
import hashlib, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KGF_CM_TO_NM = 0.0980665

def positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Expected a finite positive number')
    return float(value)

def operating_point(torque_nm, rpm, ratio, efficiency):
    torque_nm, rpm, ratio, efficiency = map(positive, (torque_nm, rpm, ratio, efficiency))
    if ratio < 1 or efficiency > 1:
        raise ValueError('Expected reduction ratio >=1 and efficiency <=1')
    return {'output_rpm': rpm / ratio, 'output_torque_nm': torque_nm * ratio * efficiency,
            'output_power_w': torque_nm * rpm * math.pi / 30 * efficiency}

def envelope(torque_nm, rpm, required_torque_nm, speed_limits, efficiency):
    lo, hi = map(positive, speed_limits)
    if lo > hi: raise ValueError('Invalid speed interval')
    point = operating_point(torque_nm, rpm, 1, efficiency)
    required_torque_nm = positive(required_torque_nm)
    minimum = max(1.0, rpm / hi, required_torque_nm / point['output_torque_nm'])
    maximum = rpm / lo
    return {'ratio_lower_bound': minimum, 'ratio_upper_bound': maximum,
            'rated_point_can_meet_current_envelope': minimum <= maximum,
            'max_rpm_at_required_torque_from_power': point['output_power_w'] * 30 / math.pi / required_torque_nm}

def main():
    baseline = ROOT / 'cad/parameters/baseline.json'
    data = json.loads(baseline.read_text())
    sources = json.loads((HERE / 'source_rows.json').read_text())
    rows = []
    for motor in sources['motors']:
        if motor['screenshot_selected_voltage_v'] != 24 or motor['screenshot_selected_rpm'] != motor['no_load_rpm']:
            raise ValueError('Published row does not match selected voltage/speed')
        torque = motor['rated_torque_kgf_cm'] * KGF_CM_TO_NM
        if motor['id'] == 'DRV-SH':
            spec = data['shredder']['motor']
            required, speeds = spec['required_cutter_continuous_torque_nm'], spec['required_cutter_speed_range_rpm']
            ratios = spec['secondary_ratio_options']
        else:
            spec = data['extruder']
            required, speeds = spec['continuous_drive_torque_nm'], spec['virtual_commissioning_rpm']
            ratios = [1.0, 2.0, 3.0, 4.0]
        rows.append({'id': motor['id'], 'rated_torque_nm': torque,
                     'rated_shaft_power_w': torque * motor['rated_rpm'] * math.pi / 30,
                     'source_applicability': 'SAME_BRAND_TABLE_ORDER_MATCH_NOT_CONFIRMED',
                     'required_torque_nm': required, 'required_rpm': speeds,
                     'ratio_cases': [dict(ratio=r, **operating_point(torque, motor['rated_rpm'], r, 1.0 if r == 1 else .85)) for r in ratios],
                     'efficiency_sensitivity': [dict(efficiency=e, **envelope(torque, motor['rated_rpm'], required, speeds, e)) for e in (.85, 1.0)]})
    paths = [Path(__file__), baseline, HERE/'source_rows.json', HERE/'user_reply.json']
    result = {'status': 'CONDITIONAL_RATED_POINT_SCREEN', 'physical_validation': 'NOT_RUN',
              'no_new_safety_factor_applied': True, 'runtime_or_geometry_changed': False, 'motors': rows,
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
