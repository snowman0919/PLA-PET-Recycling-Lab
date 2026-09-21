"""Reproduce C2 numerical results without CAD or any fabricated performance labels."""
import json
from dataclasses import replace
from pathlib import Path
from scipy.optimize import brentq
import numpy as np
import engineering
from engineering import ROOT,S2,Thermal,thermal_run,thermal_matrix,write_json
from pin_constraint import verify
from costing import evaluate
from performance import ALLOWED_EVIDENCE,candidate_hashes,evidence_inventory,training_gate
from control import allocate_power


def main():
    engineering.main()
    rows=json.loads((ROOT/'results/s2_candidates.json').read_text())
    checks=[verify(S2(**r['design'])) for r in rows if r['packaging']['kinematic_geometry_feasible'] and r['packaging']['compact_pin_family_possible']]
    write_json(ROOT/'results/pin_constraint_checks.json',checks)
    cost=evaluate(json.loads((ROOT/'bom/cost_ledger.json').read_text()))
    write_json(ROOT/'results/cost_status.json',cost)
    records=json.loads((ROOT/'experiments/performance_records.json').read_text())
    hashes=candidate_hashes(rows)
    revision=json.loads((ROOT/'design/requirements.json').read_text())['revision']
    inventory=evidence_inventory(records,ROOT/'experiments',hashes,revision)
    qualified=[r for r in records if r.get('evidence_type') in ALLOWED_EVIDENCE]
    gate=training_gate(qualified,ROOT/'experiments',geometry_hashes=hashes,expected_cad_revision=revision)
    write_json(ROOT/'results/performance_gate.json',gate)
    sensitivities=[]
    for gp in [.5,2,5]:
        for fraction in [.15,.35,.7]:
            r=thermal_run(Thermal(polymer_metal_G_W_K=gp,heat_to_polymer_fraction=fraction))
            sensitivities.append({k:v for k,v in r.items() if k not in ['trace','trace_columns']})
    write_json(ROOT/'results/contact_heat_sensitivity.json',sensitivities)
    required=[]
    for ambient in [25,30,35]:
        for heat in [10,30,60]:
            c=Thermal(ambient_C=ambient,inlet_C=ambient,chamber_heat_W=heat)
            def polymer(ua):
                C,K,b=thermal_matrix(replace(c,chamber_UA_W_K=ua))
                return float(np.linalg.solve(K,b)[0])
            target=45.
            feasible=polymer(100)<target
            ua=brentq(lambda x:polymer(x)-target,.001,100) if feasible else None
            required.append(dict(ambient_C=ambient,heat_W=heat,bulk_target_C=target,
                                 required_UA_W_K=ua,feasible_below_UA100=feasible,
                                 ideal_infinite_UA_bulk_C=polymer(1e8),
                                 evidence='ASSUMED_NETWORK_NOT_LOCAL_FLASH_TEMPERATURE'))
    write_json(ROOT/'results/required_cooling.json',required)
    power=[]
    for m1 in range(0,601,25):
        for m2 in range(0,121,20):
            for heater in range(0,401,40):power.append(allocate_power(m1,m2,30,heater))
    summary=json.loads((ROOT/'results/summary.json').read_text())
    trained=sum(json.loads(p.read_text()).get('trained') is True for p in
                [ROOT/'results/model_run/training_status.json',ROOT/'results/mlp_run/training_status.json'] if p.is_file())
    summary.update(pin_profiles_checked=len(checks),pin_profiles_with_nonnegative_sampled_clearance=sum(x['passed'] for x in checks),
                   minimum_checked_pin_clearance_mm=min(x['minimum_sampled_pin_clearance_mm'] for x in checks if x['valid_profile']),
                   cost_coverage_lines=len(json.loads((ROOT/'bom/cost_ledger.json').read_text())),unknown_cost_lines=len(cost['unknown_cost_lines']),
                   total_confirmed_cost_KRW=cost['total_KRW'],power_allocation_cases=len(power),
                   max_admitted_power_W=max(r['total_W'] for r in power),performance_gate=gate['status'],
                   actual_dem_runs=inventory['actual_dem_runs'],actual_physical_tests=inventory['actual_physical_tests'],
                   performance_models_trained=trained,budget_status=cost['status'],
                   evidence_inventory=inventory)
    write_json(ROOT/'results/summary.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
