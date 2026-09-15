"""Explicit local support and attachment details for the GGM drive package."""
import FreeCAD as App
import Part
from layout import item

def details(items):
    new=[]
    def add(n,s,material,kind='manufactured_or_stock'):
        new.append(item(n,s,'drive',material,kind))
    holder=Part.makeBox(48,10,48,App.Vector(296,401,358))
    holder=holder.cut(Part.makeCylinder(16.015,10,App.Vector(320,401,382),App.Vector(0,1,0)))
    for x in (301,339):
        for z in (363,401):
            holder=holder.cut(Part.makeCylinder(2.25,10,App.Vector(x,401,z),App.Vector(0,1,0)))
            for r in items:
                if r['name']=='ThrustPlate':
                    r['shape']=r['shape'].cut(Part.makeCylinder(1.65,10,App.Vector(x,391,z),App.Vector(0,1,0)))
    for x in (300,340): holder=holder.cut(Part.makeCylinder(1.25,10,App.Vector(x,401,382),App.Vector(0,1,0)))
    add('GGM_EX_RadialHolder',holder,'S275 t10; bore32.03; 4x4.5; matching M4 in thrust plate')
    bearing=Part.makeCylinder(16,10,App.Vector(320,401,382),App.Vector(0,1,0)).cut(Part.makeCylinder(6,10,App.Vector(320,401,382),App.Vector(0,1,0)))
    add('GGM_EX_Radial6201',bearing,'6201-2RS 12x32x10','purchased_reference_envelope')
    cap=Part.makeCylinder(23,2,App.Vector(320,411,382),App.Vector(0,1,0)).cut(Part.makeCylinder(13.7,2,App.Vector(320,411,382),App.Vector(0,1,0)))
    for x in (300,340): cap=cap.cut(Part.makeCylinder(1.7,2,App.Vector(x,411,382),App.Vector(0,1,0)))
    add('GGM_EX_RadialCap',cap,'steel t2; ID27.4 outer-ring-only retainer; M3 screws')
    # Abut the bearing outer ring, not its seal or inner ring.
    for row in items:
        if row['name']=='ThrustPlate':
            row['shape']=row['shape'].cut(Part.makeCylinder(13.7,0.30,
                App.Vector(320,400.70,382),App.Vector(0,1,0)))
    # Two welded stock steel angles tie the motor plate to its base.
    for x in (83,201):
        foot=Part.makeBox(22,36,6,App.Vector(x,144,536))
        back=Part.makeBox(22,6,100,App.Vector(x,174,542))
        add('GGM_SH_Angle'+str(x),foot.fuse(back).removeSplitter(),'S275 stock angle; continuous3mm fillet both legs; jig before welding')
    from guard_details import finish_guards
    finish_guards(items + new)
    return new
