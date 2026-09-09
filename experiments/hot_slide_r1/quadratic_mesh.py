"""Quadratic tetrahedral mesh adapter for the isolated flexure prototype."""
from pathlib import Path
import shutil, subprocess

def mesh_step(step, case_dir, size):
    out=case_dir/'gmsh.inp'
    command=[shutil.which('gmsh'),str(step),'-3','-order','2','-format','inp','-setnumber','Mesh.CharacteristicLengthMin',str(size*.55),'-setnumber','Mesh.CharacteristicLengthMax',str(size),'-o',str(out)]
    run=subprocess.run(command,capture_output=True,text=True,timeout=240)
    (case_dir/'gmsh.log').write_text(run.stdout+run.stderr)
    if run.returncode or not out.exists():raise RuntimeError('quadratic meshing failed')
    return out

def read_gmsh_inp(path):
    nodes={};elements=[];mode=''
    for raw in path.read_text().splitlines():
        line=raw.strip()
        if line.startswith('*'):
            u=line.upper();mode='NODE' if u=='*NODE' else 'ELEMENT' if 'TYPE=C3D10' in u else '';continue
        if not line or not mode:continue
        v=[s.strip() for s in line.split(',')]
        if mode=='NODE':nodes[int(v[0])]=tuple(map(float,v[1:4]))
        else:
            if len(v)!=11:raise ValueError('unexpected C3D10 connectivity')
            elements.append(','.join(v))
    if not nodes or not elements:raise ValueError('missing quadratic volume mesh')
    return nodes,elements
