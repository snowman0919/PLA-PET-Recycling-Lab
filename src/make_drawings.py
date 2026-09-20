"""Nominal dimensioned RFQ drawings from the same CSG master; not NC toolpaths."""
from pathlib import Path
import json,math,csv,sys
import numpy as np
from shapely.geometry import Polygon,Point,box as sbox
from shapely.ops import unary_union
import ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];M=json.loads((ROOT/'design/assembly.json').read_text());P=json.loads((ROOT/'design/parameters.json').read_text());E=json.loads((ROOT/'results/engineering.json').read_text());C=json.loads((ROOT/'results/cad_parts.json').read_text());R={x['part_id']:x for x in C['parts']}
OUT=ROOT/'drawings';OUT.mkdir(exist_ok=True)
FONT='Helvetica'
for path in ['/usr/share/fonts/truetype/nanum/NanumGothic.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
 if Path(path).exists():
  try:pdfmetrics.registerFont(TTFont('KR',path));FONT='KR';break
  except Exception:pass

def text(c,x,y,s,size=10):c.setFont(FONT,size);c.drawString(x,y,str(s))
def header(c,title,page,code):
 c.setLineWidth(.7);c.rect(25,25,W-50,H-50)
 text(c,42,H-53,'PPR C1  |  '+title,19)
 text(c,42,H-75,'ENGINEERING REVIEW / RFQ ONLY - NOT RELEASED FOR CUTTING, PURCHASE OR ENERGIZATION',10)
 c.line(25,62,W-25,62)
 text(c,40,44,'Project PPR | yunhyuk choi | units mm | revision C1 | 2026-09-20',10)
 text(c,W-280,44,f'{code} / sheet {page}',10)

def paragraph(c,x,y,s,width=105,size=10,leading=16):
 import textwrap
 for ln in str(s).split('\n'):
  for l in textwrap.wrap(ln,width=width) or ['']:
   text(c,x,y,l,size);y-=leading
 return y

def shape2(s,y):
 k=s['kind'];at=s.get('at',[0,0,0])
 if k=='box':
  a,b,d=s['size'];return sbox(at[0],at[2],at[0]+a,at[2]+d) if at[1]-1e-7<=y<=at[1]+b+1e-7 else None
 if k in ['cylinder','cone'] and s.get('axis',[0,1,0])==[0,1,0]:
  if at[1]-1e-7<=y<=at[1]+s['h']+1e-7:
   r=s['r'] if k=='cylinder' else s['r1']+(s['r2']-s['r1'])*(y-at[1])/s['h']
   return Point(at[0],at[2]).buffer(r,quad_segs=256)
 if k=='polygon' and s.get('plane','XZ')=='XZ' and at[1]-1e-7<=y<=at[1]+s['h']+1e-7:return Polygon([(a+at[0],b+at[2]) for a,b in s['points']])
 return None

def section(pid):
 p=M['parts'][pid];record=R[pid];y=(record['bounds'][1]+record['bounds'][4])/2
 shapes=[q for a in p['adds'] if (q:=shape2(a,y)) is not None]
 if not shapes:return None
 out=unary_union(shapes)
 for a in p['cuts']:
  q=shape2(a,y)
  if q is not None:out=out.difference(q)
 return out

def drawshape(c,geom,x,y,scale):
 polys=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
 for poly in polys:
  for ring in [poly.exterior,*poly.interiors]:
   p=c.beginPath();pts=list(ring.coords);p.moveTo(x+pts[0][0]*scale,y+pts[0][1]*scale)
   for a,b in pts[1:]:p.lineTo(x+a*scale,y+b*scale)
   p.close();c.drawPath(p,stroke=1,fill=0)

def dim(c,x1,y1,x2,y2,label,off=20):
 c.setLineWidth(.5)
 if abs(y1-y2)<1e-8:
  yy=y1+off;c.line(x1,y1,x1,yy+4);c.line(x2,y2,x2,yy+4);c.line(x1,yy,x2,yy)
  for x,sg in [(x1,1),(x2,-1)]:c.line(x,yy,x+sg*5,yy+2);c.line(x,yy,x+sg*5,yy-2)
  c.setFont(FONT,10);c.drawCentredString((x1+x2)/2,yy+5,label)
 else:
  xx=x1+off;c.line(x1,y1,xx+4,y1);c.line(x2,y2,xx+4,y2);c.line(xx,y1,xx,y2)
  for y,sg in [(y1,1),(y2,-1)]:c.line(xx,y,xx+2,y+sg*5);c.line(xx,y,xx-2,y+sg*5)
  text(c,xx+6,(y1+y2)/2,label,10)

def hole_table(c,pid,x,y):
 p=M['parts'][pid];holes=[]
 for a in p['cuts']:
  if a['kind']=='cylinder' and a.get('axis',[0,1,0])==[0,1,0]:holes.append((a['at'][0],a['at'][2],a['r']*2))
 text(c,x,y,'LOCAL X / Z HOLE CENTRES (mm)',11);y-=23
 for n,(a,b,d) in enumerate(holes[:20]):
  text(c,x,y,f'H{n+1:02d}   X {a:8.3f}   Z {b:8.3f}   DIA {d:7.3f}',9);y-=17
 if len(holes)>20:text(c,x,y,f'+ {len(holes)-20} holes; use machine-readable geometry specification.',9);y-=20
 return y

W,H=landscape(A3)

def main():
 # Flat profile DXFs are nominal closed sections, with a review-only note on separate layer.
 selected=['DRV-M1-PL','DRV-BFRONT','DRV-B12','DRV-B20','S1-BPL','S1-WALL','S1-BR-CAP','S2-GUIDE','S2-PIN-F','S2-PIN-R','S2-ECC']+[f'S1-CUT-{h}-P{j:02d}' for h in ['A','B'] for j in range(13)]
 for pid in selected:
  geom=section(pid)
  if geom is None:continue
  doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace();doc.layers.new('CUT');doc.layers.new('INFO')
  polys=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
  for pp in polys:
   for rr in [pp.exterior,*pp.interiors]:ms.add_lwpolyline(list(rr.coords)[:-1],close=True,dxfattribs={'layer':'CUT'})
  ms.add_text(pid+' C1 NOMINAL / RFQ ONLY / NOT NC RELEASE',dxfattribs={'height':3,'layer':'INFO','insert':(geom.bounds[0],geom.bounds[3]+10,0)})
  doc.saveas(OUT/(pid+'.dxf'))
 # Screen flat blank at neutral radius63.8; bending neutral factor is assumed0.5.
 doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace();L=63.8*math.radians(100)
 ms.add_lwpolyline([(0,0),(L,0),(L,40),(0,40)],close=True)
 for angle in np.linspace(228,312,13):
  for yy in [5,11,17,23,29,35]:ms.add_circle((63.8*math.radians(angle-220),yy),2)
 ms.add_text('S2-SCREEN / K=0.5 ASSUMED / BEND R62.8 INSIDE / RFQ ONLY',dxfattribs={'height':3,'insert':(0,48,0)})
 doc.saveas(OUT/'S2-SCREEN_flat.dxf')
 # A3 part-review drawing book.
 c=canvas.Canvas(str(OUT/'PPR_C1_dimensioned_review.pdf'),pagesize=(W,H));c.setTitle('PPR C1 dimensioned engineering review')
 pages=['DRV-M1-PL','DRV-BFRONT','S1-BPL','S1-BR-CAP','S1-CUT-A-P00','S1-CUT-B-P00','S2-GUIDE','S2-ECC','S2-PIN-F','S2-PIN-R']
 for page,pid in enumerate(pages,1):
  p=M['parts'][pid];g=section(pid);header(c,pid+' - '+p['name'],page,pid)
  bounds=g.bounds;w=bounds[2]-bounds[0];h=bounds[3]-bounds[1];sc=min(500/max(w,1),440/max(h,1),3.8)
  xx=70-bounds[0]*sc;yy=190-bounds[1]*sc
  c.setLineWidth(.7);drawshape(c,g,xx,yy,sc)
  dim(c,xx+bounds[0]*sc,yy+bounds[1]*sc,xx+bounds[2]*sc,yy+bounds[1]*sc,f'{w:.3f}',-28)
  dim(c,xx+bounds[0]*sc,yy+bounds[1]*sc,xx+bounds[0]*sc,yy+bounds[3]*sc,f'{h:.3f}',-28)
  text(c,650,H-119,'NOMINAL / LOCAL DATUM',13)
  sz=R[pid]['size_mm'];text(c,650,H-145,f'X {sz[0]:.3f}   Y(thickness) {sz[1]:.3f}   Z {sz[2]:.3f}',11)
  text(c,650,H-168,'Material: '+p['material'],10)
  text(c,650,H-190,'Status: '+p['status'],10)
  yy2=hole_table(c,pid,650,H-225)
  paragraph(c,650,min(yy2-25,300),p['notes'],65,10,16)
  paragraph(c,50,127,'General dimensions are nominal. Explicit fits/ground thickness override default dimensions. No unlisted thread, retention, edge radius, weld, surface treatment or assembly preload is inferred.',165,9,13)
  c.showPage()
 # Shaft and screw longitudinal working dimensions.
 page=len(pages)+1;header(c,'Shaft / screw interface schedule',page,'PPR-C1-SHAFTS')
 yy=H-135
 for title,L,d,landmarks,note in [
  ('S1 MAIN',282,25,[(40,'bearing seat140..155'),(63,'key starts163'),(226,'key ends326'),(231,'rear seat331..346')],'Local Y origin100; all26 cutter keys remain at common zero; axial retention HOLD.'),
  ('S1 SLAVE',250,25,[(40,'bearing'),(63,'cutter key'),(231,'rear bearing')],'Centre distance60.000; cutter total width161.000; axial clearance0.200 nominal.'),
  ('S2 SLEEVE',80,35,[(0,'bore12'),(80,'bearing end')],'Eccentricity7.000 +/-0.010; roller bearing bore35; geometric minimum wall4.500.'),
  ('EXTRUDER SCREW',256,16,[(96,'feed to transition'),(176,'metering starts')],'P16, flight2, roots10 /13, radial barrel clearance0.150; machining/finish/pressure seal HOLD.')]:
  text(c,55,yy,title,13);xx=260;sc=2.2;c.rect(xx,yy-10,L*sc,d*.9);dim(c,xx,yy-10,xx+L*sc,yy-10,f'L {L}',-24)
  for k,label in landmarks:
   c.line(xx+k*sc,yy-10,xx+k*sc,yy+36);text(c,xx+k*sc+3,yy+38,str(k),8)
  text(c,55,yy-56,note,9);yy-=135
 c.showPage()
 header(c,'Cutter phase / screen / fit schedule',page+1,'PPR-C1-INDEX')
 text(c,60,H-130,'CUTTER PHASE TABLE - OUTER TEETH ROTATE, KEY DATUM DOES NOT',13)
 yy=H-160
 for j in range(13):text(c,70,yy,f'P{j:02d}   {j*360/(7*13):9.5f} deg   A x1 / B x1   final thickness6.00 +/-0.02',11);yy-=24
 yy=H-130;text(c,655,yy,'SCREEN BLANK',14);yy-=30
 for line in [f'Neutral-line length {L if False else 63.8*math.radians(100):.3f}', 'Width40.000 / steel thickness2.000','78 holes DIA4.000','13 angular positions x6 axial rows','Inside bend radius62.800','Bend K factor0.5 is an assumption, verify coupon.','', 'S1 bearing bore52 H7 / journal25 k6','S1 cutter bore25 H7 / key8 Js9','S2 sleeve OD35 k6 / eccentricity7 +/-0.01','S2 guide bore46 / 8 holesD5.5 PCD70','Ring pins9xD5 H7 / PCD144 /40deg pitch','', 'Matched axial stacks must be inspected.','Independent +/-0.02 spacers can accumulate','more error than the0.2 nominal blade clearance.']:
  text(c,655,yy,line,10);yy-=23
 c.showPage();c.save()
 # Per-part nominal dimensions for BOM joins.
 with (ROOT/'bom/part_dimensions.csv').open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['part_id','X_mm','Y_mm','Z_mm','solid_count','volume_mm3','status'])
  for pid,p in M['parts'].items():w.writerow([pid,*R[pid]['size_mm'],R[pid]['solids'],R[pid]['volume_mm3'],p['status']])
 print('Drawing PDF pages',page+1,'DXF',len(list(OUT.glob('*.dxf'))))
if __name__=='__main__':main()
