"""Explicit metal mounting load paths added to the C1 sectional cartridge design."""
import math

def add(g):
 part,inst,box,cyl,poly,ring=[g[x] for x in ['part','inst','box','cyl','poly','ring']]
 P=g['PARTS'];I=g['INST'];Z1=g['Z1'];X2=g['X2'];gearc=g['gearc']
 # The spare crossmember supports S2 right feet; keep it below the PSU.
 P['FR-2020-320']=P.pop('FR-2020-280');P['FR-2020-320']['id']='FR-2020-320';P['FR-2020-320']['name']='2020 profile cut320'
 P['FR-2020-320']['adds'][0]['size'][0]=320;P['FR-2020-320']['cuts'][0]['size'][0]=322
 for a in I:
  if a['part']=='FR-2020-280':a['part']='FR-2020-320';a['name']='FR-2020-320_001';a['at']=[395,40,0]
 for row in g['cut']:
  if row['cut_mm']==280:row['cut_mm']=320;row['remaining_mm']-=40
 # Wear liners are relieved around the four accurately-ground metal tie spacers.
 P['S1-WALL']['cuts']=P['S1-WALL']['cuts'][:2]+[cyl(6.2,7,(x,-1,z)) for x in [10,150] for z in [6,86]]
 P['S1-WALL']['notes']+=' FourD12.4 edge-reliefs atX10/150,Z6/86 clear metal tie spacers.'
 a,b=ring(6,3.3,175)
 part('S1-TIE-TUBE','Ground carrier spacer12OD x175','C45',a,b,notes='175.00 +/-0.02; four tubes clamp front/rear carriers into one metal cartridge. Bore6.6; do not substitute printed struts.')
 part('S1-STUD','M6 threaded rod270 nominal','Steel fastener',[cyl(3,270)],status='FASTENER_RATING_VERIFY',notes='4 studs,270mm; thread geometry not modelled. Select proof-load certified rods/nuts.')
 # Upper roof brackets share carrier fasteners; bottom ties close the carrier load loop.
 hf=Z1+40-425
 part('S1-ROOF-F','Front roof bracket30x95x25','10mm steel welded/folded', [box([30,85,10],[0,0,15]),box([30,10,25],[0,85,0])],[cyl(3.3,97,(15,-1,hf)),cyl(3.3,12,(15,10,14),(0,0,1))],notes='Face atY135 against retainer. M6 top hole to existing profile centreY50. Metal roof load path; bend/weld qualification pending.')
 part('S1-ROOF-R','Rear roof bracket30x48x25','10mm steel welded/folded',[box([30,10,25]),box([30,38,10],[0,10,15])],[cyl(3.3,50,(15,-1,hf)),cyl(3.3,12,(15,38,14),(0,0,1))],notes='Face atY352; M6 profile connection atY390. Do not print this bracket.')
 P['S1-ROOF-R']['cuts'].append(box([4,12,5],[26,-1,-1]))
 for x in [90,230]:
  inst('S1-ROOF-F',(x-15,40,425),group='frame_mount')
  inst('S1-ROOF-R',(x-15,352,425),group='frame_mount')
  for z in [Z1-40,Z1+40]:
   inst('S1-TIE-TUBE',(x,156,z),group='S1');inst('S1-STUD',(x,108,z),group='S1')
 # Drive deck rests on the two 2040 crossmembers and the rear side rail.
 part('DRV-DECK','Steel drive deck240x194x5','S355 steel',[box([240,194,5])],[cyl(3.3,7,(x,y,-1),(0,0,1)) for x in [10,220] for y in [20,110,170]],notes='Deck atZ20..25, supported by existing crossmembers. Added4 feet must be included in frame stiffness review.')
 inst('DRV-DECK',(20,210,20),group='frame_mount')
 part('DRV-M1-FOOT','M1 steel mounting foot70x50x19','Steel',[box([70,50,6]),box([70,6,19])],[cyl(3.3,8,(x,-1,14.5)) for x in [7,63]]+[cyl(3.3,8,(x,30,-1),(0,0,1)) for x in [10,60]],notes='Motor plate corner holes to vertical face. Base bolts to drive deck, not to a printed carrier.')
 inst('DRV-M1-FOOT',(45,217,25),group='frame_mount')
 part('DRV-RISER12','Input rear bearing riser34x12x10','Steel',[box([34,12,10])],notes='Bearing bolt pattern must be transferred to deck after slots/profile series confirmed.')
 inst('DRV-RISER12',(63,358,25),group='frame_mount')
 part('DRV-RISER20','Output rear bearing shim70x18x2.5','Steel',[box([70,18,2.5])],notes='2.50 ground shim, full metal bearing support.')
 inst('DRV-RISER20',(80+gearc-35,386,25),group='frame_mount')
 # Four S2 columns, front/back faces directly against the lower support-plate holes.
 for side,footz in [('L',25),('R',20)]:
  height=210-(footz+6)
  adds=[box([50,50,6]),box([30,16,height],[10,17,6])]
  cuts=[cyl(3.3,18,(25,16,203-footz))]+[cyl(3.3,8,(25,y,-1),(0,0,1)) for y in [8,42]]
  part('S2-LEG-'+side,'S2 '+side+' column / metal foot','Steel',adds,cuts,notes=f'Foot bottomZ{footz}; topZ210. Centre mounting holeZ203. L sits on5mm deck, R on2020crossmember. Welded joint and anchors DFM hold.')
  x=X2-77 if side=='L' else X2+77
  for y in [188,334]:inst('S2-LEG-'+side,(x-25,y,footz),group='frame_mount')
 # Extruder thrust stand: side webs + extended top plate also carry M2 motor flange.
 adds=[box([50,60,6],[205,245,25]),box([8,60,51],[205,245,31]),box([8,60,51],[247,245,31]),box([88,60,8],[167,245,82]),box([6,70,22],[173,240,82])]
 # The preceding coordinates are relative to original main; final positions below offset10mm right to preserve actual carrier X222..261.
 adds=[dict(a,at=[a['at'][0]+10,a['at'][1],a['at'][2]]) for a in adds]
 cuts=[cyl(3.3,10,(x,y,81),(0,0,1)) for x in [232,248] for y in [255,295]]
 cuts +=[cyl(3.3,8,(240,y,24),(0,0,1)) for y in [255,295]]
 cuts +=[cyl(3.3,8,(182,y,99.5),(1,0,0)) for y in [247,303]]
 part('EX-STAND','Thrust stand / coaxial motor bridge','Steel',adds,cuts,notes='M2 and thrust carrier share metal stand on deck; no large right-angle gearbox. Top holes4xM6 to carrier. Weld/bolt/pressure proof remains HOLD.')
 inst('EX-STAND',group='frame_mount')
 # Reuse the exact TT face pattern for M2. No supplementary motor is added.
 inst('DRV-M1-PL',(177,310,92.5),[0,0,1,-90],label='DRV_M2_FACE_PLATE',group='frame_mount')
 # Thread pilot holes in thrust-carrier underside, preserving bearing pockets.
 P['EX-THRUST']['cuts'] += [cyl(2.5,10,(x,y,-1),(0,0,1)) for x in [10,26] for y in [10,50]]
 P['DRV-M1-PL']['name']='TT60 common motor face plate'
 P['EX-THRUST']['notes']+=' Four M6 underside pilots atX10/26,Y10/50; mating stand positions232/248,255/295.'
 # Final drive bracket and keyed-interface audit (cuts never cross bearing journals).
 P['DRV-M1-FOOT']['adds'][0]['size'][1]=30
 for q in P['DRV-M1-FOOT']['cuts']:
  if q.get('axis')==[0,0,1]:q['at'][1]=22
 q=P['DRV-BFRONT'];q['adds'][0]['size'][2]=67.5
 q['cuts']=q['cuts'][:2]+[cyl(3.3,20,(x,-1,z)) for x,z in [(8,8),(132,8),(8,60),(115,60)]]+[box([18,20,17.5],[122,-1,50])]
 q['notes']+=' Top92.5Z clears M2 can; upper-right corner relief clears coaxial bridge.'
 # Keyway cuts in female bores include0.5mm overlap inside the circle, not lost seating depth.
 for pid,q in P.items():
  if pid.startswith('S1-CUT-') or pid=='S1-SYNC':
   q['cuts'][1]['size'][2]=3.8
  if pid.startswith('S1-SPACER-'):q['cuts'].append(box([8,8.4,4.3],[-4,-1,11.5]))
 # External parallel-axis helical gears MUST mate opposite hands.
 for it in I:
  if it['part']=='DRV-SH40R':it['part']='DRV-SH40L';it['name']='DRV_SH40L_lower'
  elif it['part']=='DRV-SH40L':it['part']='DRV-SH40R';it['name']='DRV_SH40R_upper'
 for teeth,bore,width,depth in [(15,12,4,2.3),(40,20,6,2.8)]:
  for hand in ['R','L']:
   lower=(teeth==15 and hand=='R') or (teeth==40 and hand=='L')
   top=bore/2+depth
   P[f'DRV-SH{teeth}{hand}']['cuts'].append(box([width,37,depth+.2],[-width/2,-1,-top if lower else bore/2-.2]))
   P[f'DRV-SH{teeth}{hand}']['notes']+=' Opposite-hand mating specified; lower-half key is mirrored before axial flip.'
 P['DRV-IN-SHAFT']['cuts']=[box([4,72,2],[-2,39,4]),box([4,18,2],[-2,137,4])]
 P['DRV-JACK']['cuts']=[box([6,72,3.5],[-3,36,6.5]),box([6,18,3.5],[-3,114,6.5])]
 P['S2-SHAFT']['cuts']=[box([4,80,2],[-2,35,4]),box([4,18,2],[-2,169,4])]
 P['S2-ECC']['cuts'][1]=box([4,82,3.1],[-2,-1,5.2])
 # Slave gear is phased6deg to mesh. Its front shaft key is cut at the same angle.
 pts=[]
 for x,z in [(-4,8.5),(4,8.5),(4,12.5),(-4,12.5)]:
  a=math.radians(-6);pts.append([x*math.cos(a)-z*math.sin(a),x*math.sin(a)+z*math.cos(a)])
 P['S1-SHAFT-B']['cuts'][1]=poly(pts,30,(0,8,0));P['S1-SHAFT-B']['notes']+=' Front gear key6deg; cutter key0deg.'
 P['S1-SHAFT-A']['cuts'].append(box([8,18,4],[-4,254,8.5]))
 for pid,q in P.items():
  if pid.startswith('DRV-SP'):
   bore=int(pid.split('B')[-1]);w,h,depth={12:(4,4,2.3),20:(6,6,2.8),25:(8,7,3.3)}[bore]
   q['cuts'].append(box([w,20,depth+.8],[-w/2,-1,bore/2-.8]))
 # Explicit key stock makes the shaft/bore assembly auditable in the CAD model.
 keydata=[('KEY-8-154',8,7,154,8.5),('KEY-8-25',8,7,25,8.5),('KEY-8-16',8,7,16,8.5),('KEY-4-70',4,4,70,4),('KEY-4-78',4,4,78,4),('KEY-4-16',4,4,16,4),('KEY-6-70',6,6,70,6.5),('KEY-6-16',6,6,16,6.5)]
 for pid,w,h,L,z in keydata:part(pid,f'Parallel key{w}x{h}x{L}','C45 ground key stock',[box([w,L,h],[-w/2,0,z])],notes='Nominal key blank; stock/female-key fit and deburring to drawing review. No printed keys.')
 inst('KEY-8-154',(130,163.4,Z1),group='S1');inst('KEY-8-154',(190,169.6,Z1),group='S1')
 inst('KEY-8-25',(130,110,Z1),group='S1');inst('KEY-8-25',(190,110,Z1),[0,1,0,6],group='S1')
 inst('KEY-8-16',(130,355,Z1),group='S1')
 inst('KEY-4-70',(80,277,65),group='drive');inst('KEY-4-16',(80,375,65),group='drive')
 inst('KEY-6-70',(80+gearc,277,65),group='drive');inst('KEY-6-16',(80+gearc,355,65),group='drive')
 inst('KEY-4-78',(X2,241,280),group='S2');inst('KEY-4-16',(X2,375,280),group='S2')
