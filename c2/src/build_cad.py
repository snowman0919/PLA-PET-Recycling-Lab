"""C2 S2 thermal/fixed-shear development module. Not an assembly release.
C1 cutting rotor dimensions are retained only as a reference seed.
"""
from pathlib import Path
import math
import json
import hashlib
import numpy as np
import cadquery as cq
from engineering import ROOT,S2,write_json
from pin_constraint import profile
V=cq.Vector


def wire(points):
    return cq.Wire.makePolygon([V(*p) for p in points],close=True)


def xz(points,depth,y=0):
    return cq.Solid.extrudeLinear(wire([[x,y,z] for x,z in points]),[],V(0,depth,0))


def sector(r0,r1,a0,a1,depth,y=0):
    angle=np.linspace(math.radians(a0),math.radians(a1),max(40,round((a1-a0)*2)))
    pts=[[r1*math.cos(a),r1*math.sin(a)] for a in angle]+[[r0*math.cos(a),r0*math.sin(a)] for a in angle[::-1]]
    return xz(pts,depth,y)


def cylinder(r,h,at=(0,0,0),axis=(0,1,0)):
    return cq.Solid.makeCylinder(r,h,V(*at),V(*axis))


def box(d,at):
    return cq.Solid.makeBox(*d,V(*at))


def primitive(s):
    at=s.get('at',[0,0,0]);axis=s.get('axis',[0,1,0]);k=s['kind']
    if k=='cylinder':return cylinder(s['r'],s['h'],at,axis)
    if k=='box':return box(s['size'],at)
    if k=='polygon':return xz(s['points'],s['h']).translate(tuple(at))
    raise ValueError(k)


def from_c1(p):
    s=primitive(p['adds'][0])
    for a in p['adds'][1:]:s=s.fuse(primitive(a))
    for a in p['cuts']:s=s.cut(primitive(a))
    return s.clean()


def main():
    out=ROOT/'cad';out.mkdir(exist_ok=True)
    ref=json.loads((ROOT/'design/c1_s2_reference.json').read_text())
    parts={};notes={};qty={}
    def add(pid,s,n,q=1):
        parts[pid]=s.clean();notes[pid]=n;qty[pid]=q
    # Reference seed only: same bearing counterbores and 40mm active region as C1.
    add('C1_ROTOR_REFERENCE',from_c1(ref['S2-ROTOR']).translate((7,-255,0)),
        'C1 dimensional reference, not C2 optimum. Bearings and full drive frame omitted.')
    add('C1_SCREEN_REFERENCE',from_c1(ref['S2-SCREEN']),
        'C1 4mm perforation reference. Particle size and screen attachment are not qualified.')
    add('C1_LEFT_WEAR_SHELL',from_c1(ref['S2-CASE-L']),
        'C1 3mm steel wear shell reference; original feed/screen sectors remain open.')
    window=box([12,42,8.2],[62.5,-1,-4.1])
    split_shell=from_c1(ref['S2-CASE-R']).cut(window)
    for index,piece in enumerate(split_shell.Solids()):
        add(f'C2_RIGHT_WEAR_SHELL_{index+1}',piece,
            'Separate steel liner arc adjoining fixed-shear cartridge. Captured by metal caps; corner radii and seal HOLD.')
    # Replaceable steel shear insert backed by the metal saddle, no printed cutting edge.
    blade=xz([[62.8,-.3],[65.8,-4],[71,-4],[71,4],[65.8,4],[62.8,.3]],40)
    for y in [12,28]:blade=blade.cut(cylinder(1.65,4.6,(66.5,y,0),(1,0,0)))
    blade=blade.cut(cylinder(1.6,3.6,(67.5,20,0),(1,0,0)))
    add('C2_FIXED_SHEAR',blade,
        'Steel/tool-steel coupon: 40mm width; nominal tip x62.8; two M4 pilot bores depth4.5; '
        'sensor blind bore3.2mm at y20, depth3.5. Tip radius/heat treat/tapped thread/retention loads HOLD.')
    saddle_parameters=[('L',163,217,[170,210],[175,190,205]),
                       ('R',323,437,[330,430],[335,350,370,390,410,425])]
    for label,a0,a1,holes,fins in saddle_parameters:
        s=sector(66,73,a0,a1,40)
        for angle in fins:
            fin=box([13.5,38,2],[72.5,1,-1]).rotate((0,0,0),(0,1,0),-angle)
            s=s.fuse(fin)
        if label=='R':
            s=s.cut(box([9.2,42,8.2],[62,-1,-4.1]))
            for y in [12,28]:s=s.cut(cylinder(2.25,18,(71,y,0),(1,0,0)))
            s=s.cut(cylinder(1.6,18,(71,20,0),(1,0,0)))
        for angle in holes:
            th=math.radians(angle)
            s=s.cut(cylinder(2.25,42,(69.5*math.cos(th),-1,69.5*math.sin(th))))
        add('C2_THERMAL_SADDLE_'+label,s,
            'Aluminium development part: nominal Ri66/Ro73, 40mm width, fins toR86; '
            '0.2mm nominal interface to steel OD65.8 needs qualified conductive interface. '
            'Axial4.5mm holes onR69.5. Not a measured UA or a certified blade restraint.')
        cap=sector(65.6,76.5,a0,a1,4)
        for angle in holes:
            th=math.radians(angle)
            cap=cap.cut(cylinder(2.25,6,(69.5*math.cos(th),-1,69.5*math.sin(th))))
        add('C2_SADDLE_CAP_'+label,cap,
            '4mm metal end cap. Paired caps bear on steel arc end faces; bolt lengths/locking and frame reaction HOLD.',2)
    # Two interchangeable guide study blanks, not two simultaneously fitted mechanisms.
    checks=json.loads((ROOT/'results/pin_constraint_checks.json').read_text())
    study_ids=['C1-SEED','C2-046']
    candidates={r['design']['candidate_id']:r['design'] for r in json.loads((ROOT/'results/s2_candidates.json').read_text())}
    for cid in study_ids:
        p=next(x for x in checks if x['candidate_id']==cid)
        c=S2(**candidates[cid]);outline=profile(p['pin_R_mm'],c.eccentric_mm,c.ratio_denominator+1)
        blank=xz(outline,10).cut(cylinder(23,12,(0,-1,0)))
        for angle in np.linspace(0,2*np.pi,8,endpoint=False):
            blank=blank.cut(cylinder(2.75,12,(35*math.cos(angle),-1,35*math.sin(angle))))
        add('GUIDE_STUDY_'+cid,blank,
            'Interchangeable constraint study only. 46mm central bore, 8x5.5PCD70,10mm thick. '
            'Rotary bearing seat/root integrity and contact fatigue need design-specific DFM.')
    records=[]
    for pid,s in parts.items():
        if not s.isValid() or len(s.Solids())!=1:
            raise RuntimeError(f'Invalid or disconnected solid {pid}: {len(s.Solids())}')
        filename=out/(pid+'.step')
        cq.exporters.export(s,str(filename))
        imported=cq.importers.importStep(str(filename)).val()
        relative=abs(imported.Volume()-s.Volume())/s.Volume()
        if not imported.isValid() or len(imported.Solids())!=1 or relative>1e-7:
            raise RuntimeError('STEP roundtrip failed '+pid)
        b=s.BoundingBox()
        records.append(dict(part_id=pid,quantity=qty[pid],valid=True,solids=1,volume_mm3=s.Volume(),
                            size_mm=[b.xlen,b.ylen,b.zlen],step_relative_volume_error=relative,
                            sha256=hashlib.sha256(filename.read_bytes()).hexdigest(),notes=notes[pid]))
    placed=[];placed_names=[]
    for pid,s in parts.items():
        if pid.startswith('GUIDE_STUDY'):continue
        if pid.startswith('C2_SADDLE_CAP'):
            for yy in [-4,40]:placed.append(s.translate((0,yy,0)));placed_names.append(pid+str(yy))
        else:placed.append(s);placed_names.append(pid)
    assembly=cq.Compound.makeCompound(placed)
    cq.exporters.export(assembly,str(out/'PPR_C2_S2_thermal_development.step'))
    contacts=[]
    for i,a in enumerate(placed):
        for j in range(i+1,len(placed)):
            b=placed[j]
            aa,bb=a.BoundingBox(),b.BoundingBox()
            if min(aa.xmax,bb.xmax)-max(aa.xmin,bb.xmin)<1e-4:continue
            if min(aa.ymax,bb.ymax)-max(aa.ymin,bb.ymin)<1e-4:continue
            if min(aa.zmax,bb.zmax)-max(aa.zmin,bb.zmin)<1e-4:continue
            v=a.intersect(b).Volume()
            if v>.001:contacts.append(dict(a=placed_names[i],b=placed_names[j],overlap_mm3=v))
    b=assembly.BoundingBox()
    result=dict(status='DEVELOPMENT_GEOMETRY_NOT_FABRICATION_RELEASE',part_types=len(parts),
                module_instances=len(placed),module_bounds_mm=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax],
                records=records,static_overlaps_in_module=contacts,
                assembly_scope='S2 cutting/cooling coupon module only; no complete C2 machine or motor integration',
                not_checked=['full_machine_interference','shaft_bearing_seal_assembly','blade_bolt_strength',
                             'all_rotor_phases_with_shear','finned_cooling_performance','pin_contact_stress'],
                procurement='HOLD',fabrication='HOLD',energization='HOLD')
    write_json(ROOT/'results/cad_validation.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))

if __name__=='__main__':main()
