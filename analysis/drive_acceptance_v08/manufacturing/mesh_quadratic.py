"""Quadratic tetrahedral refinement for the scoped thrust-plate comparison."""
from pathlib import Path
import subprocess,os

def mesh_step(step,folder,size):
    target=folder/'gmsh.inp'
    r=subprocess.run(['gmsh',str(step),'-3','-order','2','-setnumber','Mesh.SecondOrderLinear','1','-format','inp','-setnumber','Mesh.CharacteristicLengthMin',str(size*.65),
      '-setnumber','Mesh.CharacteristicLengthMax',str(size),'-o',str(target)],capture_output=True,text=True,timeout=180)
    (folder/'gmsh.log').write_text(r.stdout+r.stderr)
    if r.returncode or not target.exists():raise RuntimeError('quadratic meshing failed')
    return target

def read_gmsh_inp(path):
    nodes={};elements=[];mode=''
    for raw in path.read_text().splitlines():
        s=raw.strip()
        if s.startswith('*'):
            mode='N' if s.upper()=='*NODE' else 'E' if 'TYPE=C3D10' in s.upper() else '';continue
        if not mode or not s:continue
        v=s.split(',')
        if mode=='N':nodes[int(v[0])]=tuple(map(float,v[1:4]))
        elif len(v)==11:elements.append(s)
        else:raise ValueError('wrong quadratic connectivity')
    if not elements:raise ValueError('quadratic elements absent')
    return nodes,elements
