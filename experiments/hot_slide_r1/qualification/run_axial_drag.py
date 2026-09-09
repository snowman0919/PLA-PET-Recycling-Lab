"""Actual CalculiX runs for the previously omitted axial shoe drag response.
Frozen selected mesh/supports. A 25 N per-sheet load is a response basis, not
measured friction or a machine rating. No physical equipment is controlled.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,os,re,shutil,sys,tempfile,math
HERE=Path(__file__).resolve().parent; EXP=HERE.parent
sys.path.insert(0,str(EXP))
from solver_kernel import solve

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=EXP/'solver_result.json'; data=json.loads(source.read_text())
    for name,h in data['source_sha256'].items():
        if sha(EXP/name)!=h: raise ValueError('Stale source: '+name)
    raw=HERE/'raw'; raw.mkdir(exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='axial-drag-',dir=raw)); rows=[]
    for size in (.55,.45):
        original=next(r for r in data['runs'] if r['mesh_mm']==size and r['mode']=='RADIAL')
        inp=EXP/original['raw_directory']/'model.inp'
        if sha(inp)!=original['input_sha256']: raise ValueError('Stale input deck')
        text=inp.read_text(); start=text.rindex('*CLOAD\n'); end=text.index('*NODE PRINT',start)
        forces=defaultdict(lambda:[0.,0.,0.])
        for line in text[start+7:end].splitlines():
            if not line.strip(): continue
            node,dof,value=line.split(','); forces[int(node)][int(dof)-1]+=float(value)
        weights={n:math.hypot(f[0],f[1]) for n,f in forces.items()}; total=sum(weights.values())
        if not math.isclose(total,75.,rel_tol=.001): raise ValueError('Radial patch load mismatch')
        loads={n:25.*w/total for n,w in weights.items()}
        case=out/('mesh_'+str(size)); case.mkdir()
        deck=text[:start]+'*CLOAD\n'+'\n'.join(f'{n},3,{f:.12g}' for n,f in loads.items())+'\n'+text[end:]
        result=solve(case,deck)
        refs=[int(x) for x in text.split('*NSET,NSET=REACTION\n')[1].split('\n')[0].split(',')]
        reactions={}; mode=False; disp={}
        for line in (case/'model.dat').read_text().splitlines():
            v=line.split()
            if len(v)==4 and v[0].isdigit() and int(v[0]) in refs:
                reactions[int(v[0])]=list(map(float,v[1:]))
        if set(reactions)!=set(refs): raise ValueError('Missing support reactions')
        # In pin_supports, reference DOF2 is the physical sheet-normal Z force.
        residual=25.+sum(v[1] for v in reactions.values())
        if abs(residual)>.001: raise ValueError('Axial force imbalance')
        for line in (case/'model.frd').read_text().splitlines():
            if line.startswith(' -4'): mode='DISP' in line
            elif line.startswith(' -3'): mode=False
            elif mode and line.startswith(' -1'):
                v=re.findall(r'[-+]?\d*\.?\d+(?:E[-+]?\d+)?',line)
                disp[int(v[1])]=list(map(float,v[2:5]))
        if not set(loads)<=set(disp): raise ValueError('Missing shoe displacement')
        average=sum(weights[n]*disp[n][2] for n in loads)/total*1000
        row={'mesh_mm':size,'applied_axial_force_n':25.,'axial_reaction_residual_n':residual,
             'mean_shoe_axial_displacement_mm':average,'result':result,
             'original_input_sha256':sha(inp),'raw_directory':str(case.relative_to(HERE)),
             'files_sha256':{p.name:sha(p) for p in case.iterdir() if p.suffix in {'.inp','.frd','.dat','.log'}}}
        rows.append(row); print('AXIAL_DRAG_SOLVED',size,average,result['max_von_mises_mpa'],flush=True)
    a,b=rows
    changes={'stress':abs(a['result']['max_von_mises_mpa']-b['result']['max_von_mises_mpa'])/b['result']['max_von_mises_mpa'],
             'axial_displacement':abs(a['mean_shoe_axial_displacement_mm']-b['mean_shoe_axial_displacement_mm'])/abs(b['mean_shoe_axial_displacement_mm'])}
    env=json.loads((EXP/'sliding_envelope.json').read_text()); derived=json.loads((EXP/'derived_requirements.json').read_text())
    drag_per_sheet=env['maximum_total_normal_force_per_carrier_n']*.25/6
    stress_bound=max(r['result']['max_von_mises_mpa'] for r in rows)*drag_per_sheet/25
    displacement=max(abs(r['mean_shoe_axial_displacement_mm']) for r in rows)*drag_per_sheet/25
    result={'status':'CONDITIONAL_FRICTION_RESPONSE_NOT_QUALIFIED','physical_validation':'NOT_RUN',
        'runs':rows,'medium_to_fine_relative_change':changes,'assumed_mu':.25,
        'friction_stress_triangle_bound_mpa':stress_bound,'axial_displacement_at_assumed_mu_mm':displacement,
        'previous_strength_requirement_mpa':derived['conservative_combined_screen_requirement_mpa'],
        'strength_requirement_including_assumed_drag_mpa':derived['conservative_combined_screen_requirement_mpa']+2*stress_bound,
        'limitations':['Axial traction is a linear sensitivity on existing shoe patches, not a solved frictional contact.',
            'Uniform share over six sheets assumed; stack contact, separation and preload redistribution not solved.',
            'Peak nodal stress may remain local-mesh sensitive; thermal/drag peaks are combined only as a triangle bound.',
            'If deflection consumes inter-sheet clearance, this model is outside its stack-free assumption.'],
        'source_sha256':{str(p.relative_to(EXP)):sha(p) for p in [Path(__file__),source,EXP/'solver_kernel.py',EXP/'pin_supports.py',EXP/'sliding_envelope.json',EXP/'derived_requirements.json']},
        'solver_binary_sha256':sha(Path(shutil.which('ccx')))}
    (HERE/'results/axial_drag.json').write_text(json.dumps(result,indent=2)+'\n')
    print('AXIAL_DRAG_SCREEN_COMPLETE',json.dumps(changes),flush=True)
if __name__=='__main__': main()
