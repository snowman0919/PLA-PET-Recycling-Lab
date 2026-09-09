"""Geometry-specific movement and pressure audit; not a pressure/fit approval."""
from pathlib import Path
import hashlib, itertools, json, math
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Expected finite positive number')
    return float(value)

def growth(length_mm, alpha_per_k, delta_c):
    positive(length_mm); positive(alpha_per_k)
    if not math.isfinite(delta_c):
        raise ValueError('Nonfinite temperature difference')
    return length_mm * alpha_per_k * delta_c

def thrust(pressure_mpa, diameter_mm):
    return positive(pressure_mpa) * math.pi * positive(diameter_mm)**2 / 4

def gap(hole_mm, body_mm, body_alpha, body_c, support_alpha, support_c, reference_c=20.):
    for value in (hole_mm, body_mm, body_alpha, support_alpha):
        positive(value)
    if not all(math.isfinite(t) for t in (body_c, support_c, reference_c)):
        raise ValueError('Nonfinite temperature')
    return hole_mm*(1+support_alpha*(support_c-reference_c))-body_mm*(1+body_alpha*(body_c-reference_c))

def main():
    baseline = json.loads((ROOT/'cad/parameters/baseline.json').read_text())
    parameters = json.loads((ROOT/'cad/parameters/final_v08.json').read_text())
    geometry = json.loads((HERE/'geometry.json').read_text())
    for rel, expected in geometry['source_sha256'].items():
        if sha(ROOT/rel) != expected:
            raise ValueError('Stale geometry source: '+rel)
    objects = {r['name']: r for r in geometry['parts']}
    barrel = objects['Barrel']['bbox_mm']; guide = objects['ExtruderFrontSlidingGuide']['bbox_mm']
    mount = parameters['hot_zone_mount']; rear = parameters['rear_axial_retainer']
    datum = barrel[3]-rear['barrel_shoulder_length_mm']
    if not barrel[0] < guide[0] < guide[3] < datum < barrel[3]:
        raise ValueError('Unexpected station order')
    span = datum-guide[0]; total = datum-barrel[0]
    cases = []
    for alpha, temp in itertools.product((12.3e-6, 17e-6), (270.,300.)):
        cases.append({'alpha_per_k': alpha, 'barrel_uniform_bound_c': temp,
            'guide_max_travel_mm': growth(span,alpha,temp-20.),
            'barrel_front_travel_mm': growth(total,alpha,temp-20.),
            'guide_clearance_nominal_mm': gap(mount['sliding_guide_bore_mm'],34.,alpha,temp,12e-6,20.),
            'rear_bore_clearance_nominal_mm': gap(mount['fixed_collar_bore_mm'],34.,alpha,temp,12e-6,20.),
            'shoulder_pocket_clearance_nominal_mm': gap(rear['collar_counterbore_mm'],44.,alpha,temp,12e-6,20.)})
    pressures = []
    for name,key in (('normal_model','normal_pressure_mpa'),('blocked_die_design_case','trip_pressure_equivalent_mpa')):
        pressure=baseline['extruder'][key];force=thrust(pressure,16.22)
        pressures.append({'id':name,'pressure_mpa':pressure,'force_n':force,
            'kgf':force/9.80665,'tonne_force':force/9806.65,'measured':False})
    sources = [Path(__file__).resolve(),HERE/'geometry.json',ROOT/'cad/parameters/final_v08.json',ROOT/'cad/parameters/baseline.json']
    result = {'status':'SCOPED_ANALYTICAL_AUDIT_NOT_FABRICATION_APPROVAL',
        'physical_validation':'NOT_RUN','machine_release':'HOLD',
        'datum_x_mm':datum,'guide_x_range_mm':[guide[0],guide[3]],
        'datum_to_guide_max_mm':span,'datum_to_barrel_front_mm':total,
        'datum_sensitivity': {'assumed_existing_model_datum_x_mm':datum, 'other_shoulder_face_x_mm':barrel[3], 'guide_travel_upper_other_face_mm':growth(barrel[3]-guide[0],17e-6,280.), 'reason':'Axial contact face/endplay must be resolved by final assembly; no hidden datum assumption'},
        'existing_declared_axial_travel_mm':mount['cold_axial_travel_mm'],
        'cases':cases,'pressures':pressures,
        'limitations':[
            'Nominal geometry only: tolerances, shaft/barrel alignment and pressure strain are not closed here.',
            'Uniform barrel temperature and cold support are sensitivities, not measured operating states.',
            'A nominal radial gap does not prove sliding, bearing contact, retained alignment or friction.',
            'A specified 6 MPa case is not a verified pressure trip and is not inferred from motor current.',
            '1,222 MPa is an HS-R1-S2-specific strength screen, not a machine extrusion-pressure requirement.'
        ],'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources}}
    (HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
