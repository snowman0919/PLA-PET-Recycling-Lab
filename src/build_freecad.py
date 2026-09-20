"""Native FreeCAD assembly from the shared master. The helical screw imports the
round-trip-checked planar STEP; the older native fuse backend is not qualified.
Run in FreeCAD's Python console: exec(open('/absolute/src/build_freecad.py').read())
Or use a .FCMacro setting PPR_ROOT and call run(root). Physical release remains HOLD.
"""
import json,math,time,os
from pathlib import Path
import FreeCAD as App
import Part
V=App.Vector

def wire(points):
 p=[V(*x) for x in points]
 if (p[0]-p[-1]).Length>1e-8:p.append(p[0])
 return Part.makePolygon(p)

def primitive(s):
 k=s['kind'];p=V(*s.get('at',[0,0,0]));axis=V(*s.get('axis',[0,1,0]))
 if k=='box':return Part.makeBox(*s['size'],p)
 if k=='cylinder':return Part.makeCylinder(s['r'],s['h'],p,axis)
 if k=='cone':
  if abs(s['r1']-s['r2'])<1e-8:return Part.makeCylinder(s['r1'],s['h'],p,axis)
  return Part.makeCone(s['r1'],s['r2'],s['h'],p,axis)
 if k=='polygon':
  pts=[]
  for a,b in s['points']:
   v=[a+p.x,p.y,b+p.z] if s.get('plane','XZ')=='XZ' else [a+p.x,b+p.y,p.z]
   if not pts or sum((v[i]-pts[-1][i])**2 for i in range(3))>1e-16:pts.append(v)
  if sum((pts[0][i]-pts[-1][i])**2 for i in range(3))<1e-16:pts.pop()
  direction=V(0,s['h'],0) if s.get('plane','XZ')=='XZ' else V(0,0,s['h'])
  return Part.Face(wire(pts)).extrude(direction)
 if k=='loft':return Part.makeLoft([wire(loop) for loop in s['loops']],True,True)
 if k=='screw_flight':
  r=(s['root_r']+s['outer_r'])/2;t=s['thickness']
  h=Part.Wire(Part.makeHelix(s['pitch'],s['height']-t,r).Edges)
  section=wire([[s['root_r'],0,0],[s['outer_r'],0,0],[s['outer_r'],0,t],[s['root_r'],0,t]])
  return h.makePipeShell([section],True,True)
 raise ValueError(k)

def build(p):
 if p['id']=='EX-SCREW':
  s=primitive(p['adds'][0])
  for a in p['adds'][1:3]:s=s.fuse(primitive(a))
  cfg=p['adds'][3];segments=cfg.get('segments_per_turn',64);turns=round(cfg['height']/cfg['pitch']);sections=[]
  for j in range(segments*turns+1):
   a=j*2*math.pi/segments;z=j*cfg['pitch']/segments;rr=cfg['root_r'];ro=cfg['outer_r'];t=cfg['thickness']
   sections.append([[rr*math.cos(a),rr*math.sin(a),z],[ro*math.cos(a),ro*math.sin(a),z],[ro*math.cos(a),ro*math.sin(a),z+t],[rr*math.cos(a),rr*math.sin(a),z+t]])
  def face(vs):return Part.Face(wire(vs))
  faces=[face(list(reversed(sections[0]))),face(sections[-1])]
  for lo,hi in zip(sections,sections[1:]):
   for k in range(4):
    a,b,c,d=lo[k],lo[(k+1)%4],hi[(k+1)%4],hi[k]
    faces.extend([face([a,b,c]),face([a,c,d])])
  flight=Part.makeSolid(Part.makeShell(faces))
  return s.fuse(flight).cut(Part.makeBox(40,40,4,V(-20,-20,cfg['height']))).removeSplitter()
 a=[primitive(x) for x in p['adds']];s=a[0]
 for t in a[1:]:s=s.fuse(t)
 for c in p['cuts']:s=s.cut(primitive(c))
 return s.removeSplitter()

def run(root):
 root=Path(root);m=json.loads((root/'design/assembly.json').read_text());doc=App.newDocument('PPR_C1')
 shapes={};checks=[]
 expected={p['part_id']:p for p in json.loads((root/'results/cad_parts.json').read_text())['parts']}
 parity=[]
 for pid,p in m['parts'].items():
  method='native_CSG'
  if pid=='EX-SCREW':
   s=Part.Shape();s.read(str(root/'cad/parts/EX-SCREW.step'));method='checked_planar_STEP_bridge'
  else:s=build(p)
  rel=abs(s.Volume-expected[pid]['volume_mm3'])/max(1,expected[pid]['volume_mm3'])
  if not s.isValid() or len(s.Solids)!=1 or rel>1e-5:raise RuntimeError('Native geometry parity failed: '+pid+' '+str(rel))
  parity.append({'part':pid,'method':method,'relative_volume_difference':rel})
  shapes[pid]=s
  checks.append({'part':pid,'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume})
  print('PPR_FREECAD',pid,s.isValid(),len(s.Solids),flush=True)
 for n,it in enumerate(m['instances']):
  ob=doc.addObject('Part::Feature',it['name'].replace('-','_'));ob.Label=it['name'];ob.Shape=shapes[it['part']]
  r=it['rotation'];ob.Placement=App.Placement(V(*it['at']),App.Rotation(V(*r[:3]),r[3]))
  ob.addProperty('App::PropertyString','PartID');ob.PartID=it['part']
  ob.addProperty('App::PropertyString','ReleaseStatus');ob.ReleaseStatus=m['parts'][it['part']]['status']
  ob.addProperty('App::PropertyString','SourceURL');ob.SourceURL=m['parts'][it['part']]['source']
 doc.recompute();(root/'cad').mkdir(exist_ok=True)
 doc.saveAs(str(root/'cad/PPR_C1_assembly.FCStd'))
 Part.export(list(doc.Objects),str(root/'cad/PPR_C1_native.step'))
 (root/'results/freecad_build.json').write_text(json.dumps({'FreeCAD_version':App.Version(),'parts':checks,'objects':len(doc.Objects),'physical_release':'HOLD','parity':parity,'screw_backend_note':'64 planar facets per turn; radius chord error at OD16 <=0.00964 mm; RFQ geometry, not cutter toolpath'},indent=2))
 return doc
if __name__=='__main__':
 root=os.environ.get('PPR_ROOT',str(Path(__file__).resolve().parents[1]));run(root)
