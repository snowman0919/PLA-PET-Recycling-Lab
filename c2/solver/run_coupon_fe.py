"""Run small uncalibrated CalculiX coupon sensitivities; never performance labels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CASES={
    'PLA':dict(model='ELASTIC',parameters=[3000.0,.36],displacement_mm=.2),
    'PET':dict(model='ELASTIC',parameters=[2500.0,.38],displacement_mm=.2),
    'TPU':dict(model='NEO_HOOKE',parameters=[3.333,.006],displacement_mm=2.0),
}


def deck(material: str, elements: int) -> str:
    case=CASES[material];length,width,height=20.0,5.0,1.0
    nodes=[]
    for i in range(elements+1):
        x=length*i/elements
        for y,z in [(0,0),(width,0),(width,height),(0,height)]:
            nodes.append((len(nodes)+1,x,y,z))
    conn=[]
    for i in range(elements):
        a=4*i+1;b=a+4
        conn.append((i+1,a,b,b+1,a+1,a+3,b+3,b+2,a+2))
    left=','.join(str(i) for i in range(1,5))
    right=','.join(str(i) for i in range(4*elements+1,4*elements+5))
    material_card=(f"*ELASTIC\n{case['parameters'][0]},{case['parameters'][1]}" if case['model']=='ELASTIC'
                   else f"*HYPERELASTIC,NEO HOOKE\n{case['parameters'][0]},{case['parameters'][1]}")
    return '\n'.join([
        '*HEADING',f'{material} uncalibrated coupon sensitivity',
        '*NODE',*[','.join(map(str,row)) for row in nodes],
        '*ELEMENT,TYPE=C3D8,ELSET=ALL',*[','.join(map(str,row)) for row in conn],
        '*NSET,NSET=LEFT',left,'*NSET,NSET=RIGHT',right,
        f'*MATERIAL,NAME={material}',material_card,
        f'*SOLID SECTION,ELSET=ALL,MATERIAL={material}',
        '*STEP,NLGEOM=YES,INC=200','*STATIC','.05,1.,1e-8,.1',
        '*BOUNDARY','LEFT,1,3,0',f"RIGHT,1,1,{case['displacement_mm']}",
        '*NODE PRINT,NSET=RIGHT','RF,U','*EL PRINT,ELSET=ALL','S,E','*END STEP',''])


def reaction_force(dat: Path) -> float:
    lines=dat.read_text(errors='replace').splitlines();start=None
    for i,line in enumerate(lines):
        if 'forces (fx,fy,fz)' in line.lower() and 'right' in line.lower():start=i
    if start is None:raise RuntimeError(f'No RIGHT reaction block in {dat}')
    values=[]
    for line in lines[start+1:]:
        m=re.match(r'^\s*\d+\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)',line)
        if m:values.append(float(m.group(1)))
        elif values and not line.strip():break
    if not values:raise RuntimeError(f'No reaction rows in {dat}')
    return abs(sum(values))


def main():
    p=argparse.ArgumentParser();p.add_argument('--ccx',default=shutil.which('ccx'))
    p.add_argument('--out',type=Path,default=ROOT/'experiments/raw/coupon_fe')
    args=p.parse_args()
    if not args.ccx:raise SystemExit('CalculiX ccx not found')
    args.out.mkdir(parents=True,exist_ok=True);runs=[]
    version=subprocess.run([args.ccx,'-v'],text=True,capture_output=True).stdout.strip()
    for material in CASES:
        for elements in (4,8,16):
            name=f'{material.lower()}_{elements}';inp=args.out/(name+'.inp')
            inp.write_text(deck(material,elements))
            result=subprocess.run([args.ccx,'-i',name],cwd=args.out,text=True,capture_output=True)
            log=args.out/(name+'.log');log.write_text(result.stdout+result.stderr)
            if result.returncode or not (args.out/(name+'.frd')).is_file():
                raise RuntimeError(f'{name} failed rc={result.returncode}; see {log}')
            dat=args.out/(name+'.dat');force=reaction_force(dat)
            runs.append(dict(material=material,elements=elements,return_code=result.returncode,
                             reaction_force_N=force,input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),
                             dat_sha256=hashlib.sha256(dat.read_bytes()).hexdigest(),
                             frd_sha256=hashlib.sha256((args.out/(name+'.frd')).read_bytes()).hexdigest()))
            for suffix in ('.12d','.cvg','.sta'):
                (args.out/(name+suffix)).unlink(missing_ok=True)
    (args.out/'spooles.out').unlink(missing_ok=True)
    convergence={}
    for material in CASES:
        values=[r['reaction_force_N'] for r in runs if r['material']==material]
        convergence[material]=abs(values[-1]-values[-2])/max(values[-1],1e-12)
    summary=dict(status='UNCALIBRATED_COUPON_SOLVER_RUN_NOT_SHREDDING_PERFORMANCE',solver='CalculiX',
                 solver_version=version,cases=CASES,geometry_mm={'length':20,'width':5,'height':1},
                 runs=runs,relative_force_change_8_to_16=convergence,
                 assumptions='ASSUMED_MATERIAL_PARAMETERS_NOT_GRADE_LOT_TEMPERATURE_OR_RATE_CALIBRATED',
                 exclusions=['fracture','tear','viscoelasticity','anisotropy','printed_layer_direction',
                             'S2_contact','particle_size','throughput','torque_history','jam'],
                 qualification='DID_RUN_SOLVER; DID_NOT_RUN_DEM_OR_PHYSICAL_TEST; NOT_A_PERFORMANCE_LABEL')
    (ROOT/'results/coupon_fe_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
