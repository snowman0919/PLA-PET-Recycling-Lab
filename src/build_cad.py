"""CadQuery/OCP verification backend for the shared constructive-solid master.
The same assembly.json is consumed by build_freecad.py for native FCStd output.
"""
from pathlib import Path
import json,time,math,sys,traceback
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
V=cq.Vector

def wire3(points):return cq.Wire.makePolygon([V(*p) for p in points],close=True)
def primitive(s):
 k=s['kind'];at=s.get('at',[0,0,0]);axis=s.get('axis',[0,1,0])
 if k=='box': return cq.Solid.makeBox(*s['size'],pnt=V(*at))
 if k=='cylinder':return cq.Solid.makeCylinder(s['r'],s['h'],V(*at),V(*axis))
 if k=='cone':
  if abs(s['r1']-s['r2'])<1e-9:return cq.Solid.makeCylinder(s['r1'],s['h'],V(*at),V(*axis))
  return cq.Solid.makeCone(s['r1'],s['r2'],s['h'],V(*at),V(*axis))
 if k=='polygon':
  if s.get('plane','XZ')=='XZ':
   pts=[[p[0]+at[0],at[1],p[1]+at[2]] for p in s['points']];vec=V(0,s['h'],0)
  else:pts=[[p[0]+at[0],p[1]+at[1],at[2]] for p in s['points']];vec=V(0,0,s['h'])
  # Remove consecutive/closing duplicates before making polygon.
  pp=[]
  for p in pts:
   if not pp or sum((p[j]-pp[-1][j])**2 for j in range(3))>1e-16:pp.append(p)
  if sum((pp[0][j]-pp[-1][j])**2 for j in range(3))<1e-16:pp.pop()
  return cq.Solid.extrudeLinear(wire3(pp),[],vec)
 if k=='loft':return cq.Solid.makeLoft([wire3(loop) for loop in s['loops']],ruled=True)
 if k=='screw_flight':
  r=(s['root_r']+s['outer_r'])/2;t=s['thickness']
  path=cq.Wire.makeHelix(s['pitch'],s['height']-t,r)
  profile=wire3([[s['root_r'],0,0],[s['outer_r'],0,0],[s['outer_r'],0,t],[s['root_r'],0,t]])
  return cq.Solid.sweep(profile,[],path,makeSolid=True,isFrenet=True)
 raise ValueError(k)

def build(p):
 if p['id']=='EX-SCREW':
  shape=primitive(p['adds'][0])
  for a in p['adds'][1:3]:shape=shape.fuse(primitive(a))
  cfg=p['adds'][3];segments=cfg.get('segments_per_turn',64);turns=round(cfg['height']/cfg['pitch'])
  sections=[]
  for j in range(segments*turns+1):
   a=j*2*math.pi/segments;z=j*cfg['pitch']/segments;rr=cfg['root_r'];ro=cfg['outer_r'];t=cfg['thickness']
   sections.append([V(rr*math.cos(a),rr*math.sin(a),z),V(ro*math.cos(a),ro*math.sin(a),z),V(ro*math.cos(a),ro*math.sin(a),z+t),V(rr*math.cos(a),rr*math.sin(a),z+t)])
  def face(vs):return cq.Face.makeFromWires(cq.Wire.makePolygon(vs,close=True))
  faces=[face(list(reversed(sections[0]))),face(sections[-1])]
  for lo,hi in zip(sections,sections[1:]):
   for k in range(4):
    a,b,c,d=lo[k],lo[(k+1)%4],hi[(k+1)%4],hi[k]
    faces.extend([face([a,b,c]),face([a,c,d])])
  flight=cq.Solid.makeSolid(cq.Shell.makeShell(faces))
  shape=shape.fuse(flight).cut(cq.Solid.makeBox(40,40,4,V(-20,-20,cfg['height'])))
  return shape.clean()
 a=[primitive(s) for s in p['adds']]
 shape=a[0]
 for b in a[1:]:shape=shape.fuse(b)
 for c in p['cuts']:shape=shape.cut(primitive(c))
 return shape.clean()

def bbox(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]

def main():
 master=json.loads((ROOT/'design/assembly.json').read_text());shapes={};records=[];fail=[]
 out=ROOT/'cad/parts';out.mkdir(exist_ok=True,parents=True)
 for n,(pid,p) in enumerate(master['parts'].items()):
  t=time.time()
  try:
   s=build(p);b=bbox(s);ok=s.isValid() and len(s.Solids())>=1
   shapes[pid]=s
   cq.exporters.export(s,str(out/(pid+'.step')))
   if p['status'].startswith('CUSTOM') or pid in ['S2-GUIDE','S1-CUT-A','S1-CUT-B']:
    cq.exporters.export(s,str(out/(pid+'.stl')),tolerance=.05,angularTolerance=.15)
   records.append({'part_id':pid,'valid':ok,'solids':len(s.Solids()),'volume_mm3':s.Volume(),'bounds':b,'size_mm':[b[i+3]-b[i] for i in range(3)],'seconds':round(time.time()-t,3),'detail':p['status']})
   print(n,pid,ok,'solids',len(s.Solids()),round(time.time()-t,2),flush=True)
  except Exception as exc:
   fail.append({'part':pid,'error':str(exc)});print('FAILED',pid,repr(exc),flush=True)
 (ROOT/'results/cad_parts.json').write_text(json.dumps({'parts':records,'errors':fail},indent=2))
 if fail:raise SystemExit('CAD part construction failed; inspect results/cad_parts.json')
 placed=[];place_records=[]
 for it in master['instances']:
  s=shapes[it['part']];r=it['rotation']
  if r[3]:s=s.rotate((0,0,0),tuple(r[:3]),r[3])
  s=s.translate(tuple(it['at']));placed.append(s)
  place_records.append({'name':it['name'],'part':it['part'],'group':it['group'],'bounds':bbox(s)})
 ass=cq.Compound.makeCompound(placed)
 cq.exporters.export(ass,str(ROOT/'cad/PPR_C1_assembly.step'))
 (ROOT/'results/cad_assembly.json').write_text(json.dumps({'bounds':bbox(ass),'instances':place_records,'part_count':len(placed),'valid':ass.isValid()},indent=2))
 # Deterministic exact Boolean review of nearby, non-reference pairs. An unapproved collision is a HOLD, never suppressed as a pass.
 contacts=[]
 for i,(a,ar) in enumerate(zip(placed,place_records)):
  ba=ar['bounds']
  for j in range(i+1,len(placed)):
   br=place_records[j];bb=br['bounds']
   if any(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])<=.01 for k in range(3)):continue
   pa=master['parts'][ar['part']];pb=master['parts'][br['part']]
   if (('REFERENCE' in pa['status'] and pa['status']!='DATASHEET_INTERFACE_REFERENCE') or ('REFERENCE' in pb['status'] and pb['status']!='DATASHEET_INTERFACE_REFERENCE') or 'BOUNDARY' in pa['status'] or 'BOUNDARY' in pb['status']):
    continue
   # The costly rotor profiles are tested by the independent full-cycle 2D kinematics, with axial projections recorded separately.
   if ar['group']=='S1' and br['group']=='S1' and ('CUT' in ar['part'] or 'CUT' in br['part']):continue
   try:
    vol=a.intersect(placed[j]).Volume()
    if vol>.05:contacts.append({'a':ar['name'],'b':br['name'],'volume_mm3':round(vol,3),'review':'UNRESOLVED_CAD_INTERSECTION'})
   except Exception as e:contacts.append({'a':ar['name'],'b':br['name'],'error':str(e)})
 print('ASSEMBLY',len(placed),'INTERSECTIONS',len(contacts),flush=True)
 (ROOT/'results/cad_intersections.json').write_text(json.dumps({'scope':'Nearby non-reference solids. Standard bearing boundaries/COTS references excluded; functional mating and full motion require separate audit.','status':'HOLD' if contacts else 'NO_STATIC_INTERSECTIONS_IN_TESTED_SCOPE','contacts':contacts},indent=2))
if __name__=='__main__':main()
