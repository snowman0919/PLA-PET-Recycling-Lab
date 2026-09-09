"""Export each closed guard half separately; avoid machining an assembly as one part."""
from pathlib import Path
import json,hashlib,sys
import FreeCAD as A
import Part
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R))
from cad.freecad.compact.generate import normalize_step
O=R/'exports/final/drive_ggm_v08/manufacturing_r2';source=O.parent/'GGM-FULL-ASM.FCStd'
doc=A.openDocument(str(source));rows=[]
for axis in ('SH','EX'):
    obj=doc.getObject('GGM_'+axis+'_CouplingGuard')
    solids=sorted(obj.Shape.Solids,key=lambda s:s.CenterOfMass.z)
    if len(solids)!=2:raise ValueError('guard must have two closed halves')
    for label,solid in zip(('LOWER','UPPER'),solids):
        d=A.newDocument('HALF');f=d.addObject('PartDesign::Feature','GGM_'+axis+'_Guard_'+label);f.Shape=solid;d.recompute()
        path=O/(f.Name+'.step');Part.export([f],str(path));normalize_step(path);A.closeDocument(d.Name)
        q=Part.read(str(path));assert q.isValid() and len(q.Solids)==1 and abs(q.Volume-solid.Volume)<1e-4
        rows.append({'file':path.name,'assembly_object':obj.Name,'half':label,'solids':1,'volume_mm3':q.Volume,
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
A.closeDocument(doc.Name)
(O/'guard_half_manifest.json').write_text(json.dumps({'files':rows,'physical_validation':'NOT_RUN',
 'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,Path(__file__).resolve())}},indent=2)+'\n')
print('SINGLE_SOLID_GUARD_HALVES',len(rows),flush=True)
