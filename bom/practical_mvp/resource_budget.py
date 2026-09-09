"""Resource arithmetic on existing part manifests, not new slicer/PSU tests."""
import json,math
from pathlib import Path
from build_plan import read_csv,sha,target_material
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
def finite(value):
    if isinstance(value,bool):raise ValueError('Boolean quantity')
    result=float(value)
    if not math.isfinite(result) or result<0:raise ValueError('Invalid resource amount')
    return result
def calculate(policy,prints,power):
    mass={'PLA':0.0,'ABS':0.0}
    for row in prints:
        target=target_material(row['part_id'],policy)
        if target!=row['material']:raise ValueError('Changed material requires re-slice, not relabeling')
        if row.get('slicer_status')!='PASS':raise ValueError('Missing prior slicer evidence')
        mass[target]+=finite(row['slicer_mass_total_g'])
    reserve=finite(policy['housing']['abs_reserve_g'])
    abs_stock=finite(policy['housing']['available_abs_g']);pla_stock=finite(policy['housing']['available_pla_g'])
    psu=policy['psu'];voltage=finite(psu['voltage_v']);capacity=finite(psu['reported_output_power_w'])
    cap=finite(psu['controller_continuous_limit_w'])
    if voltage!=power['psu_voltage_v'] or cap!=power['continuous_target_max_w']:raise ValueError('Operating contract silently changed')
    if psu['increase_controller_limit'] or psu['double_count_as_second_psu']:raise ValueError('Extra power or second PSU not authorized')
    if policy['ptc']['selected_for_mvp'] or not policy['ptc']['not_counted_in_dc_psu_w']:raise ValueError('Unqualified AC heater allocation')
    extrusion=sum(finite(power[k]) for k in ('heater_peak_w','extruder_peak_w','motion_fans_logic_peak_w'))
    shredding=sum(finite(power[k]) for k in ('shredder_peak_w','motion_fans_logic_peak_w'))
    if max(extrusion,shredding)>cap or cap>capacity:raise ValueError('Phase power exceeds limits')
    return {'status':'BUDGET_ARITHMETIC_PASS' if mass['ABS']+reserve<=abs_stock and mass['PLA']<=pla_stock else 'MATERIAL_BUDGET_EXCEEDED',
            'scope':'Existing 12 listed part types only; future full panels not included',
            'material_g':{k:round(v,2) for k,v in mass.items()},'abs_reserve_g':reserve,
            'abs_unallocated_after_reserve_g':round(abs_stock-mass['ABS']-reserve,2),
            'pla_unallocated_g':round(pla_stock-mass['PLA'],2),
            'power':{'reported_dc_capacity_w':capacity,'reported_dc_capacity_a':capacity/voltage,
                     'controller_cap_w':cap,'extrusion_phase_w':extrusion,'shredding_phase_w':shredding,
                     'headroom_against_reported_rating_w':capacity-max(extrusion,shredding),
                     'simultaneous_shred_and_heat_allowed':False,'legacy_model_rating_w':power['psu_rating_w'],
                     'physical_output_verified':False,'ptc_capacity_credit_w':0},
            'physical_validation':'NOT_RUN','machine_release':'HOLD'}
def main():
    policy=json.loads((HERE/'policy.json').read_text())
    prints=read_csv(ROOT/'exports/final/print/print_manifest.csv')
    paths=[HERE/'policy.json',Path(__file__),HERE/'build_plan.py',ROOT/'cad/parameters/baseline.json',ROOT/'exports/final/print/print_manifest.csv']
    source={str(p.relative_to(ROOT)):sha(p) for p in paths}
    result=calculate(policy,prints,json.loads(paths[3].read_text())['power'])
    artifacts=[]
    for row in prints:
        for field,digestfield in [('stl_file','sha256_stl'),('three_mf_file','sha256_3mf'),('step_reference_file','sha256_step')]:
            file=ROOT/'exports/final/print'/row[field]
            if sha(file)!=row[digestfield]:raise ValueError('Stale print artifact: '+str(file))
            artifacts.append(str(file.relative_to(ROOT)))
    if any(sha(ROOT/p)!=h for p,h in source.items()):raise ValueError('Input changed')
    result.update(source_sha256=source,existing_print_artifact_hashes_checked=len(artifacts),new_slicing_performed=False)
    (HERE/'generated/resource_budget.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},ensure_ascii=False))
if __name__=='__main__':main()
