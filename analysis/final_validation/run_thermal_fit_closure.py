"""Traceable thermal fit bounds. No material certification is inferred from arithmetic."""
from pathlib import Path
import json,math,hashlib,itertools
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hot_dimension(d,alpha,t,t0=20.):
    if not all(math.isfinite(v) for v in (d,alpha,t,t0)) or d<=0 or alpha<0:raise ValueError('dimension bounds')
    return d*(1+alpha*(t-t0))
def required_support_temperature(bore,od,ab,tb,asupport,t0=20.):
    if asupport<=0:raise ValueError('support CTE')
    return t0+(hot_dimension(od,ab,tb,t0)/bore-1)/asupport

def main():
    contract_path=ROOT/'analysis/final_validation/contracts/thermomechanical_closure_v08.json'
    contract=json.loads(contract_path.read_text());params=json.loads((ROOT/'cad/parameters/final_v08.json').read_text());base=json.loads((ROOT/'cad/parameters/baseline.json').read_text())
    t0=contract['reference_temperature_c'];rows=[]
    pairs=[('rear_plate',params['hot_zone_mount']['fixed_collar_bore_mm'],base['extruder']['barrel_od_mm']),('collar_through',params['hot_zone_mount']['fixed_collar_bore_mm'],base['extruder']['barrel_od_mm']),('collar_shoulder',params['rear_axial_retainer']['collar_counterbore_mm'],params['rear_axial_retainer']['barrel_integral_shoulder_od_mm']),('front_guide',params['hot_zone_mount']['sliding_guide_bore_mm'],base['extruder']['barrel_od_mm'])]
    for name,bore,od in pairs:
        for ab,tb,ts in itertools.product(contract['cte_sensitivity_per_k'],contract['barrel_temperature_cases_c'],contract['support_temperature_cases_c']):
            dc=hot_dimension(bore,contract['support_cte_sensitivity_per_k'],ts,t0)-hot_dimension(od,ab,tb,t0)
            rows.append({'pair':name,'nominal_bore_mm':bore,'nominal_od_mm':od,'barrel_alpha_per_k':ab,'barrel_c':tb,'support_c':ts,'diametral_clearance_mm':dc,'min_support_c_for_zero_clearance':required_support_temperature(bore,od,ab,tb,contract['support_cte_sensitivity_per_k'],t0),'free_clearance_pass':dc>=0})
    travel=[]
    for ab,tb in itertools.product(contract['cte_sensitivity_per_k'],contract['barrel_temperature_cases_c']):
        growth=hot_dimension(280.,ab,tb,t0)-280.
        travel.append({'alpha_per_k':ab,'barrel_c':tb,'reference_c':t0,'full_280mm_growth_mm':growth,'arithmetic_1p3_travel_margin_mm':params['hot_zone_mount']['cold_axial_travel_mm']-growth,'scope':'full-length arithmetic only; contact-specific axial datum and local effective length must be used for real obstruction'})
    result={'status':'HOLD_THERMAL_MATING_AND_ACTUAL_FIELD','physical_validation_state':'NOT_RUN','numeric_finite':all(math.isfinite(r['diametral_clearance_mm']) for r in rows),'nominal_dimension_pairs':rows,'full_length_arithmetic':travel,'decision':'Current bore limits are not free-sliding across the stated sensitivity envelope. Elastic contact may occur; interference volume alone does not prove yield or operational seizure. Do not enlarge holes without checking screw/barrel centring and thrust path.','source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),contract_path,ROOT/'cad/parameters/final_v08.json',ROOT/'cad/parameters/baseline.json']}}
    path=ROOT/'analysis/final_validation/results/v0.8/thermal_fit_closure.json';path.write_text(json.dumps(result,indent=2)+'\n')
    print('THERMAL_BOUND_RESULT',len(rows),'free-clearance failures',sum(not r['free_clearance_pass'] for r in rows),flush=True)
if __name__=='__main__':main()
