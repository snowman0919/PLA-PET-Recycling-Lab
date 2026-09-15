"""Four-way factorial comparison with independent temporal/spatial refinement."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
from .model import ASSUMPTIONS as A, thermal_screen, refinement_error

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'analysis/final_validation/results/v0.8/hot_zone_revision_review.json'


def configurations():
    base = json.loads((ROOT/'cad/parameters/baseline.json').read_text())['extruder']
    mount = json.loads((ROOT/'cad/parameters/final_v08.json').read_text())['hot_zone_mount']
    archive = json.loads(Path(__file__).with_name('reference_geometry.json').read_text())
    oldbase = archive['files']['cad/parameters/baseline.json']['data']['extruder']
    oldmount = archive['files']['cad/parameters/final_v08.json']['data']['hot_zone_mount']
    invariant = ['barrel_od_mm','barrel_id_mm','heater_zone_power_w',
                 'barrel_sensor_bores_mm','pet_zone_c','die_heater_power_w','pet_die_c']
    if any(base[k]!=oldbase[k] for k in invariant):
        raise ValueError('comparison requires additional changed-input factor')
    def supports(m):
        return [(A['barrel_rear_x_mm']-m[key]-m['plate_thickness_mm']/2)/1000
                for key in ('rear_fixed_plate_x_mm','front_sliding_plate_x_mm')]
    before=oldbase['heater_zone_axial_ranges_from_barrel_rear_mm']
    after=base['heater_zone_axial_ranges_from_barrel_rear_mm']
    if before[0]!=[45,90] or before[1:]!=after[1:]:
        raise ValueError('historical heater geometry mismatch')
    cases={'reference':(supports(oldmount),before), 'width_only':(supports(oldmount),after),
           'support_only':(supports(mount),before),'combined':(supports(mount),after)}
    return base,mount,archive,cases


def run(beam_solver):
    base,mount,archive,configs=configurations()
    source_paths=[ROOT/p for p in ['cad/parameters/baseline.json','cad/parameters/final_v08.json',
        'cad/freecad/compact/geometry.py','cad/freecad/compact/manufacturing.py',
        'cad/freecad/final_v08/generate.py','cad/freecad/drive_v08/assembly.py',
        'analysis/final_validation/hot_zone_revision_review.py',
        'analysis/thermal_revision_v08/reference_geometry.json',
        'analysis/thermal_revision_v08/model_inputs.json','analysis/thermal_revision_v08/model.py',
        'analysis/thermal_revision_v08/compare.py']]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    beams={name:[beam_solver(st,base['barrel_od_mm']/1000,base['barrel_id_mm']/1000,mesh)
                 for mesh in (28,56,112)] for name,(st,_) in configs.items()}
    cases=[]; convergence=[]
    for name,(stations,zones) in configs.items():
        for contact,air,support in itertools.product(A['contact_h_w_m2_k'],
                A['air_h_w_m2_k'],A['support_conductance_w_k']):
            args=(base,stations,zones,contact,air,support)
            dt=A['timestep_s']; dx=A['mesh_mm']/1000; levels=[]
            coarse=thermal_screen(*args,dt=dt,dx=dx,duration=A['duration_s'])
            for level in range(6):
                temporal=thermal_screen(*args,dt=dt/2,dx=dx,duration=A['duration_s'])
                time_error=refinement_error(coarse,temporal)
                levels.append({'dt_s':dt,'next_dt_s':dt/2,'error_c':time_error})
                if time_error<=A['convergence_tolerance_c']: break
                dt/=2; coarse=temporal
            space_levels=[]
            for level in range(4):
                spatial=thermal_screen(*args,dt=dt/2,dx=dx/2,duration=A['duration_s'])
                space_error=refinement_error(temporal,spatial)
                space_levels.append({'dx_mm':dx*1000,'next_dx_mm':dx*500,'error_c':space_error})
                if space_error<=A['convergence_tolerance_c']: break
                dx/=2; temporal=spatial
            final_time_levels=[]
            final_dt=spatial['timestep_s']; final_dx=spatial['mesh_mm']/1000
            for level in range(6):
                finer=thermal_screen(*args,dt=final_dt/2,dx=final_dx,duration=A['duration_s'])
                final_error=refinement_error(spatial,finer)
                final_time_levels.append({'dt_s':final_dt,'next_dt_s':final_dt/2,'error_c':final_error})
                spatial=finer; final_dt/=2
                if final_error<=A['convergence_tolerance_c']: break
            result=spatial
            result.update(variant=name,support_stations_mm=[s*1000 for s in stations],zone_ranges_mm=zones)
            cases.append(result)
            convergence.append({'variant':name,'contact':contact,'air':air,'support':support,
                'temporal_error_c':max(time_error,final_error),'spatial_error_c':space_error,
                'temporal_levels':levels,'spatial_levels':space_levels,'final_mesh_time_levels':final_time_levels})
    differences=[]
    for key in itertools.product(A['contact_h_w_m2_k'],A['air_h_w_m2_k'],A['support_conductance_w_k']):
        group={r['variant']:r for r in cases if (r['contact_h_w_m2_k'],r['air_h_w_m2_k'],r['support_conductance_w_k'])==key}
        ref=group['reference']
        differences.append({'conditions':key,'delta_vs_reference':{name:{
            'z1_heater_peak_c':r['heater_peaks_c'][0]-ref['heater_peaks_c'][0],
            'barrel_peak_c':r['barrel_peak_c']-ref['barrel_peak_c'],
            'growth_mm':r['peak_free_growth_mm']-ref['peak_free_growth_mm']}
            for name,r in group.items() if name!='reference'}})
    properties=[]
    for k,cp in A['property_sensitivity_pairs']:
        stations,zones=configs['combined']
        r=thermal_screen(base,stations,zones,200,8,0.05,
                         overrides={'steel_k_w_m_k':k,'steel_cp_j_kg_k':cp})
        properties.append({'k_w_mk':k,'cp_j_kgk':cp,'barrel_peak_c':r['barrel_peak_c'],
                           'heater_peaks_c':r['heater_peaks_c'],'max_step_energy_residual_j':r['max_step_energy_residual_j']})
    checks={
        'four_geometric_factors':len(configs)==4 and len(cases)==32,
        'beam_analytic_reactions':max(r['reaction_error_n'] for rows in beams.values() for r in rows)<1e-4,
        'beam_force_balance':max(abs(r['force_residual_n']) for rows in beams.values() for r in rows)<1e-4,
        'beam_moment_balance':max(abs(r['moment_residual_nm']) for rows in beams.values() for r in rows)<1e-5,
        'beam_mesh_converged':max(abs(rows[-1]['max_deflection_mm']/rows[-2]['max_deflection_mm']-1) for rows in beams.values())<0.01,
        'thermal_step_balance':max(r['max_step_energy_residual_j'] for r in cases+properties)<1e-6,
        'thermal_global_balance':max(abs(r['global_energy_residual_j']) for r in cases)<1e-4,
        'temporal_refinement':max(r['temporal_error_c'] for r in convergence)<=A['convergence_tolerance_c'],
        'spatial_refinement':max(r['spatial_error_c'] for r in convergence)<=A['convergence_tolerance_c'],
        'sources_unchanged':all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())}
    checks = {name: bool(value) for name,value in checks.items()}
    latest=[r for r in cases if r['variant']=='combined']
    result={'schema_version':2,'status':'DIGITAL_DELTA_SCREEN_COMPLETE' if all(checks.values()) else 'NUMERICAL_VERIFICATION_FAILED',
        'checks':checks,'reference_commit':archive['reference_commit'],'source_sha256':hashes,
        'assumptions':A,'configurations':{n:{'support_stations_mm':[s*1000 for s in st],
                         'zone_ranges_mm':z} for n,(st,z) in configs.items()},
        'beam':beams,'thermal_cases':cases,'refinement':convergence,
        'factor_differences':differences,'material_sensitivity':properties,
        'z1_contact_area_cm2':latest[0]['contact_areas_m2'][0]*1e4,
        'z1_power_density_w_cm2':base['heater_zone_power_w'][0]/(latest[0]['contact_areas_m2'][0]*1e4),
        'thermal_comparison':{'ceiling_c':A['comparison_ceiling_c'],
            'barrel_exceeds':any(r['barrel_peak_c']>A['comparison_ceiling_c'] for r in latest),
            'heater_exceeds':any(max(r['heater_peaks_c'])>A['comparison_ceiling_c'] for r in latest),
            'all_sensors_reach_target_band':all(r['time_to_target_band_s'] is not None for r in latest)},
        'scope':'1D axial FV / lumped heaters-die; ideal annular beam. Model verification, not process or hardware qualification.',
        'physical_validation_state':'NOT_RUN','machine_release':'HOLD',
        'fabrication_authorized':False,'energization_authorized':False,
        'limitations':['Uncalibrated heat transfer / material sensitivity; not certified bounds.',
          'Heater relay is not released PID; no safety trips or thermal cutoff simulation.',
          'No radial gradients, screw/polymer flow, feed housing, 3D notches or local contact.',
          'External radiation is to ambient, not a modeled shield enclosure. No PI tape credit.',
          'Negative rear beam reaction requires radial capture; ideal supports do not prove contact capacity.',
          'No whole-machine modal, joint slip, fatigue or interlock actuation qualification.',
          '300C comparison ceiling is not an approved heater-sheath rating.']}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['status'],json.dumps(checks),flush=True)
    print('THERMAL_COMPARISON',json.dumps(result['thermal_comparison']),flush=True)
    if not all(checks.values()): raise SystemExit(2)
    return result
