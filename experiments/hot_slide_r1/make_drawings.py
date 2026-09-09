"""Vector review drawings from the actual STEP edge geometry."""
from pathlib import Path
import html,json,hashlib
import FreeCAD as App,Part
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'drawings';OUT.mkdir(exist_ok=True)
def projection(shape,axes,x,y,w,h):
    curves=[]
    for edge in shape.Edges:
        points=edge.discretize(Deflection=.05)
        curves.append([(getattr(p,axes[0]),getattr(p,axes[1])) for p in points])
    points=[p for row in curves for p in row]
    lo=[min(p[a] for p in points) for a in (0,1)];hi=[max(p[a] for p in points) for a in (0,1)]
    scale=min(w/max(hi[0]-lo[0],1),h/max(hi[1]-lo[1],1))
    dx=x+(w-(hi[0]-lo[0])*scale)/2;dy=y+(h-(hi[1]-lo[1])*scale)/2
    return ''.join('<polyline points="'+' '.join(f'{dx+(a-lo[0])*scale:.3f},{dy+(hi[1]-b)*scale:.3f}' for a,b in row)+'" fill="none" stroke="#19364b" stroke-width="0.8"/>' for row in curves)

def page(name,title,shape,lines,axes=('x','y')):
    drawing=projection(shape,axes,35,90,620,430)
    if name=='04-pin':
        profile=[(-2,-3.5),(-2,3.5),(0,3.5),(0,2),(27.4,2),(27.4,1.5),(35.4,1.5),(35.4,-1.5),(27.4,-1.5),(27.4,-2),(0,-2),(0,-3.5),(-2,-3.5)]
        points=' '.join(f'{50+(x+2)*15:.3f},{310-y*15:.3f}' for x,y in profile)
        drawing=f'<polyline points="{points}" fill="none" stroke="#19364b" stroke-width="1.1"/><line x1="35" x2="640" y1="310" y2="310" stroke="#666" stroke-dasharray="6 4"/>'
    notes=''.join(f'<text x="685" y="{110+i*24}" font-size="14">{html.escape(line)}</text>' for i,line in enumerate(lines))
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794"><rect width="1123" height="794" fill="white"/><rect x="15" y="15" width="1093" height="764" fill="none" stroke="#19364b"/><g font-family="Noto Sans CJK KR,sans-serif" fill="#132c40"><text x="35" y="52" font-size="26">{html.escape(title)}</text><text x="35" y="76" font-size="14">HS-R1-S2 | mm | orthographic NTS | PRESSURELESS PROTOTYPE / physical NOT_RUN</text>{drawing}{notes}<text x="35" y="555" font-size="14">Actual STEP edge projection. Free-state spring preload overlaps the mandrel intentionally.</text><text x="35" y="581" font-size="14">STEP and dimensional register jointly control geometry; material/process certificate is a hold point.</text><text x="35" y="749" font-size="14">No pressure, powered rotation, automatic heating or machine installation approval.</text></g></svg>'
    path=OUT/(name+'.svg');path.write_text(svg)
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def main():
    files=[]
    files.append(page('01-flexure','HS-R1-S2 / elastic centring sheet',Part.read(str(ROOT/'fixture/HS-R1-SHEET.step')),['Base ring OD70; lug envelope73.5','Thickness 3.00 +/-0.03','6 sheets per carrier; 12 total','3 shoes R16.860 +/-0.010 free','Web 2.00 +/-0.03','3 radial slots: W4.04 / L8.00','Slot centres R32.50 at90/210/330deg','Matched slot-pin clearance <=0.05','Re-entrant fillets: STEP exact','Final edge polish; no sharp burr','Spring material: certificate required','Heat condition must be specified']))
    files.append(page('02-carrier','HS-R1 / carrier and datum',Part.read(str(ROOT/'fixture/HS-R1-CARRIER.step')),['Local axis X0 / Z50','Width90; height95; plate7','Foot90 x36 x8','Mandrel clearance bore46','3 pin holes4.02 at PCD65','Hole centres: (0,17.5)','(+/-28.1458,66.25) in X/Z','Foot holes6.6 at X+/-32 / Y24','One-piece steel angle reference','Cold alignment by indicator','Match shim; keep spring stack loose'],('x','z')))
    files.append(page('03-fixture','HS-R1 / pressureless test fixture',Part.read(str(ROOT/'fixture/HS-R1-BENCH-REVIEW.step')),['Base100 x270 x10','Carrier datum planes Y0 / Y140','Rod OD33.97-34.00; L220','Solid mandrel, not a pressure vessel','Ends32->34 conical lead over2','End M6 tap: 10 drill / 8 full thread','Stud M6 x70; hand load only','Stop plate faces Y223 / Y229','Washer contact faces Y220 / Y232','Nominal travel limits +/-3mm','Initial test stroke2mm total','6x M6 fixture mount screws required'],('y','z')))
    files.append(page('04-pin','HS-R1 / shouldered pin and stack',Part.read(str(ROOT/'fixture/HS-R1-PIN.step')),['Shoulder diameter4 h6','Shoulder length27.40 +/-0.02','Head7 x2; threaded end M3 x8','6 pins, two locknuts per pin','Carrier thickness7.00 +/-0.03','Six3mm sheets with five0.25 shims','Outer0.25 shims: 2 per pin','Additional0.35 nominal match shim','Cold measured endplay0.25-0.35','Hot measured endplay >=0.10','Nut/washer seats on shoulder','Do not compress the sheet stack'],('z','x')))
    (OUT/'manifest.json').write_text(json.dumps({'status':'PROTOTYPE_REVIEW_DRAWINGS','physical_state':'NOT_RUN','files':files},indent=2))
    print('ACTUAL_GEOMETRY_DRAWINGS_READY',len(files),flush=True)
if __name__=='__main__':main()
