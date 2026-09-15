"""Separate external-loss reduction from heater enlargement and contact adequacy."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from analysis.thermal_revision_v08.model import ASSUMPTIONS
from analysis.thermal_revision_v08.steady_state import required_power


def loss_case(base, stations, zones, factor, contact, air, support):
    if isinstance(factor,bool) or not math.isfinite(factor) or not 0<factor<=1:
        raise ValueError('loss multiplier must be finite in (0,1]')
    answer=required_power(base,stations,zones,contact=contact,air=air*factor,support=support,
        overrides={'emissivity':ASSUMPTIONS['emissivity']*factor})
    answer.update(external_loss_multiplier=factor,contact_w_m2k=contact,
        reference_air_w_m2k=air,support_w_k=support,
        comparison_ceiling_c=ASSUMPTIONS['comparison_ceiling_c'],
        heater_comparison_exceeded=max(answer['heater_c'])>ASSUMPTIONS['comparison_ceiling_c'],
        hardware_solution_defined=False,supplier_rating_verified=False,
        mode='EMPTY_STEADY_INVERSE_CONSTRAINT_NOT_TRANSIENT_OR_FLOW')
    return answer


def main():
    base_path=ROOT/'cad/parameters/baseline.json'
    mount_path=ROOT/'cad/parameters/final_v08.json'
    radial_path=ROOT/'analysis/radial_support_v08/contract.json'
    paths=[Path(__file__).resolve(),base_path,mount_path,radial_path,
        Path(__file__).with_name('model.py').resolve(),Path(__file__).with_name('steady_state.py').resolve(),
        Path(__file__).with_name('model_inputs.json').resolve()]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    base=json.loads(base_path.read_text())['extruder']
    mount=json.loads(mount_path.read_text())['hot_zone_mount']
    radial=json.loads(radial_path.read_text())
    origin=ASSUMPTIONS['barrel_rear_x_mm']; half=mount['plate_thickness_mm']/2
    rear=(origin-mount['rear_fixed_plate_x_mm']-half)/1000
    stations={'current':[rear,(origin-mount['front_sliding_plate_x_mm']-half)/1000],
              'radial_review':[rear,(origin-radial['candidate_front_plate_x_mm']-half)/1000]}
    zones=base['heater_zone_axial_ranges_from_barrel_rear_mm']
    records=[]
    factors=(1.0,0.75,0.5,0.25)
    conditions=list(itertools.product(ASSUMPTIONS['contact_h_w_m2_k'],
        ASSUMPTIONS['air_h_w_m2_k'],ASSUMPTIONS['support_conductance_w_k']))
    for label,location in stations.items():
        for factor in factors:
            for contact,air,support in conditions:
                row=loss_case(base,location,zones,factor,contact,air,support)
                row['support_layout']=label; row['stations_mm']=[1000*x for x in location]
                records.append(row)
    summary=[]
    for label in stations:
        for factor in factors:
            subset=[r for r in records if r['support_layout']==label and r['external_loss_multiplier']==factor]
            summary.append({'support_layout':label,'external_loss_multiplier':factor,'cases':len(subset),
                'rated_power_feasible_count':sum(r['heating_only_feasible'] for r in subset),
                'meets_300C_comparison_and_power_count':sum(r['heating_only_feasible'] and not r['heater_comparison_exceeded'] for r in subset),
                'max_heater_c':max(max(r['heater_c']) for r in subset),
                'max_required_watts':[max(r['required_watts'][i] for r in subset) for i in range(4)]})
    if any(max(abs(r[k]) for k in ('local_residual_w','global_residual_w','sensor_residual_c'))>1e-6 for r in records):
        raise ValueError('steady inverse residual too large')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
        raise ValueError('source changed during loss-budget solve')
    report={'status':'LOSS_BUDGET_NUMERICAL_REVIEW_COMPLETE','source_sha256':hashes,
        'cases':records,'summary':summary,'rated_watts':base['heater_zone_power_w']+[base['die_heater_power_w']],
        'physical_validation_state':'NOT_RUN','fabrication_authorized':False,'energization_authorized':False,
        'hardware_solution_defined':False,'canonical_geometry_promoted':False,
        'limitations':[
            'Multiplier jointly scales convection and emissivity as a diagnostic, not a realized shield or insulation material.',
            'Contact conductance and support loss are unchanged within each comparison.',
            '300 C is an inherited comparison value, not an approved heater sheath rating.',
            'No PI tape credit, no increased installed power, no assumed qualified thermal material.',
            'Steady empty-barrel feasibility is necessary only; no transient stability, faults, polymer throughput or assembly authorization.',
            'Reducing external loss need not solve poor contact or make every zone controllable by heating alone.']}
    out=Path(__file__).resolve().parent/'results/loss_budget.json'
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(report['status'],'cases',len(records),json.dumps(summary),flush=True)


if __name__=='__main__': main()
