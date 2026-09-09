"""Isolated real-CalculiX regression runs; does not promote release status."""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import math
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_calculix_v08 as core
from beam_torque_recovery import expanded_root_torque

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def front_u(path):
    active = False
    for line in Path(path).read_text().splitlines():
        if 'displacements (vx,vy,vz) for set FRONT' in line:
            active = True
            continue
        fields = line.split()
        if active and len(fields)==4 and fields[0].isdigit():
            value = float(fields[1]) * 1000
            if not math.isfinite(value):
                raise ValueError('non-finite front displacement')
            return value
    raise ValueError('FRONT axial U not found')

def thermal_cases(output):
    params = json.loads((ROOT/'cad/parameters/final_v08.json').read_text())
    baseline = json.loads((ROOT/'cad/parameters/baseline.json').read_text())
    travel = params['hot_zone_mount']['cold_axial_travel_mm']
    normal = max(baseline['extruder']['pet_zone_c'])
    design = baseline['extruder']['hot_path_design_c']
    rows=[]
    # Both alpha values are pre-existing UNQUALIFIED screening assumptions.
    # This is a sensitivity study, not a new SCM440 material qualification.
    for alpha,temp,pressure,spring in itertools.product((12e-6,17e-6),(normal,design),(0.,6.),(0.,1e6)):
        case_id=f'a{alpha*1e6:.0f}_T{temp:g}_P{pressure:g}_K{spring:g}'
        folder=output/case_id; folder.mkdir()
        deck=core.hot_mount_deck('C_RADIAL_CONTROLLED_AXIAL_EXPANSION',temp,spring,pressure)
        if deck.count('1.70E-5')!=1:
            raise ValueError('base expansion card changed; review transformation')
        deck=deck.replace('1.70E-5',f'{alpha:.12e}')
        result=core.solve(folder,deck)
        measured=front_u(folder/'model.dat')
        length=0.280; area=0.0265**2; modulus=190e9
        thrust=pressure*math.pi*16.22**2/4
        analytic=(alpha*(temp-25)*length+thrust*length/(modulus*area))/(1+spring*length/(modulus*area))*1000
        error=abs(measured-analytic)/max(abs(analytic),1e-12)
        if error>0.03:
            raise ValueError(f'{case_id}: analytic/solver delta {error}')
        rows.append({'case_id':case_id,'alpha_per_k':alpha,'temperature_c':temp,
                     'pressure_mpa':pressure,'spring_n_m':spring,
                     'analytic_axial_growth_mm':analytic,'solver_front_axial_growth_mm':measured,
                     'relative_error':error,'full_length_travel_arithmetic_mm':travel-measured,
                     'numeric_regression':'PASS','physical_status':'NOT_RUN',
                     'deck_sha256':sha(folder/'model.inp'),'frd_sha256':sha(folder/'model.frd'),
                     'dat_sha256':sha(folder/'model.dat'),'log_sha256':sha(folder/'ccx.log')})
    return {'status':'CONDITIONAL_SCREEN_ONLY','cases':rows,
            'normal_temperature_c':normal,'design_temperature_c':design,
            'cold_axial_travel_requirement_mm':travel,
            'max_numeric_relative_error':max(r['relative_error'] for r in rows),
            'minimum_full_length_travel_arithmetic_mm':min(r['full_length_travel_arithmetic_mm'] for r in rows),
            'limitations':['12e-6/K and 17e-6/K are existing assumptions, not certified bounds.',
                          'Uniform prescribed temperatures are not a solved heater/contact thermal field.',
                          'Full barrel axial growth must not be confused with clearance at an arbitrary local guide.',
                          'A negative arithmetic reserve requires geometric/temperature review, not an automatic global machine-failure claim.',
                          'No physical operation and no material/fastener approval.']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    os.environ['OMP_NUM_THREADS']='1';os.environ.pop('KMP_DUPLICATE_LIB_OK',None)
    core.RAW=output/'shaft';core.RAW.mkdir()
    before=sha(ROOT/'analysis/final_validation/input/geometry_manifest.json')
    shafts=core.run_shaft_cases()
    if sha(ROOT/'analysis/final_validation/input/geometry_manifest.json')!=before:
        raise ValueError('input changed while solving')
    measured=[]
    for case,summary in shafts.items():
        for shaft,data in summary['per_shaft'].items():
            for item in data['meshes']:
                r=item['result'];measured.append({'case_id':case,'shaft':shaft,'mesh':item['mesh'],
                    'torque':r['reaction']['measured_root_torque'],
                    'equilibrium':r['equilibrium'],'displacement_mm':r['max_displacement_mm']})
    stations=json.loads((ROOT/'analysis/final_validation/input/geometry_manifest.json').read_text())['shredder_stations']['153']
    signed=[]
    for value in (-22.,44.,0.):
        deck,prov,_,coords=core.shaft_deck('LC02',24,stations)
        old=f"{prov['load_application_node']},4,22"
        if deck.count(old)!=1: raise ValueError('unexpected torque card')
        deck=deck.replace(old,f"{prov['load_application_node']},4,{value:g}")
        folder=output/f'torque_{value:g}';folder.mkdir()
        core.solve(folder,deck)
        signed.append(expanded_root_torque(folder/'model.frd',value))
    rejected=0
    sample=core.RAW/'LC02_153_fine/model.frd'
    for wrong in (-22.,21.,float('nan')):
        try: expanded_root_torque(sample,wrong)
        except ValueError: rejected+=1
        else: raise AssertionError('incorrect torque accepted')
    thermal=thermal_cases(output)
    result={'status':'SCOPED_NUMERIC_REGRESSIONS_PASS','release_state':'HOLD_UNCHANGED',
            'solver_binary':shutil.which('ccx'),'solver_binary_sha256':sha(shutil.which('ccx')),
            'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),
                ROOT/'analysis/final_validation/beam_torque_recovery.py',
                ROOT/'analysis/final_validation/run_calculix_v08.py',
                ROOT/'analysis/structural/run_load_checks.py',
                ROOT/'analysis/final_validation/input/geometry_manifest.json',
                ROOT/'cad/parameters/baseline.json',ROOT/'cad/parameters/final_v08.json']},
            'shaft_runs':measured,'torque_sign_and_scaling':signed,
            'negative_controls_rejected':rejected,'thermal':thermal,
            'physical_validation_state':'NOT_RUN'}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'shaft_cases':len(measured),'torque_variants':len(signed),
                      'rejected':rejected,'thermal_cases':len(thermal['cases']),
                      'max_thermal_error':thermal['max_numeric_relative_error'],
                      'min_arithmetic_travel_mm':thermal['minimum_full_length_travel_arithmetic_mm'],
                      'result':str(output/'result.json')},indent=2))
if __name__=='__main__': main()
