"""Stock/turned GGM integration parts; coordinates and tolerances in contract."""
import math
import FreeCAD as App
import Part

def cylinder(r,h,z=0): return Part.makeCylinder(r,h,App.Vector(0,0,z))
def keyed_bore(length,diameter=12.05,key=4.10,z=0):
    root=diameter/2-(3.6 if diameter>20 else 2.6)
    top=diameter/2+(3.1 if diameter>20 else 2.0)
    return cylinder(diameter/2,length,z).fuse(Part.makeBox(key,top-root,length,App.Vector(-key/2,root,z)))

def fuse_hubs():
    a=cylinder(14,22).fuse(cylinder(23,4,22)).fuse(cylinder(10,4,26))
    a=a.cut(keyed_bore(30))
    b=cylinder(23,4,26.4).fuse(cylinder(14,22,30.4))
    b=b.cut(keyed_bore(26,12.05,z=26.4)).cut(cylinder(10.05,4.2,26.4))
    for name in ('a','b'):
        s=locals()[name]
        s=s.cut(Part.makeCylinder(1.55,8.4,App.Vector(16,0,22)))
        z=12 if name=='a' else 40.4
        s=s.cut(Part.makeCylinder(1.65,14,App.Vector(0,0,z),App.Vector(0,1,0)))
        if name=='a': a=s
        else: b=s
    pin=Part.makeCylinder(1.5,11.7,App.Vector(16,0,21.7)).fuse(Part.makeCylinder(2,1,App.Vector(16,0,20.7)))
    pin=pin.cut(Part.makeCylinder(.45,4,App.Vector(16,-2,32),App.Vector(0,1,0)))
    return a.removeSplitter(),b.removeSplitter(),pin

def motor_plate(shredder=True):
    # Gearhead output is 18 mm above case centre, NOT centred in its square.
    bottom=-146.167 if shredder else -70
    s=Part.makeBox(140,50-bottom,6,App.Vector(-70,bottom,0))
    s=s.cut(Part.makeCylinder(18.25,6))
    a=104/(2*math.sqrt(2))
    for x in (-a,a):
        for y in (-18-a,-18+a): s=s.cut(Part.makeCylinder(3.3,6,App.Vector(x,y,0)))
    return s.removeSplitter()

def jackshaft():
    s=cylinder(6,78)
    for z,length in ((2.4,22),(39,18)):
        s=s.cut(Part.makeBox(4.0,3.0,length,App.Vector(-2,3.5,z)))
    return s.removeSplitter()

def bearing_plate():
    s=Part.makeBox(216,60,10,App.Vector(-108,-30,0))
    s=s.cut(Part.makeCylinder(16.015,10))
    for x in (-98,95):
        for y in (-20,20): s=s.cut(Part.makeCylinder(2.75,10,App.Vector(x,y,0)))
    for x in (-20,20):
        s=s.cut(Part.makeCylinder(1.25,10,App.Vector(x,0,0)))
    return s

def key(length,width=4,height=4):
    return Part.makeBox(width,height,length,App.Vector(-width/2,3.5,0))

def sprocket(teeth,bore,hub_r,hub_z0,hub_len):
    # Pitch/root envelope, not an ISO tooth cutting master. BUY standard #35.
    pitch=9.525; root=pitch/(2*math.sin(math.pi/teeth))-2.54
    s=cylinder(root,6).fuse(cylinder(hub_r,hub_len,hub_z0))
    return s.cut(keyed_bore(hub_len,bore,4.10 if bore<20 else 6.10,hub_z0)).removeSplitter()

def guard(width,depth,height,t=1):
    s=Part.makeBox(width,depth,height)
    s=s.cut(Part.makeBox(width-2*t,depth-2*t,height-2*t,App.Vector(t,t,t)))
    return s
