"""Finite-element stiffness/strain screening of a radially compliant shoe sheet."""
import sys, os, math, json, re, subprocess, hashlib
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parent
from solver_kernel import nset,solve
from quadratic_mesh import mesh_step,read_gmsh_inp
from pin_supports import supports
# Use the existing statically consistent surface-load distributor.
from distributing_patch_v08 import resultant_loads
OUT=ROOT/'raw_runs/gradients';OUT.mkdir(parents=True,exist_ok=True)
SPEC=json.loads((ROOT/'contract.json').read_text())
def fields(path):
    out={};mode=''
    for line in path.read_text().splitlines():
        if line.startswith(' -4'):
            mode=next((k for k in ['DISP','STRESS','FORC'] if k in line),'');out.setdefault(mode,{})
        elif line.startswith(' -3'):mode=''
        elif mode and line.startswith(' -1'):
            v=re.findall(r'[-+]?\d*\.?\d+(?:E[-+]?\d+)?',line)
            out[mode][int(v[1])]=list(map(float,v[2:]))
    return out

def main():
    rows=[]
    step=ROOT/'prototype_geometry_slotted/HS-R1-sheet.step'
    for size in (.55,.45):
        base=OUT/f'mesh_{size}';base.mkdir(exist_ok=True)
        nodes,elements=read_gmsh_inp(mesh_step(step,base,size))
        coords,relations,pins=supports(nodes)
        refs=[r['ref'] for r in pins]
        faces=Counter();face6={}
        for e in elements:
            ids=list(map(int,e.split(',')))[1:]
            for indices in ((0,1,2,4,5,6),(0,1,3,4,8,7),(0,2,3,6,9,7),(1,2,3,5,9,8)):
                key=tuple(sorted(ids[i] for i in indices[:3]));faces[key]+=1;face6[key]=[ids[i] for i in indices]
        patches=[]
        for deg in (30,150,270):
            theta=math.radians(deg);normal=np.array([math.cos(theta),math.sin(theta),0.])
            weights=defaultdict(float)
            for face,count in faces.items():
                if count!=1:continue
                pts=np.array([nodes[n] for n in face]);mid=pts.mean(axis=0)
                if not all(abs(math.hypot(p[0],p[1])-SPEC['shoe_free_radius_mm'])<.05 for p in pts):continue
                if np.dot(mid[:2],normal[:2])/max(np.linalg.norm(mid[:2]),1e-12)<.97:continue
                six=face6[face]
                for sub in ((0,3,5),(3,1,4),(5,4,2),(3,4,5)):
                    f=[six[i] for i in sub];xyz=np.array([nodes[n] for n in f])
                    area=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2/1e6
                    for n in f:weights[n]+=area/3
            assert len(weights)>5,(deg,len(weights))
            origin=sum(w*np.array(coords[n]) for n,w in weights.items())/sum(weights.values())
            patches.append((normal,dict(weights),origin))
        for mode in ('RADIAL_HEAT','RADIAL_COOL','FACE_GRADIENT'):
            case=base/mode;case.mkdir(exist_ok=True);forces=defaultdict(lambda:np.zeros(3))
            for normal,weights,origin in patches:
                scalar=0.
                loads=resultant_loads(coords,weights,normal*scalar,[0,0,0],origin)
                for n,f in loads.items():forces[n]+=f
            deck=['*HEADING','HS-R1 elastic shoe sheet; SI m N Pa', '*NODE',*[f'{n},{x:.12g},{y:.12g},{z:.12g}' for n,(x,y,z) in coords.items()], '*ELEMENT,TYPE=C3D10,ELSET=ALL',*elements,*nset('REACTION',refs), '*NSET,NSET=ALLN,GENERATE',f'1,{max(nodes)},1', '*SOLID SECTION,ELSET=ALL,MATERIAL=SPRING','*MATERIAL,NAME=SPRING','*ELASTIC','2.0e11,0.30','*EXPANSION','1.71e-5','*INITIAL CONDITIONS,TYPE=TEMPERATURE','ALLN,0.',*relations,'*BOUNDARY',*[f'{n},1,2,0' for n in refs],'*STEP','*STATIC','0.1,1.0,0.000001','*CLOAD']
            temperatures={}
            for n,point in nodes.items():
                f=max(0.,min(1.,(30-math.hypot(point[0],point[1]))/(30-SPEC['shoe_free_radius_mm'])))
                temperatures[n]=280*(f if mode=='RADIAL_HEAT' else 1-f if mode=='RADIAL_COOL' else point[2]/3)
            deck=deck[:-1]+['*TEMPERATURE',*[f'{n},{temp:.12g}' for n,temp in temperatures.items()],'*CLOAD']
            deck += [f'{n},{a+1},{f[a]:.12g}' for n,f in forces.items() for a in range(3)]
            deck += ['*NODE PRINT,NSET=REACTION','RF','*NODE FILE','U,RF','*EL FILE','S','*END STEP','']
            result=solve(case,'\n'.join(deck));data=fields(case/'model.frd')
            readings=[]
            for normal,weights,origin in patches:
                disp=sum(w*np.array(data['DISP'][n]) for n,w in weights.items())/sum(weights.values())*1000
                readings.append(float(np.dot(disp,normal)))
            force_sum=sum(forces.values());reaction=np.zeros(3);reaction_moment=np.zeros(3);aux={}
            for line in (case/'model.dat').read_text().splitlines():
                v=line.split()
                if len(v)==4 and v[0].isdigit() and int(v[0]) in refs:aux[int(v[0])]=np.array(list(map(float,v[1:])))
            if set(aux)!=set(refs):raise ValueError('missing slot reaction')
            for pin in pins:
                v=aux[pin['ref']];t=pin['tangent'];f=np.array([t[0]*v[0],t[1]*v[0],v[1]])
                reaction+=f;reaction_moment+=np.cross(pin['centroid_m'],f)
            applied_moment=sum(np.cross(coords[n],f) for n,f in forces.items())
            moment_residual=float(np.linalg.norm(applied_moment+reaction_moment))
            if moment_residual>.001:raise ValueError('moment imbalance')
            result['reaction']={'force_n':reaction.tolist(),'moment_nm':reaction_moment.tolist(),'moment_residual_nm':moment_residual,'support':'tangent/Z means, radial slip free'}
            residual=float(np.linalg.norm(force_sum+reaction));assert residual<.01,residual
            row={'mesh_mm':size,'mode':mode,'nodes':len(nodes),'elements':len(elements),'shoe_radial_displacements_mm':readings,'force_residual_n':residual,'result':result,'scope':'quadratic elastic sheet, three radial-slot tangent/Z mean constraints; contact/friction and hot material not qualified','input_sha256':hashlib.sha256((case/'model.inp').read_bytes()).hexdigest(),'raw_directory':str(case.relative_to(ROOT))}
            rows.append(row)
            print('FLEXURE_SOLVED',size,mode,readings,result['max_von_mises_mpa'],flush=True)
    (ROOT/'gradient_result.json').write_text(json.dumps({'status':'SCREENING_ONLY','physical_validation':'NOT_RUN','runs':rows,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'contract.json',Path(__file__).resolve(),ROOT/'pin_supports.py',ROOT/'quadratic_mesh.py',ROOT/'solver_kernel.py',ROOT/'distributing_patch_v08.py',ROOT/'sliding_geometry_slotted.py')},'geometry_sha256':hashlib.sha256(step.read_bytes()).hexdigest()},indent=2))
    print('FLEXURE_SOLVES_DONE',len(rows),flush=True)
if __name__=='__main__':main()
