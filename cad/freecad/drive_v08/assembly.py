"""Motor integration: lengthwise direct extrusion and supported shredder shaft."""
import FreeCAD as App
import Part
from layout import layout,item,moved,motor_pose
from parts import fuse_hubs,motor_plate,jackshaft,bearing_plate,sprocket,key,guard

def box(x,y,z,dx,dy,dz): return Part.makeBox(dx,dy,dz,App.Vector(x,y,z))
def ring(r,ri,h,point,direction):
    return Part.makeCylinder(r,h,App.Vector(*point),App.Vector(*direction)).cut(Part.makeCylinder(ri,h,App.Vector(*point),App.Vector(*direction)))

def integrated_objects(base_items=None):
    items,changed=layout(base_items); removed={'ExtruderDrive','CutterSprocket30T'}
    items=[r for r in items if r['name'] not in removed]
    def add(n,s,material='S275 steel',kind='manufactured_or_stock',group='drive'):
        items.append(item(n,s,group,material,kind)); changed.append(n)
    for r in items:
        if r['name']=='FlakeBin' or r['name'].startswith('PPR-C03'):
            r['shape']=moved(r['shape'],offset=(0,10,0)); changed.append(r['name'])
        if r['name']=='ShredderCableRouteEnvelope':
            r['shape']=moved(r['shape'],offset=(75,0,0)); changed.append(r['name'])
        if r['name']=='ShredderRPMSensorEnvelope':
            r['shape']=moved(r['shape'],offset=(0,11,0)); changed.append(r['name'])
        if r['name']=='MidRail500':
            r['shape']=box(20,270,480,430,20,40);r['material']='2040 profile L430; 40mm vertical; top datum520';changed.append(r['name'])
        if r['name']=='MidRail320':
            r['shape']=moved(r['shape'],offset=(0,-11,0));changed.append(r['name'])
        if r['name']=='Screw':
            # Replace erroneous transverse notch by an axial rear drive keyseat.
            s=r['shape'].fuse(Part.makeCylinder(6,35,App.Vector(320,400,382),App.Vector(0,1,0)))
            r['shape']=s.cut(box(313.0,414,379.975,3.5,20,4.05)).removeSplitter()
            r['material']='EX-SCR-01-G: drive keyseat 4.05 x20; bearing land Y401..411 uninterrupted, finish after turn'
            changed.append(r['name'])
    for n,y,z in [('GGM_ShredRail',90,500),('GGM_HotRearRail',349,320),('GGM_ThrustRail',401,315),('GGM_ExMotorRail',477,315),('GGM_FeederTopRail',440,910)]:
        shape=box(20,y,480,430,20,40) if n=='GGM_ShredRail' else box(20,y,z,430,20,20)
        add(n,shape,'2040 profile L430; 40mm vertical' if n=='GGM_ShredRail' else '2020 profile L430; bracketed ends','purchased_reference_lod','frame')
    for x in (274.5,345.5): add('GGM_ThrustPost'+str(x),box(x,401,335,20,20,100),'2020 profile L100','purchased_reference_lod','frame')
    add('GGM_FeederHanger',box(335,440,786,20,20,124),'2020 profile L124','purchased_reference_lod','frame')
    shelf=box(40,50,530,235,253,6)
    for x in (90,220):
        for y in (100,280): shelf=shelf.cut(Part.makeCylinder(3.3,6,App.Vector(x,y,530)))
    for x in (55,248):
        for y in (233,293): shelf=shelf.cut(Part.makeCylinder(2.75,6,App.Vector(x,y,530)))
    add('GGM_SH_Base',shelf,'6 mm S275 sheet; fourM6 base holes plus fourM5 end-tap post holes')
    for x in (90,220):
        for y in (100,280): add('GGM_SH_Spacer_%s_%s'%(x,y),ring(6,3.3,10,(x,y,520),(0,0,1)),'steel spacer 12/6.6 x10')
    sh_plate=motor_pose(motor_plate(True),(153,210,676.167))
    # Cut straight lower edge to sit on shelf; weld two stock 40x40 angles.
    sh_plate=sh_plate.cut(box(50,200,500,220,30,36))
    add('GGM_SH_Mount',sh_plate,'6 mm S275 plate; 4x6.6 PCD104; pilot36.5')
    for x in (45,238):
        for y in (253,313): add('GGM_SH_Post_%s_%s'%(x,y),box(x,y,536,20,20,180),'2020 profile L180','purchased_reference_lod')
    for y in (273,303):
        add('GGM_SH_BearingPlate'+str(y),moved(bearing_plate(),(1,0,0),-90,(153,y,676.167)),'216x60x10 plate,32.03 bore,193x40 asymmetric hole grid; rings retained by caps')
        add('GGM_SH_Bearing'+str(y),ring(16,6,10,(153,y,676.167),(0,1,0)),'6201-2RS 12x32x10','purchased_reference_envelope')
    add('GGM_SH_Jackshaft',motor_pose(jackshaft(),(153,246,676.167)),'S45C 12 h6 x78; two 4 mm keys')
    add('GGM_SH_12T',motor_pose(sprocket(12,12.05,13.5,-3,15),(153,288,676.167)),'BUY #35 12T steel, hub15, key4.1','purchased_reference_envelope')
    large=motor_pose(sprocket(30,25.05,22,0,30),(153,288,590)); large.rotate(App.Vector(153,288,590),App.Vector(0,1,0),25.714)
    add('GGM_SH_30T',large,'BUY #35 30T steel, hub28, key6.1','purchased_reference_envelope')
    for label,pt,ex in [('SH',(153,218,676.167),False),('EX',(320,469,382),True)]:
        for suffix,s in zip(('Input','Output','PinBlank'),fuse_hubs()):
            if ex: s=motor_pose(s,pt,True)
            else: s=motor_pose(s,pt)
            add('GGM_'+label+'_Fuse'+suffix,s,'S45C hubs / brass uncalibrated pin blank; release target8.8-9.3Nm')
    ex_plate=motor_plate(False)
    for y in (-40,40): ex_plate=ex_plate.cut(Part.makeCylinder(2.75,6,App.Vector(-57,y,0)))
    add('GGM_EX_Mount',motor_pose(ex_plate,(320,477,382),True),'6 mm S275 plate; use catalog eccentric output datum')
    # Standard retaining rings/caps positively retain jackshaft bearing outer rings.
    for y in (271,283,301,313):
        cap=ring(23,13.7,2,(153,y,676.167),(0,1,0))
        for x in (133,173): cap=cap.cut(Part.makeCylinder(1.7,2,App.Vector(x,y,676.167),App.Vector(0,1,0)))
        add('GGM_SH_BearingCap'+str(y),cap,'2 mm steel; M3 retainer screws')
    # Machined hubs transmit torque by keys; radial set screws retain axially only.
    for n,y,l in [('MotorKey',213,25),('JackInputKey',248.4,22),('JackSprocketKey',285,15)]:
        add('GGM_SH_'+n,motor_pose(key(l),(153,y,676.167)),'4x4 steel key')
    for n,y,l in [('MotorKey',449,25),('ScrewKey',417,17)]:
        add('GGM_EX_'+n,box(312.5,y,380,4,l,4),'4x4 steel key')
    # Lower load carrier keyed at original shaft clocking.
    k=Part.makeBox(6,20,6,App.Vector(-3,0,9))
    k=moved(k,(0,1,0),25.714,(153,293,590))
    add('GGM_SH_CutterKey',k,'6x6x20 steel key')
    # Profile fasteners are reference volumes; profile T-slot voids are omitted.
    for n,x,y,z in [('EX_MountL',280,465,325),('EX_MountR',360,465,325)]:
        add('GGM_M5_'+n,Part.makeCylinder(2.5,24,App.Vector(x,y,z),App.Vector(0,1,0)),'M5 class8.8 + matching T-nut','purchased_fastener')
    for r in items:
        if r['name'].startswith('GGM_SH_') and r['name']!='GGM_SH_Base' and not r['name'].startswith('GGM_SH_Spacer'):
            r['shape']=moved(r['shape'],offset=(0,-30,0))
    items=[r for r in items if r['name']!='FrameSpoolTopRail']
    for y,stop in ((290,349),(369,401),(421,477),(497,608)):
        add('SpoolTopSegment'+str(y),box(410,y,320,20,stop-y,20),'recut existing 2020','purchased_reference_lod','frame')
    for r in items:
        if r['name']=='FrameSpoolColumnFront':
            r['shape']=box(410,480,20,20,20,295); changed.append(r['name'])
    for label,pt,length in [('SH',(153,186,676.167),57),('EX',(320,413,382),58)]:
        shell=ring(25 if label=='EX' else 27,24 if label=='EX' else 25,length,pt,(0,1,0))
        add('GGM_'+label+'_CouplingGuard',shell,'2 mm rolled steel; removable seam and independent guard switch')
    shroud=box(94,250,537,118,24,173).cut(box(95,251,538,116,22,171))
    for y in (250,273):
        shroud=shroud.cut(Part.makeCylinder(25,1,App.Vector(153,y,676.167),App.Vector(0,1,0)))
    shroud=shroud.cut(Part.makeCylinder(24,1,App.Vector(153,273,590),App.Vector(0,1,0)))
    for r in items:
        if r['name'].startswith('GGM_SH_BearingPlate'):
            b=r['shape'].BoundBox
            shroud=shroud.cut(box(b.XMin-.3,b.YMin-.3,b.ZMin-.3,b.XLength+.6,b.YLength+.6,b.ZLength+.6))
    add('GGM_ChainGuard',shroud,'1 mm folded steel; bearing plates close upper cutouts; interlocked removable cover')
    for tag,y,length in [('front',240.4,2.6),('pinionfront',253,2),('pinionrear',270,3),('rear',283,1)]:
        add('GGM_JackInnerSpacer_'+tag,ring(8.5,6.05,length,(153,y,676.167),(0,1,0)),'steel ID12.1 OD17 shim/spacer; inner ring only')
    add('GGM_JackAxialCollar',ring(12,6.025,8,(153,284,676.167),(0,1,0)),'split shaft collar12mm; maxOD24 width8; received clamp verified','purchased_reference_envelope')
    from detail import details
    additions=details(items); items.extend(additions); changed.extend(r["name"] for r in additions)
    changed.append("ThrustPlate")
    return items,changed
