"""Source-bound radial load, free seating and thermal-axis sensitivity review."""
from __future__ import annotations
import hashlib,itertools,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from analysis.radial_support_v08.mechanics import reactions,capture_lift,axis_at,seated_thermal_shift


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=Path(__file__).resolve(); contract=source.with_name('contract.json')
    baseline=ROOT/'cad/parameters/baseline.json'; params=ROOT/'cad/parameters/final_v08.json'
    spec=json.loads(contract.read_text()); base=json.loads(baseline.read_text())['extruder']
    mount=json.loads(params.read_text())['hot_zone_mount']
    paths=[source,contract,source.with_name('mechanics.py'),baseline,params,
        ROOT/'analysis/thermal_revision_v08/steady_state.py',ROOT/'analysis/thermal_revision_v08/model.py',
        ROOT/'analysis/thermal_revision_v08/model_inputs.json']
    geometry_path=source.with_name('results')/'geometry.json'
    geometry=json.loads(geometry_path.read_text()); paths.append(geometry_path)
    if not all(sha(ROOT/p)==h for p,h in geometry['source_sha256'].items()): raise ValueError('stale candidate CAD')
    stations=geometry['cad_stations_mm']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    length=spec['barrel_length_mm']; radius=base['barrel_od_mm']/2
    weight=math.pi*(base['barrel_od_mm']**2-base['barrel_id_mm']**2)/4*length*1e-9*spec['steel_density_kg_m3']*9.80665
    rear=spec['barrel_rear_x_mm']-mount['rear_fixed_plate_x_mm']-mount['plate_thickness_mm']/2
    current=spec['barrel_rear_x_mm']-mount['front_sliding_plate_x_mm']-mount['plate_thickness_mm']/2
    proposed=spec['barrel_rear_x_mm']-spec['candidate_front_plate_x_mm']-mount['plate_thickness_mm']/2
    old=reactions(length,rear,current,weight,spec['tip_load_n'])
    new=reactions(length,rear,proposed,weight,spec['tip_load_n'])
    if abs(rear-(stations['barrel_rear_y']-stations['rear_plate_y']))>1e-6 or abs(proposed-(stations['barrel_rear_y']-stations['candidate_front_y']))>1e-6: raise ValueError('CAD support station mismatch')
    lift=capture_lift(mount['fixed_collar_bore_mm']/2,radius,stations['rear_lip_top_z']-spec['axis_z_mm'])
    drop=(mount['sliding_guide_bore_mm']-base['barrel_od_mm'])/2
    inherited_axis={str(x):axis_at(x,rear,current,lift,-drop) for x in (0.,length)}
    candidate_drop=(spec['candidate_front_bore_mm']-base['barrel_od_mm'])/2
    cold=spec['cold_axis_setting_mm']; tolerance=spec['cold_axis_setting_tolerance_mm']
    seats=[]
    for alpha,tbar,tsupport,outer in itertools.product(spec['barrel_cte_per_k'],
            spec['barrel_temperature_c'],spec['support_temperature_c'],(33.97,34.0)):
        r=outer/2; bore=spec['candidate_front_bore_mm']/2
        height=spec['axis_z_mm']-spec['foot_z_mm']+(bore-r)+cold
        shift=seated_thermal_shift(height,bore,r,tsupport,tbar,spec['support_cte_per_k'],alpha)
        seats.append(dict(barrel_c=tbar,support_c=tsupport,barrel_cte=alpha,outer_mm=outer,
                          thermal_axis_shift_mm=shift))
    low=cold-tolerance+min(r['thermal_axis_shift_mm'] for r in seats)
    high=cold+tolerance+max(r['thermal_axis_shift_mm'] for r in seats)
    axes=[axis_at(x,rear,proposed,za,zb) for x,za,zb in itertools.product((0.,length),(low,high),(low,high))]
    error=max(abs(v) for v in axes)
    hot_gaps=[(16.20*(1+alpha*(tb-20))-15.92*(1+alpha*(ts-20)))/2
              for alpha,(tb,ts) in itertools.product(spec['barrel_cte_per_k'],((245.,270.),(270.,245.)))]
    result=dict(status='RADIAL_SUPPORT_ARITHMETIC_REVIEW_COMPLETE',source_sha256=hashes,
        barrel_only_weight_n=weight,supports_mm=dict(rear=rear,current_front=current,candidate_front=proposed),
        current_reactions=old,candidate_reactions=new,
        free_seating_diagnostic=dict(rear_up_mm=lift,front_down_mm=drop,
            extrapolated_barrel_axis_mm=inherited_axis,
            scope='Unconstrained rigid seating limit, NOT actual motion; screw/feed/thrust contact would redistribute load'),
        candidate_unadjusted_cold_drop_mm=candidate_drop,
        proposed_axis_setting=dict(nominal_mm=cold,tolerance_mm=tolerance,
            support_axis_range_mm=[low,high],whole_barrel_axis_error_bound_mm=error,
            minimum_reference_hot_radial_gap_mm=min(hot_gaps),
            residual_budget_before_runout_bending_eccentricity_mm=min(hot_gaps)-error),
        thermal_seating_cases=seats)
    from analysis.thermal_revision_v08.steady_state import required_power
    thermal=[]
    for front,h,air,g in itertools.product((current,proposed),(200.,1000.),(8.,15.),(.05,.2)):
        row=required_power(base,[rear/1000,front/1000],base['heater_zone_axial_ranges_from_barrel_rear_mm'],
                           contact=h,air=air,support=g)
        thermal.append(dict(front_station_mm=front,contact_h=h,air_h=air,support_g=g,**row))
    result['steady_thermal_cases']=thermal
    result['checks']=dict(force_balance=max(abs(v['force_residual_n']) for v in (old,new))<1e-10,
        moment_balance=max(abs(v['moment_residual_nmm']) for v in (old,new))<1e-8,
        candidate_reactions_compressive=min(new['rear_n'],new['front_n'])>0,
        candidate_75n_analysis_load_exceeds_twice_nominal=spec['proof_load_n']>=2*max(new['rear_n'],new['front_n']),
        numerical_heat_balance=all(abs(v['global_residual_w'])<1e-7 for v in thermal),
        sources_unchanged=all(sha(ROOT/p)==h for p,h in hashes.items()))
    result.update(candidate_all_thermal_cases_feasible=all(v['heating_only_feasible'] for v in thermal if v['front_station_mm']==proposed),
        canonical_geometry_promoted=False,physical_validation_state='NOT_RUN',fabrication_authorized=False,
        energization_authorized=False,design_acceptance='HOLD_PENDING_INTEGRATED_THERMAL_ALIGNMENT_AND_JOINT_QUALIFICATION',
        limitations=spec['limitations']+[
            'Whole-barrel axis bound excludes screw runout, barrel ID/OD eccentricity, rail/plate deflection and feed/thrust alignment.',
            'Positive nominal reactions do not bound impact, operator loads, cable drag, or all possible extrusion loads.',
            'A change of support location shifts thermal losses; it does not solve the existing heater power deficit.'
        ])
    if not all(result['checks'].values()): result['status']='FAIL'
    path=source.with_name('results')/'review.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['status'],json.dumps({k:result[k] for k in ('current_reactions','candidate_reactions','proposed_axis_setting','candidate_all_thermal_cases_feasible')}),flush=True)
    if result['status']=='FAIL': raise SystemExit(1)


if __name__=='__main__': main()
