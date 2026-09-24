"""PPR C1 dimensional master. Generates a backend-neutral constructive-solid model."""
from pathlib import Path
import json, math, csv, hashlib, sys
import numpy as np
from geometry import hooks, cycloid_profile, gear_section, chain_center
ROOT=Path(__file__).resolve().parents[1]
PARTS={}; INST=[]
SOURCES={
 'TT60':'https://www.ttmotor.com/uploads/GMP60-609760127.pdf',
 'KHK_SH':'https://khkgears.net/pdf/sh.pdf',
 'KHK_SS':'https://khkgears.net/pdf/ss.pdf',
 'NSK6205':'https://www.nsk.com/engineering/6205-apn.html',
 'NSK6001':'https://www.nsk.com/engineering/6001-apn.html',
 'NSK6204':'https://www.nsk.com/engineering/6204-apn.html',
 'NSK51102':'https://www.nsk.com/engineering/51102-apn.html',
 'FAN':'https://products.sanyodenki.com/en/sanace/dc/dc-fan/9RA0824H1001/',
 'FAN_DK':'https://www.digikey.kr/ko/products/detail/sanyo-denki-america-inc/9RA0824H1001/16707729',
 'DRIVER':'https://www.pololu.com/product/2995',
 'TC':'https://www.adafruit.com/product/3263',
 'HANDOVER':'PPR_project_handover_2026-09-20.zip / 08_BOM_COMPONENTS.md',
 'DESIGN':'PPR-C1 original dimensional design; not an empirical qualification',
 'RFQ':'Supplier drawing / capacity confirmation required before procurement'
}
PARAMS={
 'revision':'C1','units':'mm','body_limit_mm':[650,420,510],
 'body_hard_limit_mm':[700,420,520],'operating_limit_mm':[850,450,510],
 'psu':{'V':24,'current_A':33,'nameplate_W':800,'current_derived_ceiling_W':792,'body_mm':[240,120,65],'operational_cap_W':500},
 'M1':{'motor':'TRK-60127-2460','gearbox':'GMP60','ratio':77,'rated_rpm':58,'rated_kgf_cm':160,'rated_A':8.2,'motor_can_mm':127,'gearbox_mm':59,'shaft_projection_mm':25.8,'shaft_mm':12,'OD_mm':60.5,'status':'MANUFACTURER_REFERENCE_NOT_OWNED'},
 'M2':{'motor':'TRK-6097-2425','gearbox':'GMP60','ratio':168,'rated_rpm':12,'rated_kgf_cm':150,'rated_A':1.8,'motor_can_mm':97,'gearbox_mm':70,'shaft_projection_mm':25.8,'shaft_mm':12,'OD_mm':60.5,'status':'MANUFACTURER_REFERENCE_NOT_OWNED'},
 'drive':{'normal_module':2,'helix_deg':15,'pinion_teeth':15,'gear_teeth':40,'half_face_mm':25,'half_hub_mm':10,'central_gap_mm':2,'branch_A_eta_assumed':.90,'branch_B_eta_assumed':.90,'chain_pitch_mm':9.525,'chain_A_teeth':[24,24],'chain_A_links':94,'chain_B_teeth':[24,12],'chain_B_links':84},
 'S1':{'cutter_tip_mm':80,'cutter_root_mm':46,'cutter_thickness_mm':6.,'spacer_thickness_mm':6.4,'spacer_OD_mm':36,'cutters_per_shaft':13,'shaft_mm':25,'shaft_center_mm':60,'axial_phase_mm':6.2,'end_gap_mm':.6,'hooks':7,'axial_key_mm':[8,7]},
 'S2':{'tip_mm':110,'root_mm':86,'active_width_mm':40,'eccentric_mm':7.,'radial_gap_mm':.8,'pin_ring_R_mm':72.,'fixed_pins':9,'guide_lobes':8,'pin_roller_OD_mm':16.,'guide_offset_allowance_mm':.2,'guide_samples':2880,'screen_hole_mm':4.,'screen_thickness_mm':2.,'screen_arc_deg':100,'orbit_ratio':2.,'self_over_orbit':-.125},
 'extruder':{'screw_OD_mm':16,'active_length_mm':256,'barrel_ID_mm':16.3,'barrel_OD_mm':30,'pitch_mm':16,'flight_thickness_mm':2,'feed_root_mm':10,'meter_root_mm':13,'shaft_thrust_seat_mm':15,'nominal_target_g_h':100,'heater_W':[100,100,100,60]},
 'cooling':{'working_length_mm':275,'filament_mm':1.75,'center_target_C':50,'status':'CONDITIONAL_THROUGHPUT_NOT_MEASURED'},
 'safety':{'release':'ENGINEERING_BASELINE_HOLD','procurement':'HOLD','energization':'HOLD','physical_test':'NOT_RUN','DEM':'NOT_RUN','3D_stress_FEA':'NOT_RUN'}
}
D=PARAMS['drive']; S1=PARAMS['S1']; S2=PARAMS['S2']
gearc=(D['pinion_teeth']+D['gear_teeth'])*D['normal_module']/2/math.cos(math.radians(D['helix_deg']))
ca=chain_center(9.525,24,24,94); cb=chain_center(9.525,24,12,84)
Z1=65+math.sqrt(ca**2-(80+gearc-130)**2)
X2=80+math.sqrt(cb**2-215**2)
PARAMS['datums']={'M1_xz':[80,65],'jack_xz':[80+gearc,65],'S1_main_xz':[130,Z1],'S1_slave_xz':[190,Z1],'S2_xz':[X2,280],'extruder_axis_yz':[275,125],'extruder_start_x':264,'chamber_S1_y':[162.4,324.6],'chain_A_center_mm':ca,'chain_B_center_mm':cb,'gear_center_mm':gearc}

def box(size,at=(0,0,0)): return {'kind':'box','size':list(size),'at':list(at)}
def cyl(r,h,at=(0,0,0),axis=(0,1,0)): return {'kind':'cylinder','r':r,'h':h,'at':list(at),'axis':list(axis)}
def cone(r1,r2,h,at=(0,0,0),axis=(0,1,0)): return {'kind':'cone','r1':r1,'r2':r2,'h':h,'at':list(at),'axis':list(axis)}
def poly(points,h,at=(0,0,0),plane='XZ'): return {'kind':'polygon','points':points,'h':h,'at':list(at),'plane':plane}
def ring(ro,ri,h,at=(0,0,0),axis=(0,1,0)):
 return [cyl(ro,h,at,axis)], [cyl(ri,h+2,tuple(at[k]-axis[k] for k in range(3)),axis)]
def part(pid,name,material,adds,cuts=None,source='DESIGN',status='CUSTOM_DFM_HOLD',notes='',drawing=True):
 PARTS[pid]={'id':pid,'name':name,'material':material,'adds':adds,'cuts':cuts or [],'source_id':source,'source':SOURCES[source],'status':status,'notes':notes,'drawing':drawing}
 return pid

def inst(pid,at=(0,0,0),rot=None,label=None,group=''):
 INST.append({'part':pid,'at':list(at),'rotation':rot or [0,0,1,0],'name':label or f'{pid}_{sum(i["part"]==pid for i in INST)+1:03d}','group':group})

def plate(pid,name,w,h,t,holes,material='S355 steel',notes='',source='DESIGN'):
 return part(pid,name,material,[box([w,t,h])],[cyl(r,t+2,(x,-1,z)) for x,z,r in holes],source=source,notes=notes)

# Existing profile cut plan. Hollow reference sections are NOT supplier slot geometry.
stock=[('2040',630,630),('2040',630,630),('2040',620,400),('2040',620,400),('2040',590,320),('2040',590,320),('2020',600,590),('2020',600,590),('2020',600,400),('2020',600,400),('2020',530,360),('2020',530,360),('2020',530,280),('2020',540,360)]
cut=[]
for k,(typ,raw,L) in enumerate(stock):
 kerf=0 if raw==L else 3
 cut.append({'stock_id':f'STK-{k+1:02d}','profile':typ,'stock_mm':raw,'cut_mm':L,'kerf_mm':kerf,'remaining_mm':raw-L-kerf,'owned':True})
for typ,L in sorted({(a,c) for a,b,c in stock}):
 w=40 if typ=='2040' else 20
 part(f'FR-{typ}-{L}',f'{typ} profile cut {L}', 'Al extrusion - existing',[box([L,w,20])],[box([L+2,w-4,16],[-1,2,2])],source='HANDOVER',status='OWNED_SLOT_PATTERN_TO_MEASURE',notes='Nominal section only. Confirm slot series before buying brackets; 3 mm saw kerf.',drawing=False)
for y in [0,360]: inst('FR-2040-630',(0,y,0),group='frame')
for x in [40,260]: inst('FR-2040-320',(x,40,0),[0,0,1,90],group='frame')
# Vertical members: long X axis is rotated into +Z.
for pid,x,y in [('FR-2040-400',20,40),('FR-2040-400',630,360),('FR-2020-400',630,40),('FR-2020-400',20,380)]:
 inst(pid,(x,y,20),[0,1,0,-90],group='frame')
for y in [40,380]: inst('FR-2020-590',(20,y,420),group='frame')
for x in [20,630]: inst('FR-2020-360',(x,40,420),[0,0,1,90],group='frame')
inst('FR-2020-360',(440,40,440),[0,0,1,90],group='frame')
inst('FR-2020-280',(340,100,20),[0,0,1,90],group='frame')
part('FR-BASE','Bottom tray 630x400x3','Al 5052',[box([630,400,3])],status='SHEET_DFM_HOLD',notes='Mains and hot zones require separate partitions; shown base is not sealed containment.')
inst('FR-BASE',(0,0,-3),group='frame')
# PSU true measured envelope; manufacturing mounting hole pattern deliberately absent.
part('EL-PSU','Owned 24V 800W PSU','Purchased',[box([240,120,65])],source='HANDOVER',status='OWNED_MOUNTING_PATTERN_UNMEASURED',notes='No guessed mounting holes. 120x240x65 user measurement; model contains true body only.',drawing=False)
inst('EL-PSU',(370,40,30),group='electrical')

# Motor physical interfaces based on exact TT PDF. Front face at Y=0, body negative Y.
for mid,can,gear in [('M1',127,59),('M2',97,70)]:
 adds=[cyl(30.25,can,(0,-can-gear,0)),cyl(30,gear,(0,-gear,0)),cyl(16,2),cyl(6,25.8)]
 cuts=[box([12,13,2],[-6,12.8,4.9])]
 for a in range(0,360,90):
  cuts.append(cyl(2.1,8,(22.5*math.cos(math.radians(a)),-8,22.5*math.sin(math.radians(a)))))
 part('DRV-'+mid,mid+' TT GMP60 motor reference','Purchased',adds,cuts,'TT60','DATASHEET_INTERFACE_REFERENCE','4xM5 PCD45, pilot32, shaft12 D10.9; encoder and wire exit not dimensioned in this option.',False)
inst('DRV-M1',(80,211,65),group='drive')
inst('DRV-M2',(187,275,125),[0,0,1,-90],group='extruder')
# Common 12 mm input shaft and motor plate.
plate('DRV-M1-PL','M1 mounting plate',70,65,6,[(35,32.5,16.1)]+[(35+22.5*math.cos(math.radians(a)),32.5+22.5*math.sin(math.radians(a)),2.75) for a in range(0,360,90)]+[(7,7,3.3),(63,7,3.3),(7,58,3.3),(63,58,3.3)],notes='Motor axis datum(35,32.5); 4x5.5 THRU onPCD45. Confirm motor engagement depth.')
inst('DRV-M1-PL',(45,211,32.5),group='drive')
adds,cuts=ring(16,6,28)
cuts += [box([1,28,14],[0,0,3]),cyl(2.75,34,(-17,7,10),(1,0,0)),cyl(2.75,34,(-17,21,10),(1,0,0))]
part('DRV-CPL12','Split clamp coupling 12-12','Steel',adds,cuts,status='CLAMP_TORQUE_HOLD',notes='2xM5 clamp bolts; friction capacity and motor flat-specific jaw require proof. Not an approved torque limiter.')
inst('DRV-CPL12',(80,221,65),group='drive')
part('DRV-IN-SHAFT','Common input shaft 12x157','C45',[cyl(6,157)], [box([4,115,2],[-2,20,4])],notes='Bearing journals 12 k6; keyed regions 12 h6. 4 mm key width; retaining collar details in RFQ.')
inst('DRV-IN-SHAFT',(80,237,65),group='drive')
part('DRV-JACK','Output jackshaft 20x168','C45',[cyl(10,168)],[box([6,92,3.5],[-3,26,6.5])],notes='20 k6 bearing seats; 6 mm keyway outside bearing seats. Shoulder/retention specification needs final tolerance audit.')
inst('DRV-JACK',(80+gearc,240,65),group='drive')
# Standard bearings represented by exact boundary solids, not detailed balls/cages.
for code,bore,od,t,source in [('6205',25,52,15,'NSK6205'),('6001',12,28,8,'NSK6001'),('6204',20,47,14,'NSK6204'),('51102',15,28,9,'NSK51102'),('6202',15,35,11,'RFQ'),('6007',35,62,14,'RFQ'),('625',5,16,5,'RFQ')]:
 a,b=ring(od/2,bore/2,t)
 part('BR-'+code,code+' bearing boundary','Bearing steel',a,b,source,'DATASHEET_BOUNDARY' if source!='RFQ' else 'STANDARD_SIZE_VERIFY_MPN','Seal, clearance class and exact suffix must be selected. Bearing envelope is not solid steel in mass estimates.',False)
for y in [253,360]: inst('BR-6001',(80,y,65),group='drive')
for y in [254,388]: inst('BR-6204',(80+gearc,y,65),group='drive')
plate('DRV-BFRONT','Common front bearing plate',140,80,18,[(35,40,14),(35+gearc,40,23.5)]+[(x,z,3.3) for x in [8,132] for z in [8,72]],notes='Two independent bores at56.9402 centres,28 H7 and47 H7. Combined plate avoids overlapping separate housings.')
inst('DRV-BFRONT',(45,250,25),group='drive')
plate('DRV-B12','Input rear bearing plate',34,60,12,[(17,30,14),(8,7,2.75),(26,7,2.75),(8,53,2.75),(26,53,2.75)],notes='28 H7; 34 mm local width clears adjacent output sprocket. Attachment/rib stiffness DFM hold.')
inst('DRV-B12',(63,358,35),group='drive')
plate('DRV-B20','Output rear bearing plate',70,75,18,[(35,37.5,23.5)]+[(x,z,3.3) for x in [9,61] for z in [9,66]],notes='47 H7; metal support with bearing retainers required.')
inst('DRV-B20',(80+gearc-35,386,27.5),group='drive')
# COTS helical gear reference is OD/hub/bore and axial face stack, not printable teeth.
for z,bore,hub in [(15,12,24),(40,20,60)]:
 rp=2*z/2/math.cos(math.radians(15)); ro=rp+2
 for hand in ['R','L']:
  a=[cyl(ro,25),cyl(hub/2,10,(0,25,0))];c=[cyl(bore/2,37,(0,-1,0))]
  part(f'DRV-SH{z}{hand}',f'KHK SH2-{z}{hand}H reference','S45C hardened',a,c,'KHK_SH','COTS_REFERENCE_SECONDARY_BORE_HOLD','Purchased hardened teeth. 25 face + 10 hub. Do not machine teeth from this OD model. 40T bore modified 18 to20.',False)
# Lower half face toward center; upper half face adjacent across 2 mm gap.
for z,xx in [(15,80),(40,80+gearc)]:
 inst(f'DRV-SH{z}R',(xx,311,65),[1,0,0,180],group='drive')
 inst(f'DRV-SH{z}L',(xx,313,65),group='drive')
# Chain sprocket reference with roller-root scallops (no tooth rating asserted).
for z,bore in [(24,20),(24,12),(12,12),(24,25)]:
 rp=9.525/(2*math.sin(math.pi/z));ro=9.525*(.6+1/math.tan(math.pi/z))/2
 a=[cyl(ro,8),cyl(min(rp*.7,20),10,(0,8,0))]
 c=[cyl(bore/2,20,(0,-1,0))]
 for ang in np.linspace(0,2*math.pi,z,endpoint=False):c.append(cyl(2.54,10,(rp*math.cos(ang),-1,rp*math.sin(ang))))
 part(f'DRV-SP{z}-B{bore}',f'ANSI35 {z}T sprocket bore{bore}','Steel',a,c,'RFQ','CHAIN_TOOTH_PROFILE_AND_LOAD_HOLD','9.525 pitch. Roller pocket reference only; exact manufacturer tooth form, width and working load must replace this model.',False)
for pid,at in [('DRV-SP24-B20',(80+gearc,354,65)),('DRV-SP24-B25',(130,354,Z1)),('DRV-SP24-B12',(80,374,65)),('DRV-SP12-B12',(X2,374,280))]:inst(pid,at,group='drive')

# S1 cutters, staggered spacers, shafts and drilled support plates.
for hand in ['A','B']:
 pts=hooks(direction=1 if hand=='A' else -1)
 a=[poly(pts,6.)]; c=[cyl(12.5,8,(0,-1,0)),box([8,8,3.3],[-4,-1,12.0])]
 part('S1-CUT-'+hand,'S1 7-hook cutter '+hand,'Tool steel, heat treatment RFQ',a,c,notes='Final thickness 6.00 +/-0.02; bore25 H7; key8 Js9. Cut blank then heat-treat/grind, edge hardening not a laser-as-cut assumption.')
 a,b=ring(18,12.5,6.4)
 part('S1-SPACER-'+hand,'S1 spacer '+hand,'Ground C45',a,b,notes='6.40 +/-0.02 thickness; stack sorted and shimmed. No bearings on these spacers.')
 x=130 if hand=='A' else 190
 offset=0 if hand=='A' else 6.2
 for j in range(13):
  y=163+offset+12.4*j
  # Clock the teeth in the blank, NOT the keyed bore relative to the shaft.
  from copy import deepcopy
  pid=f'S1-CUT-{hand}-P{j:02d}'
  spec=deepcopy(PARTS['S1-CUT-'+hand]);spec['id']=pid
  phase=j*2*math.pi/(7*13)
  spec['adds'][0]['points']=[[u*math.cos(phase)-v*math.sin(phase),u*math.sin(phase)+v*math.cos(phase)] for u,v in spec['adds'][0]['points']]
  spec['name']=f'S1 cutter {hand} tooth phase {j} / common key datum'
  spec['notes']+=f' Tooth phase {math.degrees(phase):.6f} deg; KEY REMAINS ZERO. Mark part phase before grinding.'
  PARTS[pid]=spec
  inst(pid,(x,y,Z1),group='S1')
  if j<12:inst('S1-SPACER-'+hand,(x,y+6,Z1),group='S1')
 L=282 if hand=='A' else 250
 part('S1-SHAFT-'+hand,f'S1 shaft {hand} 25x{L}','C45 or SCM440 certified',[cyl(12.5,L)],[box([8,163,4],[-4,63,8.5]),box([8,30,4],[-4,8,8.5])],notes='25 k6 at y40..55 and231..246; cutter/key lands25 h6. Keyways must not cross journals. Retention collars required; step/fillet audit pending.')
 inst('S1-SHAFT-'+hand,(x,100,Z1),group='S1')
 for y in [140,331]:inst('BR-6205',(x,y,Z1),group='S1')
# KHK SS2-30HJ25 permitted J bore range; an actual involute reference profile is included.
a=[poly(gear_section(2,30),20),cyl(25,10,(0,20,0))]
c=[cyl(12.5,32,(0,-1,0)),box([8,32,3.3],[-4,-1,12])]
part('S1-SYNC','KHK SS2-30HJ25 reference','S45C hardened',a,c,'KHK_SS','COTS_TOOTH_REFERENCE','Pitch60 OD64; face20 hub10. Involute reference has simplified root. Purchase manufacturer gear, do not cut from this model.',False)
inst('S1-SYNC',(130,108,Z1),group='S1')
inst('S1-SYNC',(190,108,Z1),[0,1,0,6],group='S1')
plate('S1-BPL','S1 bearing carrier',160,100,18,[(50,50,26),(110,50,26)]+[(x,z,3.3) for x in [10,150] for z in [10,90]],notes='Two 52 H7 seats at60.00 +/-0.02 centres. Line bore assembled metal carriers. Datums A face, B base, C left edge.')
for y in [138,331]:inst('S1-BPL',(80,y,Z1-50),group='S1')
plate('S1-WALL','S1 metal end liner',160,92,5,[(50,46,13),(110,46,13)]+[(x,z,3.3) for x in [10,150] for z in [10,82]],material='S355 wear liner',notes='Wear liner shaft opening26; not bearing seat. Ground/shimmed cutter end gap0.60 nominal.')
for y in [157.4,324.6]:inst('S1-WALL',(80,y,Z1-46),group='S1')
part('S1-SIDE','S1 side containment strip','3mm steel',[box([3,162.2,92])],notes='Two steel side liners. Upper inlet and lower outlet intentionally open inside interlocked enclosure.')
for x in [80,237]:inst('S1-SIDE',(x,162.4,Z1-46),group='S1')
# Common two-bearing retainer avoids overlapping individual caps at60mm centres.
plate('S1-BR-CAP','Two-bearing retainer',160,100,3,[(50,50,23.5),(110,50,23.5)]+[(x,z,3.3) for x in [10,150] for z in [10,90]],notes='47 mm inner abutment per NSK6205; four M6 through bolts share carrier pattern. No overlapping round caps.')
for y in [135,349]:inst('S1-BR-CAP',(80,y,Z1-50),group='S1')

# S2 ring guide with actual cycloidal constraint, eccentric sleeve and assembleable shaft.
outline=cycloid_profile(R=S2['pin_ring_R_mm'],e=7,clearance=.2,samples=S2['guide_samples'])
a=[poly(outline,10)];c=[cyl(23,12,(0,-1,0))]
for a0 in np.linspace(0,2*math.pi,8,endpoint=False):c.append(cyl(2.75,12,(35*math.cos(a0),-1,35*math.sin(a0))))
part('S2-GUIDE','8-lobe cycloidal guide, 9 fixed pins','C45 surface treatment RFQ',a,c,notes='Rpin72 / e7 / rollerR8; analytic offset allowance0.20. 8x5.5 onPCD70. Profile generated from analytic equations; contact fatigue/backlash NOT qualified.')
inst('S2-GUIDE',(X2+7,310,280),group='S2')
# Profiled cutter integral centre body with two real bearing counterbores.
a=[poly(hooks(55,43,8,24),40,at=(0,255,0)),cyl(43,15,(0,240,0)),cyl(43,15,(0,295,0))]
c=[cyl(23,72,(0,239,0)),cyl(31,14,(0,240,0)),cyl(31,14,(0,296,0))]
for a0 in np.linspace(0,2*math.pi,8,endpoint=False):c.append(cyl(2.1,15,(35*math.cos(a0),295,35*math.sin(a0))))
part('S2-ROTOR','S2 8-hook rotor110, bearing cartridge','C45 / wear inserts RFQ',a,c,notes='Active40; total70; 2x62 H7 counterbores14 deep; minimum wall and heat treatment DFM needed. Inserts vs monolithic material not yet closed.')
inst('S2-ROTOR',(X2+7,0,280),group='S2')
for y in [240,296]:inst('BR-6007',(X2+7,y,280),group='S2')
a=[cyl(17.5,80,(7,0,0))];c=[cyl(6,82,(0,-1,0)),box([4,82,2],[-2,-1,4])]
part('S2-ECC','Eccentric sleeve35 / bore12 / e7','C45',a,c,notes='Outside35 k6, bore12 H7, eccentricity7.00 +/-0.01; minimum geometric wall4.5. Separate sleeve permits bearing/rotor assembly; torque, key and fatigue validation pending.')
inst('S2-ECC',(X2,240,280),group='S2')
part('S2-SHAFT','S2 drive shaft12x189','C45',[cyl(6,189)],[box([4,80,2],[-2,35,4])],notes='Drive is one centred shaft plus removable eccentric sleeve, not an unassembleable integral crank. 12 k6 bearing seats.')
inst('S2-SHAFT',(X2,205,280),group='S2')
for y in [223,335]:inst('BR-6001',(X2,y,280),group='S2')
part('S2-SUP','S2 chamfered main shaft support','C45',[poly([[0,0],[178,0],[178,178],[70,178],[0,108]],18)], [cyl(14,20,(89,-1,89))]+[cyl(3.3,20,(x,-1,z)) for x,z in [(12,12),(166,12),(166,166),(80,166)]],notes='28 H7 main bearing seat. Upper-left70mm chamfer clears S1 carrier; add metal rail support before load release.')
for y in [221,333]:inst('S2-SUP',(X2-89,y,191),group='S2')
for pid,t,y in [('S2-PIN-F',6,300),('S2-PIN-R',6,325)]:
 a=[cyl(89,t)];c=[cyl(60,t+2,(0,-1,0))]
 for phi in np.linspace(0,2*math.pi,9,endpoint=False): c.append(cyl(2.5,t+2,(72*math.cos(phi),-1,72*math.sin(phi))))
 part(pid,'Fixed pin ring '+pid[-1],'C45',a,c,notes='9x5 H7 holes onPCD144; 40deg pitch. Select precision shoulder pins, not threaded bolt shanks. Plate stays fixed.')
 inst(pid,(X2,y,280),group='S2')
part('S2-PIN','Precision roller pin5x31','Bearing steel',[cyl(2.5,31)],notes='Supported at both ends by fixed ring plates. Axial retaining hardware not yet released.')
for phi in np.linspace(0,2*math.pi,9,endpoint=False):
 x=X2+72*math.cos(phi);z=280+72*math.sin(phi)
 inst('S2-PIN',(x,300,z),group='S2')
 for y in [310,315]:inst('BR-625',(x,y,z),group='S2')
# Two separate bent steel shell arcs, rather than a misleading disconnected solid.
for suffix,startdeg,enddeg in [('L',160,220),('R',320,440)]:
 pts=[[65.8*math.cos(math.radians(a)),65.8*math.sin(math.radians(a))] for a in np.linspace(startdeg,enddeg,121)]+[[62.8*math.cos(math.radians(a)),62.8*math.sin(math.radians(a))] for a in np.linspace(enddeg,startdeg,121)]
 part('S2-CASE-'+suffix,'S2 steel shell arc '+suffix,'3mm steel',[poly(pts,40)],notes='ID125.6 wall3. Two discrete shell arcs leave feed80deg and screen100deg. Flanges/fasteners must be finalised.')
 inst('S2-CASE-'+suffix,(X2,255,280),group='S2')
sect=[[64.8*math.cos(math.radians(a)),64.8*math.sin(math.radians(a))] for a in np.linspace(220,320,101)]+[[62.8*math.cos(math.radians(a)),62.8*math.sin(math.radians(a))] for a in np.linspace(320,220,101)]
a=[poly(sect,40)];b=[]
for theta in np.linspace(228,312,13):
 th=math.radians(theta);v=(math.cos(th),0,math.sin(th))
 for y in [5,11,17,23,29,35]:b.append(cyl(2,6,(60.8*v[0],y,60.8*v[2]),v))
part('S2-SCREEN','Curved screen4mm x78 holes','2mm steel',a,b,notes='4 mm round holes, pitch6 axial. Bent radius inner62.8. Hole size is not a guaranteed maximum particle length. Flat DXF generated separately.')
inst('S2-SCREEN',(X2,255,280),group='S2')

# Buffer CAD is a true hollow frustum. Lower discharge throat and material-specific drying are held.
def rectloop(w,d,z):return [[-w/2,-d/2,z],[w/2,-d/2,z],[w/2,d/2,z],[-w/2,d/2,z]]
bottom=rectloop(50,40,0);top=rectloop(190,48,73)
ib=rectloop(44,34,-1);it=rectloop(184,42,74)
# Offset throat to extruder feed atX289; upper buffer remains under screen.
for loop in [bottom,ib]:
 for pt in loop:pt[0]+=289-X2
part('FEED-BUF','Buffer190x48 top /50x40 throat /height73','PC outer shell plus metal throat',[{'kind':'loft','loops':[bottom,top]}],[{'kind':'loft','loops':[ib,it]}],notes='Internal geometric volume calculated; usable75pct separately stated. Top fits between Y251..299, ahead of pin rings. Cold throat offset to barrel feed X289.')
inst('FEED-BUF',(X2,275,145),group='feed')
# Screw: genuine helical flight swept about local Z plus a tapered root, rotated Z to X at instance.
a=[cone(5,5,96,axis=(0,0,1)),cone(5,6.5,80,(0,0,96),(0,0,1)),cyl(6.5,80,(0,0,176),(0,0,1)),{'kind':'screw_flight','pitch':16,'height':256,'outer_r':8,'root_r':4.9,'thickness':2}]
part('EX-SCREW','16mm x256mm compression screw','SCM440 QT/nitriding RFQ',a,notes='Pitch16, flight2, root10 feed /13 meter, L/D16. CAD flight has square flanks; fillets/tip geometry/finish and nitriding supplier confirmation required.')
inst('EX-SCREW',(274,275,125),[0,1,0,90],group='extruder')
# Barrel, feed opening, discrete heater seats and die interface.
a=[cyl(15,256,axis=(1,0,0))];c=[cyl(8.15,258,(-1,0,0),(1,0,0)),cyl(10,22,(25,0,0),(0,0,1))]
part('EX-BARREL','Barrel16.3ID x30OD x256','SCM440 nitrided RFQ',a,c,notes='Radial cold clearance0.15. Honing, straightness, hot fit, feed hole and die pressure sealing require supplier approval.')
inst('EX-BARREL',(274,275,125),group='extruder')
# Actual stepped rear shaft, independent thrust bearing and retaining cartridge.
a=[cyl(7.5,61,axis=(1,0,0)),cyl(13,6,(45,0,0),(1,0,0))]
part('EX-REAR','Extruder rear/thrust shaft15','SCM440',a,notes='x213..274 inassembly; collar258..264. No thrust transmitted to M2 bearings; shaft-screw connection detail is manufacturing HOLD.')
inst('EX-REAR',(213,275,125),group='extruder')
a,b=ring(16,6,16,axis=(1,0,0));a += [cyl(16,16,(16,0,0),(1,0,0))]; b +=[cyl(7.5,18,(15,0,0),(1,0,0))]
part('EX-CPL','12-to15 split coupling32 long','Steel',a,b,status='CLAMP_TORQUE_HOLD',notes='D-shaft jaw and clamping proof pending, no axial load transfer intent.')
inst('EX-CPL',(197,275,125),group='extruder')
inst('BR-6202',(235,275,125),[0,0,1,-90],group='extruder')
inst('BR-51102',(249,275,125),[0,0,1,-90],group='extruder')
a=[box([39,60,70])];c=[cyl(7.8,41,(-1,30,35),(1,0,0)),cyl(17.5,11,(3,30,35),(1,0,0)),cyl(14,9,(17,30,35),(1,0,0)),cyl(13.3,9,(26,30,35),(1,0,0))]
c.append(box([13,60,20],[26,0,50]))
part('EX-THRUST','Metal thrust carrier39x60x70','C45',a,c,notes='6202 and51102 distinct radial/thrust functions. Split lid, positive stops and end access need assembly DFM; digital solid only.')
inst('EX-THRUST',(232,245,90),group='extruder')
a=[cyl(18,20,axis=(1,0,0))];c=[cone(8.15,1,16,(-1,0,0),(1,0,0)),cyl(1,22,(-1,0,0),(1,0,0)),cyl(3,38,(12,-19,8),(0,1,0))]
part('EX-DIE','Die36OD x20 with2mm exit','SCM440 or stainless RFQ',a,c,notes='2mm die exit is a drawdown candidate for1.75 filament, not final calibration. Heater bore6x38; pressure attachment not yet detailed.')
inst('EX-DIE',(530,275,125),group='extruder')
a,b=ring(20,15,40,axis=(1,0,0))
part('EX-H100','24V100W band heater30ID x40','Purchased custom',a,b,'RFQ','HEATER_QUOTE_AND_DRAWING_HOLD','3units100W; power density100/(pi*3cm*4cm)=2.65W/cm2. Lead/clamp bulge not invented.',False)
for x in [338,398,458]:inst('EX-H100',(x,275,125),group='extruder')
part('EX-H60','24V60W cartridge6x20','Purchased custom',[cyl(3,20)],source='RFQ',status='HEATER_QUOTE_AND_DRAWING_HOLD',notes='Rated60W is requirement, not a verified off-the-shelf product.',drawing=False)
inst('EX-H60',(542,256,133),group='extruder')
# Cooling trough and two actual fan housings.
part('COOL-TRAY','Air cooling trough275x80','Sheet metal',[box([275,80,2]),box([275,2,28],[0,0,2]),box([275,2,28],[0,78,2])],notes='275mm working length. Filament path125Z; thermal model determines throughput; fans require a measured duct curve.')
inst('COOL-TRAY',(555,235,103),group='cooling')
a=[box([80,38,80])];c=[cyl(35,40,(40,-1,40))]
for x in [4.25,75.75]:
 for z in [4.25,75.75]:c.append(cyl(2.25,40,(x,-1,z)))
part('COOL-FAN','Sanyo9RA0824H1001','Purchased',a,c,'FAN','DATASHEET_BODY_HOLE_PATTERN_VERIFY','80x80x38,24V0.33A7.92W; mounting pattern must use final manufacturer drawing. Tach, no PWM pin.',False)
for x in [570,710]:inst('COOL-FAN',(x,187,85),group='cooling')
# Spool and puller are dimensioned interfaces, not falsely detailed purchased motors.
a,b=ring(100,26,2,axis=(1,0,0));a += [cyl(27,66,(2,0,0),(1,0,0)),cyl(100,2,(68,0,0),(1,0,0))];b +=[cyl(26,70,(1,0,0),(1,0,0))]
part('SPOOL-ENV','200mm x70 spool reference','User spool reference',a,b,source='RFQ',status='SPOOL_INTERFACE_ONLY',notes='Side-removable, support shaft/bracket/traverse and powered tensioning remain unqualified.',drawing=False)
inst('SPOOL-ENV',(640,105,245),group='spool')
for pid in ['PULL-ROLLER']:
 a,b=ring(10,2.5,22)
 part(pid,'Puller roller20x22','TPU tread / metal hub',a,b,notes='2 rollers,one compliant preload. Drive motor/tach and spring stack not yet manufacturing released.')
for z in [114.1,135.9]:inst('PULL-ROLLER',(839,264,z),group='puller')
# Hopper panels: true tapered shell with inclined centreline35deg.
zbot=Z1+46.2; ztop=500; run=(ztop-zbot)/math.tan(math.radians(35))
loops=[[[83,162.4,zbot],[237,162.4,zbot],[237,324.6,zbot],[83,324.6,zbot]],[[170-run-90,175,ztop],[170-run+90,175,ztop],[170-run+90,315,ztop],[170-run-90,315,ztop]]]
inloops=[[[86,165.4,zbot-1],[234,165.4,zbot-1],[234,322.8,zbot-1],[86,322.8,zbot-1]],[[173-run-90,178,ztop+1],[167-run+90,178,ztop+1],[167-run+90,312,ztop+1],[173-run-90,312,ztop+1]]]
part('HOPPER','35deg batch hopper','PC shell + steel lower liner',[{'kind':'loft','loops':loops}],[{'kind':'loft','loops':inloops}],notes='Whole hopper exceeds print limit; must split into <=210mm panels before printing. Closed lid and standstill interlock mandatory; angle is not an access safety measure.')
inst('HOPPER',group='feed')
part('HOP-LID','Interlocked lid180x140','PC with metal strike',[box([180,140,5])],notes='Hinge/guard lock hardware not chosen. NO open-lid operation.')
inst('HOP-LID',(170-run-90,175,500),group='feed')

for item in INST:
 if item['group'] in ['extruder','cooling','puller']: item['at'][0]-=10

# Non-CAD procurement requirements are separate from geometrically modelled parts.
EXTRA=[
 ['EL-DRV','Pololu2995 M1 driver option',1,'DRIVER','OPTION_NOT_PURCHASED','Configurable current limit; board21A is not terminal43A. Existing BTS7960 requires qualification.'],
 ['EL-TC','Adafruit3263 MAX31856',4,'TC','PURCHASE_CANDIDATE','Four independent temperature inputs; K probes exact mechanical model unresolved.'],
 ['SAFE-STOP','Existing E-stop',1,'HANDOVER','OWNED_RATING_VERIFY','Independent hard cut with contactor; contact configuration verify.'],
 ['CTRL-MEGA','Arduino Mega',1,'HANDOVER','OWNED','Reference power allocator is NOT deployable heater firmware.'],
 ['EL-BTS','Existing BTS7960 modules',2,'HANDOVER','OWNED_UNQUALIFIED','Do not assume advertised43A continuous.'],
 ['SAFE-LOCK','Coded/positive-opening guard lock',2,'RFQ','SAFETY_SELECTION_HOLD','Lid and service access, standstill unlock, manual reset.'],
 ['SAFE-CONTACT','24V coil DC rated contactor',1,'RFQ','SAFETY_SELECTION_HOLD','Continuous>=35A DC and fault-current breaking coordinated with fuse.'],
 ['SAFE-FUSE','Branch and mains fuses / holders',1,'RFQ','CIRCUIT_DESIGN_HOLD','Select from actual cable ampacity, DC breaking and inrush. No guessed fuse order.'],
 ['SAFE-THERM','Independent thermal cutoff chain',1,'RFQ','SAFETY_SELECTION_HOLD','Normally closed manual-reset overtemp plus one-shot protection.'],
 ['SAFE-BRAKE','Bus overvoltage/braking protection',1,'RFQ','REGEN_DESIGN_HOLD','PSU sink ability unknown; no regeneration assumption.'],
 ['DRV-TLIMIT','Mechanical torque limiter',1,'RFQ','TORQUE_LIMITER_HOLD','Shared M1 input; calibration before blade operation.'],
 ['CHAIN-A','ANSI35 chain94 pitches',1,'RFQ','CHAIN_RATING_HOLD','Pitch length895.35mm. Working load and width to confirm.'],
 ['CHAIN-B','ANSI35 chain84 pitches',1,'RFQ','CHAIN_RATING_HOLD','Pitch length800.10mm. Working load and width to confirm.'],
 ['FASTENERS','Brackets, metal supports,keys,shims,retainers',1,'RFQ','HARDWARE_SCHEDULE_HOLD','Not an orderable quantity list; full mechanical fastener closure is outstanding.'],
 ['FEED-CHUTE','Metal lined transfer chute',1,'DESIGN','TRANSFER_PATH_HOLD','Complete swept envelope/bridging check and split-print panels before release.'],
 ['GUARDS','Steel cutter containment / chain guards / heat shield',1,'DESIGN','SAFETY_GEOMETRY_HOLD','Do not operate the open review assembly. Guard geometry still to be detailed.'],
 ['AUX-DRIVES','Puller,spool,traverse actuation',1,'RFQ','AUX_ACTUATION_HOLD','Separate low-power controls, no large third shredder motor.']]

def write_all():
 from supports import add
 add(globals())
 PARTS["EX-SCREW"]["adds"][3]["segments_per_turn"]=64
 for sub in ['design','bom','sources']: (ROOT/sub).mkdir(exist_ok=True)
 (ROOT/'design/parameters.json').write_text(json.dumps(PARAMS,indent=2),encoding='utf-8')
 (ROOT/'design/assembly.json').write_text(json.dumps({'parts':PARTS,'instances':INST},separators=(',',':')),encoding='utf-8')
 (ROOT/'sources/register.json').write_text(json.dumps(SOURCES,indent=2),encoding='utf-8')
 with (ROOT/'bom/profile_cut_plan.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(cut[0]),lineterminator='\n');w.writeheader();w.writerows(cut)
 rows=[]
 for pid,p in PARTS.items():
  q=sum(i['part']==pid for i in INST)
  if q: rows.append([pid,p['name'],q,p['material'],p['status'],p['source'],p['notes']])
 for pid,n,q,src,st,note in EXTRA: rows.append([pid,n,q,'Procurement requirement',st,SOURCES[src],note])
 with (ROOT/'bom/BOM.csv').open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['part_id','description','quantity','material','status','source','notes']);w.writerows(rows)
 print(json.dumps({'part_types':len(PARTS),'instances':len(INST),'bom_rows':len(rows),'S1_z':Z1,'S2_x':X2,'gear_center':gearc,'A_center':ca,'B_center':cb},indent=2))
if __name__=='__main__':write_all()
