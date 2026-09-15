"""Extract machining coordinates from the exported, hash-bound assembly."""
from pathlib import Path
import json, hashlib, math, sys
import FreeCAD as App
import Part
R=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=R/'exports/final/drive_ggm_v08'
source=OUT/'GGM-FULL-ASM.FCStd'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
doc=App.openDocument(str(source))
records={}
for obj in doc.Objects:
    if not hasattr(obj,'Shape') or obj.Shape.isNull(): continue
    s=obj.Shape; b=s.BoundBox; holes=[]
    if not obj.Name.startswith('GGM_') and obj.Name not in {'Screw','ThrustPlate'}: continue
    for f in s.Faces:
        surface=f.Surface
        if type(surface).__name__!='Cylinder': continue
        axis=surface.Axis; center=surface.Center
        u0,u1,v0,v1=f.ParameterRange
        u=(u0+u1)/2; v=(v0+v1)/2
        normal=f.normalAt(u,v)
        q=f.valueAt(u,v); radial=q-center-axis*((q-center).dot(axis))
        inward=normal.dot(radial)<0
        holes.append({'diameter':2*surface.Radius,'center':[center.x,center.y,center.z],
                      'axis':[axis.x,axis.y,axis.z],'inward':inward,
                      'bbox':[f.BoundBox.XMin,f.BoundBox.YMin,f.BoundBox.ZMin,f.BoundBox.XMax,f.BoundBox.YMax,f.BoundBox.ZMax]})
    records[obj.Name]={'label':obj.Label,'bbox':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],
                       'solids':len(s.Solids),'valid':s.isValid(),'cylinders':holes}
App.closeDocument(doc.Name)
(HERE/'features.json').write_text(json.dumps({'source_sha256':{str(source.relative_to(R)):sha(source)},'objects':records},indent=2)+'\n')
print('FEATURE_EXTRACTION',len(records),flush=True)
