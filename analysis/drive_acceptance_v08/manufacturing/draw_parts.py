"""Produce dimensioned vector sheets from actual CAD, with HLR projections."""
from pathlib import Path
import json,hashlib,math,html,textwrap,csv
import FreeCAD as A
import Part,TechDraw
H=Path(__file__).resolve().parent; R=H.parents[2]
SOURCE=R/'exports/final/drive_ggm_v08'; OUT=SOURCE/'manufacturing_r2'
OUT.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(x,y,s,size=14,weight='normal'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}">{html.escape(str(s))}</text>'
def line(x1,y1,x2,y2): return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="#222" stroke-width="0.8"/>'
def dimh(x0,x1,y,label):
    return line(x0,y,x1,y)+line(x0,y-6,x0,y+6)+line(x1,y-6,x1,y+6)+text((x0+x1)/2-20,y-5,label,13)
def dimv(x,y0,y1,label):
    return line(x,y0,x,y1)+line(x-6,y0,x+6,y0)+line(x-6,y1,x+6,y1)+text(x+7,(y0+y1)/2,label,13)
def matrix_for(axes):
    u=A.Vector(*[int(i==axes[0]) for i in range(3)]);v=A.Vector(*[int(i==axes[1]) for i in range(3)]);w=u.cross(v)
    return A.Matrix(u.x,u.y,u.z,0,v.x,v.y,v.z,0,w.x,w.y,w.z,0,0,0,0,1)
def projection(shape,axes,box,label):
    s=shape.copy();s.transformShape(matrix_for(axes),True);b=s.BoundBox
    x,y,width,height=box; ratio=next(r for r in (2,1,.75,.5,1/3,.25,.2,.1,.05) if b.XLength*r*10/3<width-70 and b.YLength*r*10/3<height-65)
    scale=ratio*10/3; ox=x+30-b.XMin*scale;oy=y+height-30+b.YMin*scale
    groups=TechDraw.project(s,A.Vector(0,0,1));svg=text(x,y+18,label+'  scale '+str(ratio)+':1',13)
    for index in (2,3,0,1):
        g=groups[index]
        if g.isNull():continue
        for edge in g.Edges:
            points=edge.discretize(Number=2 if type(edge.Curve).__name__=='Line' else 48)
            path=' '.join(('M' if n==0 else 'L')+f'{ox+p.x*scale:.3f},{oy-p.y*scale:.3f}' for n,p in enumerate(points))
            dash=' stroke-dasharray="5 3"' if index>=2 else ''
            svg+=f'<path d="{path}" fill="none" stroke="{("#999" if index>=2 else "#111")}" stroke-width="0.8"{dash}/>'
    svg+=dimh(ox+b.XMin*scale,ox+b.XMax*scale,oy-b.YMax*scale-12,f'{b.XLength:.3f}')
    svg+=dimv(ox+b.XMax*scale+12,oy-b.YMax*scale,oy-b.YMin*scale,f'{b.YLength:.3f}')
    return svg,groups

def surfaces(shape):
    rows=[];seen=set();b=shape.BoundBox;mins=(b.XMin,b.YMin,b.ZMin)
    for f in shape.Faces:
        c=f.Surface
        if type(c).__name__!='Cylinder':continue
        a=c.Axis;components=(a.x,a.y,a.z);axis=max(range(3),key=lambda i:abs(components[i]))
        if abs(components[axis])<.999:continue
        u0,u1,v0,v1=f.ParameterRange;u=(u0+u1)/2;v=(v0+v1)/2;p=f.valueAt(u,v)
        radial=p-c.Center-a*((p-c.Center).dot(a));kind='ID' if f.normalAt(u,v).dot(radial)<0 else 'OD'
        q=c.Center;fb=f.BoundBox;low=(fb.XMin,fb.YMin,fb.ZMin);hi=(fb.XMax,fb.YMax,fb.ZMax)
        others=[i for i in range(3) if i!=axis];coords=(q.x,q.y,q.z)
        values=[2*c.Radius,coords[others[0]]-mins[others[0]],coords[others[1]]-mins[others[1]],low[axis]-mins[axis],hi[axis]-mins[axis]]
        key=(kind,axis,*[round(x,4) for x in values])
        if key in seen:continue
        seen.add(key);rows.append({'kind':kind,'axis':'XYZ'[axis],
            'diameter_mm':values[0],'coordinate_axes':''.join('XYZ'[i] for i in others),
            'u_mm':values[1],'v_mm':values[2],'start_mm':values[3],'end_mm':values[4]})
    return sorted(rows,key=lambda r:(r['axis'],r['kind'],r['diameter_mm'],r['u_mm'],r['v_mm']))

def wrap(s,n=38):
    lines=[];current='';width=0
    for word in s.split():
        w=sum(1 if ord(ch)<256 else 1.7 for ch in word)
        if current and width+w+1>n:
            lines.append(current);current='';width=0
        current+=((' ' if current else '')+word);width+=w+1
    return lines+([current] if current else [])

def sheet(entry,shape,features,page_index,feature_slice):
    title=entry['id']+('A'+str(page_index) if page_index else '')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 1400 990"><rect width="1400" height="990" fill="white"/><g fill="#111" font-family="Noto Sans CJK KR, sans-serif">'
    svg+='<rect x="12" y="12" width="1376" height="966" fill="none" stroke="#111"/>'
    svg+=text(30,47,title+'  '+entry['title'],25,'bold')+text(30,75,'GGM-MFG-v0.8-r2 | mm | DIGITAL REVIEW / NOT AUTHORIZED TO FABRICATE',14)
    primary=(0,1) if entry['axis']=='Z' else (0,2)
    sec=(1,2) if entry['axis']=='Z' else (1,2)
    for axes,box,label in [(primary,(35,95,590,390),'PRIMARY'),(sec,(645,95,310,390),'SIDE'),((0,2) if entry['axis']=='Z' else (0,1),(35,495,910,125),'ORTHOGONAL')]:
        image,_=projection(shape,axes,box,label);svg+=image
    svg+=text(990,113,'공정 / 재료 / 검사',18,'bold')+text(990,138,entry['process'],13)
    yy=169
    for note in entry['notes']:
        for line_ in wrap(note,43):svg+=text(990,yy,line_,13);yy+=21
        yy+=9
    if yy>866: raise ValueError('Notes overflow '+entry['id'])
    svg+=text(35,652,'정확한 원통면 좌표: 원점은 해당 부품 bbox 최소점. 축 열이 가공 방향.',14,'bold')
    heads=('ID','형식','축','D mm','좌표축','U mm','V mm','축시작','축끝')
    xx=(35,100,170,220,330,420,540,680,810)
    for x,h in zip(xx,heads):svg+=text(x,679,h,12,'bold')
    for index,row in feature_slice:
        vals=(f'F{index+1:02}',row['kind'],row['axis'],f"{row['diameter_mm']:.3f}",row['coordinate_axes'],f"{row['u_mm']:.3f}",f"{row['v_mm']:.3f}",f"{row['start_mm']:.3f}",f"{row['end_mm']:.3f}")
        for x,val in zip(xx,vals):svg+=text(x,701+20*(index-feature_slice[0][0]),val,12)
    svg+=line(25,883,1375,883)+text(30,908,'수량 '+str(len(entry['objects']))+' | '+', '.join(entry['objects'])[:138],12)
    svg+=text(30,932,'선삭단/보어 치수는 원통면 표, 키홈/탭/용접/공차는 우측 주기 우선. PDF/SVG 선을 CNC 경로로 사용하지 않는다.',12)
    svg+=text(30,954,'원본은 해당 STEP + drawing_manifest.json SHA-256. 실측값을 생성하지 않았으며 본체/통전 승인은 HOLD.',12)
    svg+='</g></svg>'
    target=OUT/(title+'.svg');target.write_text(svg,encoding="utf-8")
    return {'file':target.name,'sha256':sha(target),'drawing':entry['id'],'features':len(feature_slice)}
def main():
    source=SOURCE/'GGM-FULL-ASM.FCStd'; contract=H/'drawing_contract.json'
    bindings={str(p.relative_to(R)):sha(p) for p in (source,contract,Path(__file__).resolve(),SOURCE/'manifest.json')}
    data=json.loads(contract.read_text(encoding="utf-8"));doc=A.openDocument(str(source));pages=[];dimensions=[]
    covered=[]
    for entry in data['parts']:
        obj=doc.getObject(entry['objects'][0]);s=obj.Shape.copy()
        if obj is None or s.isNull() or not s.isValid():raise ValueError('invalid '+entry['id'])
        if entry['id']=='D19':s=s.common(Part.makeBox(80,60,80,A.Vector(280,375,342)))
        feats=surfaces(s)
        for row in feats:dimensions.append({'drawing':entry['id'],'object':entry['objects'][0],**row})
        for start in range(0,max(1,len(feats)),9):
            pages.append(sheet(entry,s,feats,start//9,list(enumerate(feats))[start:start+9]))
        covered.extend(entry['objects'])
        try:
            import importDXF
            ss=s.copy();ss.transformShape(matrix_for((0,1) if entry['axis']=='Z' else (0,2)),True)
            projected=TechDraw.project(ss,A.Vector(0,0,1))
            td=A.newDocument('DXF_'+entry['id']);part=td.addObject('PartDesign::Feature','Projection')
            part.Shape=Part.makeCompound([g for g in projected[:2] if not g.isNull()]);td.recompute()
            dest=OUT/(entry['id']+'.dxf');importDXF.export([part],str(dest));A.closeDocument(td.Name)
            dest.write_text('\n'.join('' if not line.strip() else line for line in dest.read_text().splitlines())+'\n',encoding='utf-8')
        except Exception as exc:raise RuntimeError('DXF failed '+entry['id']) from exc
        print('DRAWN',entry['id'],len(feats),flush=True)
    A.closeDocument(doc.Name)
    if any(sha(R/p)!=h for p,h in bindings.items()):raise RuntimeError('source changed')
    with (OUT/'cylindrical_features.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(dimensions[0]),lineterminator='\n');writer.writeheader();writer.writerows(dimensions)
    report={'status':'DIMENSIONED_DRAWINGS_GENERATED','source_sha256':bindings,'pages':pages,'covered_objects':covered,
            'not_machine_release':True,'physical_measurements':'NOT_RUN','drawing_families':len(data['parts'])}
    (OUT/'drawing_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DRAWINGS_COMPLETE',len(pages),len(covered),flush=True)
main()
