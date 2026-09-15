"""Contact-compatible linear screen using actual FE shoe compliance matrix.
No inferred material certificate or physical PASS. Units mm, N, MPa.
"""
import json, math, itertools
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
N=np.array([[math.cos(math.radians(a)),math.sin(math.radians(a))] for a in (30,150,270)])
F=np.column_stack((np.ones(3)*25,(2/3)*10*N[:,0],(2/3)*10*N[:,1]))

def solve_contact(C,g,load):
    K=np.linalg.inv(C)
    centre=np.linalg.solve(N.T@K@N,np.asarray(load)-N.T@K@g)
    force=K@(g+N@centre)
    if not np.isfinite(force).all():raise ValueError('nonfinite contact result')
    return centre,force

def main():
    spec=json.loads((ROOT/'contract.json').read_text())
    data=json.loads((ROOT/'solver_result.json').read_text())
    fine=min(spec['mesh_levels_mm']);medium=sorted(spec['mesh_levels_mm'])[1]
    cases={r['mode']:r for r in data['runs'] if r['mesh_mm']==fine}
    modes=('RADIAL','X','Y')
    U=np.column_stack([cases[m]['shoe_radial_displacements_mm'] for m in modes])
    C=U@np.linalg.inv(F)
    symmetry=np.linalg.norm(C-C.T)/np.linalg.norm(C)
    if symmetry>.01 or min(np.linalg.eigvalsh((C+C.T)/2))<=0:raise ValueError('invalid compliance')
    peaks=np.array([cases[m]['result']['max_von_mises_mpa'] for m in modes])
    records=[];worst_stress=0;worst_force=0;worst_centre=0;min_contact=1e9
    for tb,ts,ab,aspring,E,rb,errors,axis,sign in itertools.product((20,270,300),(20,100,200,300),(12.3e-6,17e-6),(11.5e-6,17.1e-6),(160e3,200e3),(16.985,17.),itertools.product((-.01,.01),repeat=3),(0,1),(-1,1)):
        g=rb*(1+ab*(tb-20))-(spec['shoe_free_radius_mm']+np.array(errors))*(1+aspring*(ts-20))
        load=np.zeros(2);load[axis]=25*sign
        centre,force=solve_contact(C/(6*E/200e3),g,load)
        coeff=np.linalg.solve(F,force/6)
        stress_bound=float(np.abs(coeff)@peaks)
        normal_sum=float(np.sum(force));offset=float(np.linalg.norm(centre))
        min_contact=min(min_contact,float(min(force)))
        worst_force=max(worst_force,normal_sum);worst_stress=max(worst_stress,stress_bound);worst_centre=max(worst_centre,offset)
        records.append({'barrel_c':tb,'spring_c':ts,'barrel_cte':ab,'spring_cte':aspring,'E_mpa':E,'barrel_radius_mm':rb,'shoe_radius_errors_mm':list(errors),'radial_load_n':load.tolist(),'centre_offset_mm':offset,'shoe_forces_n':force.tolist(),'total_normal_force_n':normal_sum,'stress_upper_bound_mpa':stress_bound})
    metrics={}
    for mode in modes:
        a=next(r for r in data['runs'] if r['mesh_mm']==medium and r['mode']==mode)
        b=cases[mode]
        metrics[mode]={'displacement_change':float(np.linalg.norm(np.array(a['shoe_radial_displacements_mm'])-b['shoe_radial_displacements_mm'])/np.linalg.norm(b['shoe_radial_displacements_mm'])),'peak_stress_change':abs(a['result']['max_von_mises_mpa']-b['result']['max_von_mises_mpa'])/b['result']['max_von_mises_mpa']}
    extreme={key:max(records,key=lambda r:r[key]) for key in ('centre_offset_mm','total_normal_force_n','stress_upper_bound_mpa')}
    result={'status':'CONDITIONAL_ENGINEERING_SCREEN','physical_validation_state':'NOT_RUN','compliance_matrix_mm_per_n':C.tolist(),'symmetry_error':symmetry,'sheet_count':6,'case_count':len(records),'minimum_shoe_normal_force_n':min_contact,'maximum_compliance_centre_offset_mm':worst_centre,'mounting_clearance_and_alignment_budget_mm':.04,'conservative_total_centre_budget_mm':worst_centre+.04,'maximum_total_normal_force_per_carrier_n':worst_force,'friction_force_per_carrier_at_mu025_n':.25*worst_force,'maximum_stress_triangle_bound_mpa':worst_stress,'required_service_yield_mpa_for_sf2':2*worst_stress,'convergence':metrics,'extremes':extreme,'limitations':['Uniform temperature per component; gradients and friction hysteresis not solved.','Positive force in linear mean-contact model is not actual line-contact proof.','Spring-temperature E and CTE bounds are assumptions; hot yield and fatigue require supplier/test data.','Radial25N per carrier is a proposed bench envelope, not certified machine load.','Fixture slot clearance, mounting alignment and unequal sheet preload require measured acceptance.']}
    (ROOT/'sliding_envelope.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('extremes','compliance_matrix_mm_per_n','limitations')},indent=2))
if __name__=='__main__':main()
