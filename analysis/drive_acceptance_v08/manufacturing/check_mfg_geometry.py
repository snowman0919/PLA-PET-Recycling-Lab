"""Check actual R2 bearing relief and cover mounting in the exported CAD."""
from pathlib import Path
import json,hashlib
import FreeCAD as A
import Part
H=Path(__file__).resolve().parent;R=H.parents[2];O=R/'exports/final/drive_ggm_v08'
source=O/'GGM-FULL-ASM.FCStd';doc=A.openDocument(str(source));checks=[]
def add(name,value,limit=1e-6):
    checks.append({'check':name,'value':value,'limit':limit,'pass':value<=limit})
cap=doc.getObject('GGM_EX_RadialCap').Shape
add('cap central bore clear',cap.common(Part.makeCylinder(13.699,2,A.Vector(320,411,382),A.Vector(0,1,0))).Volume)
plate=doc.getObject('ThrustPlate').Shape
add('plate rear relief clear',plate.common(Part.makeCylinder(13.699,.299,A.Vector(320,400.701,382),A.Vector(0,1,0))).Volume)
for label,xc,zc,y0,length in [('SH',153,676.167,186,57),('EX',320,382,413,58)]:
    shape=doc.getObject('GGM_'+label+'_CouplingGuard').Shape
    add(label+' two independently removable halves',abs(len(shape.Solids)-2),0)
    add(label+' open split seam',shape.common(Part.makeBox(90,length+4,.998,A.Vector(xc-45,y0-1,zc-.499))).Volume)
    for dx in (-29,29) if label=='SH' else (-18,18):
        for dz in (-18,18) if label=='SH' else (-29,29):
            shapes=[doc.getObject('GGM_'+label+'_Mount').Shape,shape]
            for k,s in enumerate(shapes):
                d=2.5 if k==0 else 3.4
                holes=[f for f in s.Faces if type(f.Surface).__name__=='Cylinder' and abs(f.Surface.Radius*2-d)<1e-5
                    and abs(f.Surface.Center.x-xc-dx)<1e-5 and abs(f.Surface.Center.z-zc-dz)<1e-5]
                add(label+' mounting '+str((dx,dz,k)),0 if holes else 1,0)
A.closeDocument(doc.Name)
result={'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':checks,'physical_validation':'NOT_RUN',
  'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,Path(__file__).resolve())}}
(H/'geometry_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('R2_GEOMETRY',result['status'],len(checks),flush=True)
if result['status']!='PASS':raise ValueError('R2 geometry mismatch')
