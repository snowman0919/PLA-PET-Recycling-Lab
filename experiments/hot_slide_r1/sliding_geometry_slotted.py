"""FreeCAD prototype: replace hard radial fit by three elastic shoes.
Not an approved machine variant. All source dimensions are millimetres.
"""
from pathlib import Path
import json, math, sys
import FreeCAD as App, Part
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'prototype_geometry_slotted'; OUT.mkdir(exist_ok=True)
SPEC=json.loads((ROOT/'contract.json').read_text())
def cyl(r,h): return Part.makeCylinder(r,h)
def rotor_sheet(web=2.0, rfree=SPEC["shoe_free_radius_mm"], thickness=3.0):
    rim=cyl(35,thickness).cut(cyl(30,thickness))
    arm=Part.makeBox(web,27,thickness,App.Vector(20-web/2,-27,0))
    shoe=Part.makeBox(8,6,thickness,App.Vector(14,-3,0))
    branch=arm.fuse(shoe).cut(cyl(rfree,thickness))
    for deg in (30,150,270):
        part=branch.copy(); part.rotate(App.Vector(),App.Vector(0,0,1),deg)
        rim=rim.fuse(part)
    for deg in (90,210,330):
        a=math.radians(deg);c=App.Vector(32.5*math.cos(a),32.5*math.sin(a),0)
        rim=rim.fuse(Part.makeCylinder(6,thickness,c))
        slot=Part.makeCylinder(2.02,thickness,App.Vector(32.5-1.98,0,0)).fuse(Part.makeCylinder(2.02,thickness,App.Vector(32.5+1.98,0,0)))
        slot=slot.fuse(Part.makeBox(3.96,4.04,thickness,App.Vector(32.5-1.98,-2.02,0)))
        slot.rotate(App.Vector(),App.Vector(0,0,1),deg)
        rim=rim.cut(slot)
    rim=rim.removeSplitter()
    targets=[(e.CenterOfMass.x,e.CenterOfMass.y) for e in rim.Edges if e.BoundBox.ZLength>thickness-.01 and e.BoundBox.XLength<.01 and e.BoundBox.YLength<.01 and 18 < math.hypot(e.CenterOfMass.x,e.CenterOfMass.y) < 30.1]
    applied=[]
    for x,y in targets:
        matching=[e for e in rim.Edges if e.BoundBox.ZLength>thickness-.01 and math.hypot(e.CenterOfMass.x-x,e.CenterOfMass.y-y)<.01]
        if not matching:continue
        for radius in (.6,.4,.25):
            try:
                rounded=rim.makeFillet(radius,[matching[0]])
                if rounded.isValid() and len(rounded.Solids)==1:
                    rim=rounded;applied.append([x,y,radius]);break
            except Exception:pass
    print('FILLETS',len(applied),'/',len(targets),applied,flush=True)
    (OUT/'fillets.json').write_text(json.dumps({'targets':targets,'applied':applied}))
    assert rim.isValid() and len(rim.Solids)==1 and rim.Volume>0
    return rim
def main():
    shape=rotor_sheet()
    doc=App.newDocument('HS_R1_sheet')
    obj=doc.addObject('PartDesign::Feature','HS_R1_FLEXURE_SHEET');obj.Shape=shape;doc.recompute()
    path=OUT/'HS-R1-sheet.step';Part.export([obj],str(path))
    imported=Part.read(str(path))
    assert imported.isValid() and len(imported.Solids)==1
    err=abs(imported.Volume-shape.Volume)/shape.Volume
    assert err<1e-6
    shape.exportBrep(str(OUT/'HS-R1-sheet.brep'))
    doc.saveAs(str(OUT/'HS-R1-sheet.FCStd'))
    (OUT/'metadata.json').write_text(json.dumps({'state':'PROTOTYPE_ONLY','volume_mm3':shape.Volume,'step_reimport_relative_volume_error':err,'base_ring_diameter_mm':70,'overall_bbox_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength],'thickness_mm':3,'web_mm':2,'shoe_free_radius_mm':SPEC['shoe_free_radius_mm'],'physical_validation':'NOT_RUN'},indent=2))
    print('SLIDING_PROTOTYPE_GEOMETRY_READY',shape.Volume,flush=True)
if __name__=='__main__':main()
