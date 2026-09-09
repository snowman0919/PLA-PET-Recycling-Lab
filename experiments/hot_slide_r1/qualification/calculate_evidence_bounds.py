"""Read-only engineering evidence calculations. No equipment control."""
from pathlib import Path
import csv, hashlib, itertools, json, math
ROOT = Path(__file__).resolve().parent
EXP = ROOT.parent
REPO = EXP.parents[1]
KSI_MPA = 6.894757293168

def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Finite numeric input required')
    return float(value)

def pressure_force(pressure_mpa, bore_mm):
    p, d = finite(pressure_mpa), finite(bore_mm)
    if p < 0 or d <= 0:
        raise ValueError('Input outside calculation domain')
    return p * math.pi * d * d / 4

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def bolt_screen(total_force, preload, retained, thermal_delta, stiffness_fraction,
                proof_capacity, prying=2., bolts=2):
    values=[finite(x) for x in (total_force,preload,retained,thermal_delta,
                                stiffness_fraction,proof_capacity,prying,bolts)]
    total_force,preload,retained,thermal_delta,C,proof,prying,bolts=values
    if total_force<0 or preload<0 or not 0<=retained<=1 or not 0<=C<=1:
        raise ValueError('Invalid joint inputs')
    if proof<=0 or prying<1 or bolts<1 or bolts!=int(bolts):
        raise ValueError('Invalid capacity/count')
    effective=max(0.,preload*retained+thermal_delta)
    local=total_force*prying/bolts
    clamp=effective-(1-C)*local
    bolt=effective+C*local
    return {'per_bolt_external_bound_n':local,'effective_preload_n':effective,
            'residual_clamp_n':clamp,'bolt_load_before_separation_n':bolt,
            'proof_utilization':bolt/proof,'separation_predicted':clamp<=0,
            'above_proof_predicted':bolt>proof,'valid_before_separation_only':True}

def drag_budget(service_yield, base_requirement, stress_per_n, sheets=6):
    y,b,k,n=[finite(v) for v in (service_yield,base_requirement,stress_per_n,sheets)]
    if y<=0 or b<=0 or k<=0 or n<1: raise ValueError('Invalid drag budget')
    return {'base_strength_feasible':y>=b,'conditional_max_drag_per_carrier_n':max(0.,(y-b)*n/(2*k))}

def main():
    axial=json.loads((ROOT/'results/axial_drag.json').read_text())
    envelope=json.loads((EXP/'sliding_envelope.json').read_text())
    rows=list(csv.DictReader((ROOT/'naca4075_selected.csv').open()))
    observed=[float(r['yield_ksi'])*KSI_MPA for r in rows if float(r['temperature_f'])==600]
    material={'paper_temperature_c':(600-32)*5/9,'paper_yield_range_mpa':[min(observed),max(observed)],
              'source_id':'NACA4075','source_scope':'1.27 mm TH1050, 30 minutes; not current product/lot',
              'applicability_to_current_3mm_CH900':'NOT_ESTABLISHED',
              'heat_treatment_dimensional_example_mm':16.86*.004,
              'dimensional_example_tolerance_ratio':16.86*.004/.01,
              'required_yield_with_assumed_axial_drag_mpa':axial['strength_requirement_including_assumed_drag_mpa']}
    retention_path=REPO/'analysis/final_validation/results/v0.8/axial_retainer_qualification.json'
    retention=json.loads(retention_path.read_text())
    normal=envelope['maximum_total_normal_force_per_carrier_n']
    pressure=pressure_force(6.,16.22)
    proof=retention['m4_class88_proof_safety_factor']*retention['design_bolt_load_n']
    cases=[]
    for mu,retained,delta,C,proof_ratio,preload in itertools.product(
            (0.,.1,.25,.4,.6,1.),(1.,.8,.6),(-1000.,0.,1000.),(.1,.3,.5),
            (1.,.8,.6),retention['calculated_preload_range_n']):
        drag=2*normal*mu
        joint=bolt_screen(pressure+drag,preload,retained,delta,C,proof*proof_ratio)
        cases.append({'assumed_mu':mu,'retained_preload_fraction':retained,
                      'assumed_thermal_preload_delta_n':delta,'assumed_stiffness_fraction':C,
                      'assumed_hot_proof_fraction':proof_ratio,'initial_preload_n':preload,
                      'two_carrier_drag_bound_n':drag,'total_retainer_load_bound_n':pressure+drag,
                      **joint})
    result={'status':'HOLD_PENDING_MATERIAL_FRICTION_AND_JOINT_EVIDENCE',
            'physical_validation':'NOT_RUN','material_applicability':material,
            'pressure_load_case_n':pressure,'normal_sum_per_carrier_bound_n':normal,
            'two_carrier_drag_at_mu025_n':2*normal*.25,
            'retainer_additive_bound_at_mu025_n':pressure+2*normal*.25,
            'bearing_dynamic_load_ratio_not_safety_factor':10600/pressure,
            'bearing_static_load_ratio_reference':16800/pressure,
            'bolt_cold_reference_proof_capacity_n':proof,'cases':cases,
            'case_count':len(cases),'separation_case_count':sum(c['separation_predicted'] for c in cases),
            'above_proof_case_count':sum(c['above_proof_predicted'] for c in cases),
            'limitations':['6 MPa is a specified blocked-die case, not inferred from motor current.',
                'Drag is conservatively added in the retainer path; it is not automatically added to the screw bearing.',
                'Preload, prying, stiffness and hot-capacity factors are sensitivity assumptions, not measured conditions.',
                'The bearing ratios do not establish temperature, lubrication, reverse-thrust or whole-frame qualification.'],
            'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in (
                Path(__file__),ROOT/'naca4075_selected.csv',ROOT/'results/axial_drag.json',
                EXP/'sliding_envelope.json',retention_path)}}
    stress_per_n=max(r['result']['max_von_mises_mpa'] for r in axial['runs'])/25
    result['material_drag_tradeoff']=[{'hypothetical_service_yield_mpa':y,**drag_budget(y,axial['previous_strength_requirement_mpa'],stress_per_n)} for y in (1000.,1100.,1250.,1400.)]
    result['material_drag_tradeoff_limits']='Equal load sharing across six sheets; hypothetical certificates; not a machine or test rating'
    (ROOT/'results/evidence_bounds.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','source_sha256')},indent=2))

if __name__=='__main__': main()
