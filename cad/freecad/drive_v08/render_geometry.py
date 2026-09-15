"""Render actual BRep triangles for the review, not an imagined assembly."""
from pathlib import Path
import json,math
import FreeCAD as App
import Part
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'analysis/drive_integration_v08/raw';OUT=ROOT/'exports/final/drive_ggm_v08'
items=json.loads((RAW/'render_items.json').read_text())

def render(name,select):
    faces=[]; xs=[];ys=[]
    for row in items:
        if not select(row):continue
        s=Part.Shape();s.read(str(RAW/(row['name']+'.brep')))
        print('RENDER_PART',name,row['name'],len(s.Faces),flush=True)
        if row['name']=='Screw':
            b=s.BoundBox; s=Part.makeCylinder(8,b.YLength,App.Vector(320,b.YMin,382),App.Vector(0,1,0))
        points,triangles=s.tessellate(2.0)
        base=(130,149,156) if row['group']=='frame' else (88,132,151)
        if row['name'].startswith('GGM'):base=(183,111,64) if 'Fuse' in row['name'] else (108,128,149)
        for tri in triangles:
            vs=[points[i] for i in tri]
            p=[((v.x-v.y)*.707,-(v.x+v.y)*.35-v.z*.92) for v in vs]
            for x,y in p:xs.append(x);ys.append(y)
            normal=(vs[1]-vs[0]).cross(vs[2]-vs[0]);length=normal.Length
            shade=.68+.3*abs(normal.z/length) if length else .8
            faces.append((sum(-v.x-v.y+v.z*.6 for v in vs)/3,p,tuple(int(c*shade) for c in base)))
    width,height=1200,1000;scale=min((width-100)/(max(xs)-min(xs)),(height-100)/(max(ys)-min(ys)))
    lowx,lowy=min(xs),min(ys)
    image=Image.new('RGB',(width,height),'white');draw=ImageDraw.Draw(image)
    for _,poly,color in sorted(faces):
        draw.polygon([(50+(x-lowx)*scale,50+(y-lowy)*scale) for x,y in poly],fill=color)
    draw.text((25,20),name+' - CAD drive review; screw helix omitted; guards removed; no hardware test',fill='black')
    image.save(OUT/(name+'.png'))
render('GGM_full_layout',lambda r:(r['group']=='frame' or r['name'].startswith('GGM_') or r['name'] in {'Barrel','ThrustPlate','Screw'}) and 'Guard' not in r['name'])
render('GGM_drive_details',lambda r:r['name'].startswith('GGM_') and r['group']!='frame')
render('GGM_shredder_detail',lambda r:r['name'].startswith(('GGM_SH','GGM_Shredder','GGM_Jack')) and 'Guard' not in r['name'])
render('GGM_extruder_detail',lambda r:r['name'].startswith(('GGM_EX','GGM_Extruder')) and 'Guard' not in r['name'] or r['name'] in {'Screw','ThrustPlate','ThrustBearing51102'})
print('CAD_RENDER_DONE',flush=True)
