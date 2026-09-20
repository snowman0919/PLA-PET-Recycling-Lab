"""Orthographic mesh render of actual BRep parts, not an image-generated concept."""
from pathlib import Path
import json,math
import numpy as np
import cadquery as cq
import trimesh
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
M=json.loads((ROOT/'design/assembly.json').read_text())

def render():
  camera=np.array([1.,-1.4,.9]);camera/=np.linalg.norm(camera)
  right=np.cross(np.array([0.,0.,1.]),camera);right/=np.linalg.norm(right)
  up=np.cross(camera,right);basis=np.array([right,up,camera])
  mesh={}
  for pid in {i['part'] for i in M['instances']}:
    stl=ROOT/'cad/parts'/f'{pid}.stl'
    if stl.exists():
      mm=trimesh.load(str(stl),force='mesh',process=False);mesh[pid]=(np.asarray(mm.vertices),np.asarray(mm.faces))
    else:
      s=cq.importers.importStep(str(ROOT/'cad/parts'/f'{pid}.step')).val()
      vs,ts=s.tessellate(1.,.6);mesh[pid]=(np.array([v.toTuple() for v in vs]),np.array(ts))
    print(pid,flush=True)
  faces=[];bounds=[]
  for it in M['instances']:
    if it['part'] in ['HOPPER','HOP-LID']:continue
    verts,tris=mesh[it['part']];r=it['rotation'];axis=np.array(r[:3],dtype=float);axis/=np.linalg.norm(axis);angle=math.radians(r[3]);K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    rot=np.eye(3)+math.sin(angle)*K+(1-math.cos(angle))*(K@K)
    world=verts@rot.T+it['at'];pp=world@basis.T;bounds.append(pp)
    material=M['parts'][it['part']]['material']
    color=np.array([165,179,187])
    if it['group']=='frame':color=np.array([177,185,192])
    if it['group']=='electrical':color=np.array([95,111,122])
    if 'PC' in material:color=np.array([79,149,163])
    if it['part'].startswith('EX-H'):color=np.array([188,141,86])
    for tri in tris:
      v=world[tri];normal=np.cross(v[1]-v[0],v[2]-v[0]);ln=np.linalg.norm(normal)
      if ln<1e-10:continue
      normal/=ln
      if np.dot(normal,camera)<-.05:continue
      shade=.62+.38*max(0,np.dot(normal,np.array([-.2,-.6,.775])))
      faces.append((float(pp[tri,2].mean()),pp[tri,:2],tuple((color*shade).astype(int))))
  b=np.concatenate(bounds);lo=b[:,:2].min(0);hi=b[:,:2].max(0);W,H=1800,1100;sc=min((W-160)/(hi[0]-lo[0]),(H-150)/(hi[1]-lo[1]))
  im=Image.new('RGB',(W,H),'white');dr=ImageDraw.Draw(im)
  for depth,p,c in sorted(faces,key=lambda q:q[0]):
    xy=[(80+(v[0]-lo[0])*sc,H-70-(v[1]-lo[1])*sc) for v in p]
    dr.polygon(xy,fill=c)
  font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
  dr.text((50,22),'PPR C1 | BRep mesh inspection view | Hopper/lid hidden for visibility',font=font,fill=(35,48,55))
  im.save(ROOT/'docs/CAD_inspection.png')
  print('mesh triangles rendered',len(faces))
if __name__=='__main__':render()
