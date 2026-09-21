"""Reproduce C2 numerical results without CAD or any fabricated performance labels."""
import json
from dataclasses import replace
from pathlib import Path
from scipy.optimize import brentq
import numpy as np
import engineering
from engineering import (ROOT,S2,Thermal,thermal_run,thermal_matrix,thermal_duty_run,
                         thermal_capacities_from_cad,write_json)
from pin_constraint import verify
from costing import evaluate
from performance import ALLOWED_EVIDENCE,candidate_hashes,evidence_inventory,training_gate
from control import Controller,REQUIRED_SENSORS,allocate_power


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
            ua=brentq(lambda x:polymer(x)-target,c.natural_UA_W_K,100) if feasible else None
            required.append(dict(ambient_C=ambient,heat_W=heat,bulk_target_C=target,
                                 required_UA_W_K=ua,feasible_below_UA100=feasible,
                                 ideal_infinite_UA_bulk_C=polymer(1e8),
                                 evidence='ASSUMED_NETWORK_NOT_LOCAL_FLASH_TEMPERATURE'))
    write_json(ROOT/'results/required_cooling.json',required)
    cad=json.loads((ROOT/'results/cad_validation.json').read_text())
    capacity=thermal_capacities_from_cad(cad)
    duty=[]
    cp_by_material={'PLA':1800,'PET':1200,'TPU':1700}
    for material,cp in cp_by_material.items():
        for airflow,fan_factor in [('CLEAN_FILTER_ASSUMED',1),('CLOGGED_FILTER_SENSITIVITY',.25),
                                  ('FAN_FAILED_NATURAL_ONLY',0)]:
            segments=[]
            for cycle in range(1,4):
                segments.extend([
                    dict(name=f'batch_{cycle}',duration_s=600,chamber_heat_W=30,mass_flow_g_h=100,
                         motor_loss_W=25,gear_loss_W=8,fan_factor=fan_factor,inlet_C=35),
                    dict(name=f'idle_{cycle}',duration_s=300,chamber_heat_W=2,mass_flow_g_h=0,
                         motor_loss_W=2,gear_loss_W=1,fan_factor=fan_factor,inlet_C=35)])
            cfg=Thermal(material=material,cp_J_kg_K=cp,ambient_C=35,inlet_C=35,chamber_UA_W_K=4,
                        metal_heat_capacity_J_K=capacity['shear_metal_J_K'],
                        shell_heat_capacity_J_K=capacity['shell_spreader_J_K'])
            duty.append(dict(material=material,airflow=airflow,**thermal_duty_run(cfg,segments)))
    temperatures={k:25. for k in REQUIRED_SENSORS}
    control_base=dict(material='PLA',temperatures=temperatures,sensor_age_s=0,estop_closed=True,
                      guards_closed=True,fan_ok=True,jam_detected=False,drive_current_A=4,
                      drive_rpm=120,drive_sample_age_s=0,start_edge=True,run_request=True)
    def controller():
        return Controller(qualified=True,motor_limit_C=70,gear_limit_C=70,
                          current_limit_A=10,minimum_running_rpm=10)
    control_cases=[]
    for name,overrides in [('normal_reference',{}),('fan_failed',{'fan_ok':False}),
                           ('stale_temperature',{'sensor_age_s':2}),
                           ('stale_drive',{'drive_sample_age_s':2}),
                           ('hardware_overtemp_open',{'hardware_overtemp_closed':False}),
                           ('high_current_low_rpm',{'drive_current_A':8.5,'drive_rpm':2}),
                           ('buffer_full',{'buffer_full':True})]:
        result=controller().evaluate(**{**control_base,**overrides})
        control_cases.append(dict(name=name,state=result['state'],reason=result.get('reason'),
                                  m1_fraction=result['m1_fraction'],heat_enable=result['heat_enable']))
    write_json(ROOT/'results/p5_thermal_control.json',dict(
        status='UNCALIBRATED_DIGITAL_SENSITIVITY_AND_CONTROL_LOGIC_ONLY',
        cad_capacity_basis=capacity,thermal_cases=duty,control_cases=control_cases,
        assumptions={'ambient_C':35,'clean_installed_UA_W_K':4,'natural_UA_W_K':.3,
                     'active_chamber_loss_W':30,'active_motor_loss_W':25,'active_gear_loss_W':8,
                     'losses_are_assumed_not_motor_electrical_input':True,
                     'fan_failed_case':'FAULT_ENVELOPE_IF_STOP_OR_DETECTION_FAILS_NOT_A_RUN_COMMAND',
                     'fan_curve_and_filter_pressure_drop':'NOT_MEASURED',
                     'motor_and_gear_parameters':'UNSELECTED_ASSUMPTIONS'},
        did_not_run=['physical_thermal_test','fan_curve_test','sensor_delay_test','firmware_build',
                     'firmware_flash','energization'],
        hardware_safety_boundary=['independent_estop_and_guard_contactor_chain',
                                  'hardware_current_limit','manual_reset_overtemperature_chain',
                                  'one_shot_thermal_fuse']))
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
                   evidence_inventory=inventory,p5_thermal_cases=len(duty),
                   p5_control_cases=len(control_cases),
                   p5_status='DIGITAL_SENSITIVITY_COMPLETE_PHYSICAL_QUALIFICATION_HOLD')
    write_json(ROOT/'results/summary.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
