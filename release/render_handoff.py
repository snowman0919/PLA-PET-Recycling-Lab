#!/usr/bin/env python3
"""Render real native CAD solids without invented parts or substituted screw geometry."""
from pathlib import Path
import hashlib,json
import FreeCAD as App
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'exports/final/drive_ggm_v08/GGM-FULL-ASM.FCStd'
OUT=ROOT/'exports/final/handoff'
def main():
 OUT.mkdir(parents=True,exist_ok=True);doc=App.openDocument(str(SOURCE))
 objects=[o for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
 faces=[];xs=[];ys=[]
 for obj in objects:
  points,triangles=obj.Shape.tessellate(1.0);name=obj.Name
  base=(144,164,173) if 'Frame' in name or 'Rail' in name else (100,138,160)
  if any(x in name for x in ('Hopper','Bin','Shield','Guard')):base=(175,188,193)
  if any(x in name for x in ('Heater','Barrel','Die')):base=(172,131,90)
  if 'Spool' in name:base=(120,137,121)
  for tri in triangles:
   vs=[points[i] for i in tri];poly=[((v.x-v.y)*.70710678,(v.x+v.y)*.40824829-v.z*.81649658) for v in vs]
   for x,y in poly:xs.append(x);ys.append(y)
   normal=(vs[1]-vs[0]).cross(vs[2]-vs[0]);shade=.60+.38*abs(normal.z/normal.Length) if normal.Length else .8
   faces.append((sum(v.x+v.y+v.z for v in vs)/3,poly,tuple(int(c*shade) for c in base)))
 w,h=1800,1500;xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys)
 scale=min((w-200)/(xmax-xmin),(h-200)/(ymax-ymin));ox=(w-(xmax-xmin)*scale)/2
 image=Image.new('RGB',(w,h),'white');draw=ImageDraw.Draw(image)
 for _,poly,color in sorted(faces,key=lambda x:x[0]):
  draw.polygon([(ox+(x-xmin)*scale,100+(y-ymin)*scale) for x,y in poly],fill=color)
 draw.text((40,30),'PPR / GGM-FULL-ASM / actual native CAD solids / physical validation NOT_RUN',fill='black')
 target=OUT/'GGM_complete_assembly.png';image.save(target);App.closeDocument(doc.Name)
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'status':'HANDOFF_RENDER_PASS','native_objects':len(objects),'triangles':len(faces),
  'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__).resolve(),SOURCE)},
  'file':target.name,'sha256':digest(target),'physical_validation_state':'NOT_RUN'}
 (OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print('HANDOFF_RENDER_PASS',len(objects),len(faces),flush=True)
if __name__=='__main__':main()
