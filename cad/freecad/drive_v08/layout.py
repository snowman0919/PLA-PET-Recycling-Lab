"""GGM layout on current PPR solids. Local motor z points out of gearhead."""
from pathlib import Path
import json, math, hashlib
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'analysis/drive_integration_v08/raw/source'

def moved(shape, axis=(0,0,1), angle=0, offset=(0,0,0)):
    s=shape.copy(); s.rotate(App.Vector(),App.Vector(*axis),angle); s.translate(App.Vector(*offset)); return s

def ggm_local():
    gear=Part.makeBox(90,90,60,App.Vector(-45,-63,-60))
    motor=Part.makeCylinder(45,149,App.Vector(0,-18,-209))
    pilot=Part.makeCylinder(18,3)
    shaft=Part.makeCylinder(6,32)
    shaft=shaft.cut(Part.makeBox(4,3,25,App.Vector(-2,3.5,3)))
    s=gear.fuse(motor).fuse(pilot).fuse(shaft).removeSplitter()
    d=104/(2*math.sqrt(2))
    for x in (-d,d):
        for y in (-18-d,-18+d):
            s=s.cut(Part.makeCylinder(3.25,60,App.Vector(x,y,-60)))
    return s

def item(name,s,group,material,kind='manufactured_or_stock'):
    if group=='drive': group='extruder' if name.startswith(('GGM_EX','GGM_Extruder','GGM_M5_EX')) else 'shredder'
    return dict(name=name,shape=s,group=group,material=material,classification=kind)

def motor_pose(shape, point, extruder=False):
    s=moved(shape,(0,0,1),90 if extruder else 180)
    return moved(s,(1,0,0),90 if extruder else -90,point)

def load_base():
    data=json.loads((SRC/'manifest.json').read_text()); result=[]
    for r in data['objects']:
        path=SRC/(r['name']+'.brep')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=r.get('brep_sha256'):raise ValueError('Stale BRep cache:'+r['name'])
        s=Part.Shape(); s.read(str(path))
        result.append(dict(r,shape=s))
    return result

def layout(base_items=None):
    items=load_base() if base_items is None else base_items; out=[]; changed=[]
    drop={'DriveMotorGMP60Reference','DriveAdapterGMP60','MotorMountPlate',
          'MotorSprocket12T','ChainTightSide','ChainSlackSide','DriveGuard',
          'ExtruderSupportRailRear','HeaterCableDuctBridgeX','HeaterCableDuctBridgeY'}
    for obj in items:
        n=obj['name']
        if n in drop: continue
        obj=dict(obj)
        if obj['group'] in {'extruder','forming'} or (obj['group']=='feed' and not(n.startswith('PPR-C03') or n=='FlakeBin')):
            obj['shape']=moved(obj['shape'],(0,0,1),90,(667,0,0)); changed.append(n)
        elif obj['group']=='control' and n not in {'CableDuct'} and not n.startswith('PPR-C12'):
            obj['shape']=moved(obj['shape'],offset=(-210,0,0)); changed.append(n)
        out.append(obj)
    for name,pt,ex in [('GGM_Shredder',(153,180,676.167),False),('GGM_Extruder',(320,477,382),True)]:
        out.append(item(name,motor_pose(ggm_local(),pt,ex),'drive','GGM K9DG60N2 + K9G75C/150C','purchased_reference_envelope')); changed.append(name)
    return out,changed
