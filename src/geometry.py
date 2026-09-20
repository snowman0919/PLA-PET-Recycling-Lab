"""Deterministic section geometry. Units: millimetres, radians."""
import math
import numpy as np

def cycloid_profile(R=70., e=7., pins=9, roller_r=8., clearance=.10, samples=1440):
    u=np.linspace(0,2*math.pi,samples,endpoint=False)
    q=np.column_stack((R*np.cos(u)-e*np.cos(pins*u),R*np.sin(u)-e*np.sin(pins*u)))
    d=np.column_stack((-R*np.sin(u)+pins*e*np.sin(pins*u),R*np.cos(u)-pins*e*np.cos(pins*u)))
    normal=np.column_stack((-d[:,1],d[:,0]))/np.linalg.norm(d,axis=1)[:,None]
    return (q+(roller_r+clearance)*normal).tolist()

def hooks(tip=40., root=23., n=7, samples=16, direction=1):
    pts=[]
    for j in range(n):
        for k in range(samples):
            u=k/samples
            if u<=.76:
                t=u/.76
                r=root+(tip-root)*(t-math.sin(2*math.pi*t)/(2*math.pi))
            else:
                r=tip-(tip-root)*(u-.76)/.24
            a=direction*2*math.pi*(j+u)/n
            pts.append([r*math.cos(a),r*math.sin(a)])
    if direction<0: pts.reverse()
    return pts

def gear_section(module, teeth, pressure=20., samples=7):
    """Reference involute section; root fillets/tolerances NOT a manufacturing profile."""
    rp=module*teeth/2; rb=rp*math.cos(math.radians(pressure)); ra=rp+module; rr=rp-1.25*module
    invp=math.tan(math.radians(pressure))-math.radians(pressure)
    pts=[]
    for j in range(teeth):
        center=2*math.pi*j/teeth
        for side,rs in [(-1,np.linspace(max(rr,rb),ra,samples)),(1,np.linspace(ra,max(rr,rb),samples))]:
            for r in rs:
                a=math.acos(min(1,rb/r)); inv=math.tan(a)-a
                ang=center+side*(math.pi/(2*teeth)+invp-inv)
                pts.append([r*math.cos(ang),r*math.sin(ang)])
            if side==1:
                ang=center+math.pi/(2*teeth)+invp
                pts.append([rr*math.cos(ang),rr*math.sin(ang)])
                ang=2*math.pi*(j+1)/teeth-math.pi/(2*teeth)-invp
                pts.append([rr*math.cos(ang),rr*math.sin(ang)])
    return pts

def chain_center(pitch,n1,n2,links):
    a=(n1+n2)/2; b=((n1-n2)/(2*math.pi))**2
    return pitch*((links-a)+math.sqrt((links-a)**2-8*b))/4
