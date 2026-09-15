"""Standalone pressureless sliding test fixture; not a machine replacement."""
from pathlib import Path
import sys,json,hashlib
import FreeCAD as App,Part,importDXF
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'fixture';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
from sliding_geometry_slotted import rotor_sheet

def circle(r,h,p=(0,0,0),axis=(0,0,1)):
    return Part.makeCylinder(r,h,App.Vector(*p),App.Vector(*axis))

def carrier():
    # Clamp to a flat base; three fixed shoulder pins engage radial slots.
    solid=Part.makeBox(90,7,95,App.Vector(-45,0,0))
    solid=solid.fuse(Part.makeBox(90,36,8,App.Vector(-45,0,0)))
    solid=solid.cut(circle(23,7,(0,0,50),(0,1,0)))
    import math
    for deg in (90,210,330):
        a=math.radians(deg)
        solid=solid.cut(circle(2.01,7,(32.5*math.cos(a),0,50-32.5*math.sin(a)),(0,1,0)))
    for x in (-32,32):solid=solid.cut(circle(3.3,8,(x,24,0)))
    return solid.removeSplitter()

def local_to_station(shape,y):
    s=shape.copy();s.rotate(App.Vector(),App.Vector(1,0,0),-90);s.translate(App.Vector(0,y,50));return s
def export_one(name,shape):
    assert shape.isValid() and len(shape.Solids)==1
    path=OUT/(name+'.step');doc=App.newDocument(name.replace('-','_'))
    obj=doc.addObject('PartDesign::Feature',name.replace('-','_'));obj.Shape=shape;doc.recompute()
    Part.export([obj],str(path));doc.saveAs(str(OUT/(name+'.FCStd')))
    importDXF.export([obj],str(OUT/(name+'.dxf')))
    back=Part.read(str(path));err=abs(back.Volume-shape.Volume)/shape.Volume
    assert back.isValid() and len(back.Solids)==1 and err<1e-6
    App.closeDocument(doc.Name)
    return {'part_id':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'volume_mm3':shape.Volume,'reimport_relative_error':err}

def main():
    sheet=rotor_sheet();items=[]
    base=Part.makeBox(100,270,10,App.Vector(-50,-15,-10))
    for y in (24,164):
        for x in (-32,32):base=base.cut(circle(2.5,10,(x,y,-10)))
    for x in (-20,20):base=base.cut(circle(2.5,10,(x,236,-10)))
    carrier_shape=carrier();mandrel=circle(17,216,(0,-8,50),(0,1,0))
    mandrel=mandrel.fuse(Part.makeCone(16,17,2,App.Vector(0,-10,50),App.Vector(0,1,0)))
    mandrel=mandrel.fuse(Part.makeCone(17,16,2,App.Vector(0,208,50),App.Vector(0,1,0)))
    mandrel=mandrel.cut(circle(2.5,10,(0,200,50),(0,1,0))).removeSplitter()
    records=[export_one('HS-R1-SHEET',sheet),export_one('HS-R1-CARRIER',carrier_shape),export_one('HS-R1-BASE',base),export_one('HS-R1-MANDREL',mandrel)]
    items.append(('Base',base));items.append(('Open_mandrel_no_pressure',mandrel))
    for station,y in enumerate((0,140)):
        c=carrier_shape.copy();c.translate(App.Vector(0,y,0));items.append((f'Carrier{station}',c))
        for i in range(6):items.append((f'Sheet{station}_{i}',local_to_station(sheet,y+7.25+3.25*i)))
    import math
    pin=circle(2,27.4).fuse(circle(3.5,2,(0,0,-2))).fuse(circle(1.5,8,(0,0,27.4)))
    shim=circle(3,.25).cut(circle(2.05,.25))
    adjust=circle(3,.35).cut(circle(2.05,.35))
    washer=circle(4.25,.8).cut(circle(1.6,.8))
    nut=circle(3.2,2.4).cut(circle(1.5,2.4))
    for station,y in enumerate((0,140)):
        for angle in (90,210,330):
            theta=math.radians(angle);dx=32.5*math.cos(theta);dz=-32.5*math.sin(theta)
            for name,shape,local_y in [('PIN',pin,0),('WASHER',washer,27.4),('NUT',nut,28.2),('LOCKNUT',nut,30.6),('ADJUST035',adjust,26.75)]+[('SHIM'+str(i),shim,7+3.25*i) for i in range(7)]:
                item=local_to_station(shape,y+local_y);item.translate(App.Vector(dx,0,dz));items.append((f'{name}_{station}_{angle}',item))
    stop=Part.makeBox(60,6,65,App.Vector(-30,223,0)).fuse(Part.makeBox(60,25,8,App.Vector(-30,220,0)))
    stop=stop.cut(circle(5,6,(0,223,50),(0,1,0)))
    for x in (-20,20):stop=stop.cut(circle(3.3,8,(x,236,0)))
    stop=stop.removeSplitter();records.append(export_one('HS-R1-STOP-BRACKET',stop));items.append(('Positive_travel_stop',stop))
    stud=circle(3,70,(0,200,50),(0,1,0));items.append(('M6_pull_stud_thread_reference',stud))
    for y in (218.4,232):items.append(('M6_stop_washer_'+str(y),circle(9,1.6,(0,y,50),(0,1,0)).cut(circle(3.3,1.6,(0,y,50),(0,1,0)))))
    for y,l in ((210.4,3),(213.4,5),(233.6,5),(238.6,3)):
        items.append(('M6_stop_nut_ref_'+str(y),circle(5.5,l,(0,y,50),(0,1,0)).cut(circle(3,l,(0,y,50),(0,1,0)))))
    # Free-state sheet/mandrel overlap is intentional elastic preload, not assembled geometry.
    doc=App.newDocument('HS_R1_BENCH_REVIEW')
    for name,shape in items:
        obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape
    doc.recompute();Part.export(doc.Objects,str(OUT/'HS-R1-BENCH-REVIEW.step'))
    assert Part.read(str(OUT/'HS-R1-BENCH-REVIEW.step')).isValid()
    doc.saveAs(str(OUT/'HS-R1-BENCH-REVIEW.FCStd'));App.closeDocument(doc.Name)
    pin=circle(2,27.4).fuse(circle(3.5,2,(0,0,-2))).fuse(circle(1.5,8,(0,0,27.4)))
    washer=circle(3,.25).cut(circle(2.05,.25))
    records += [export_one('HS-R1-PIN',pin),export_one('HS-R1-SHIM025',washer),export_one('HS-R1-ADJUST035',adjust)]
    (OUT/'manifest.json').write_text(json.dumps({'status':'PRESSURELESS_TEST_FIXTURE_DESIGN','nominal_mechanical_travel_limits_mm':[-3.0,3.0],'base_dimensions_mm':[100,270,10],'assembly_model':'Free-state sheets intentionally overlap mandrel; nuts/studs are purchased-part envelopes, threads omitted','physical_state':'NOT_RUN','rows':records,'mounting':'pin4mm shoulder27.40+/-0.02mm + M3 thread8; nuts seat on shoulder via M3 washer, not spring stack; match shim cold axial endplay0.25-0.35mm','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),ROOT/'sliding_geometry_slotted.py',ROOT/'contract.json')}},indent=2))
    print('SLIDING_FIXTURE_GEOMETRY_READY',len(records),flush=True)
if __name__=='__main__':main()
