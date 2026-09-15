"""Pre/post rear-relief local plate screen; rigid bolt bores, room-temperature steel."""
from pathlib import Path
import sys,os,json,math,hashlib,zipfile
from collections import Counter,defaultdict
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'analysis/final_validation'))
from run_calculix_v08 import nset,solve
from mesh_quadratic import mesh_step,read_gmsh_inp
RAW=H/'raw/plate_quadratic';RAW.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=RAW/'before.step'
with zipfile.ZipFile(R/'dist/PPR-GGM-DRIVE-REVIEW-20260909-r1.zip') as z:
    old.write_bytes(z.read('PPR-GGM-DRIVE-REVIEW/01_CAD/ThrustPlate-GGM.step'))
new=R/'exports/final/drive_ggm_v08/ThrustPlate-GGM.step'
F=6*math.pi*16.22**2/4
report=[]
for label,source in [('before',old),('r2',new)]:
  for size in (4.0,3.0,2.0):
    work=RAW/(label+'_'+str(size));work.mkdir(exist_ok=True)
    nodes,elements=read_gmsh_inp(mesh_step(source,work,size))
    counts=Counter();face_mids={}
    for e in elements:
        v=list(map(int,e.split(',')))[1:]
        for a,b,c,m,n,k in ((0,1,2,4,5,6),(0,1,3,4,8,7),(0,2,3,6,9,7),(1,2,3,5,9,8)):
            key=tuple(sorted((v[a],v[b],v[c])));counts[key]+=1;face_mids[key]=[v[m],v[n],v[k]]
    w=defaultdict(float)
    for face,count in counts.items():
        if count!=1 or max(abs(nodes[n][1]-398.15) for n in face)>1e-4:continue
        p=[nodes[n] for n in face];cx=sum(q[0] for q in p)/3;cz=sum(q[2] for q in p)/3
        rad=math.hypot(cx-320,cz-382)
        if not 8.5<rad<14.2:continue
        a=[p[1][i]-p[0][i] for i in range(3)];b=[p[2][i]-p[0][i] for i in range(3)]
        area=math.sqrt(sum(q*q for q in (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])))/2
        for n in face_mids[face]:w[n]+=area/3
    assert len(w)>10 and sum(w.values())>300,'bearing load patch missing'
    fixed=[n for n,(x,y,z) in nodes.items() if any(abs(math.hypot(x-bx,z-bz)-3.3)<.03 for bx in (284.5,355.5) for bz in (344.5,419.5))]
    assert len(fixed)>20,'bolt bore support missing'
    total=sum(w.values());deck=['*HEADING','R2 relief local comparison; mm N MPa; rigid bolt bores','*NODE']
    deck += [f'{n},{x:.10g},{y:.10g},{z:.10g}' for n,(x,y,z) in nodes.items()]
    deck += ['*ELEMENT,TYPE=C3D10,ELSET=ALL',*elements,'*SOLID SECTION,ELSET=ALL,MATERIAL=STEEL',
             '*MATERIAL,NAME=STEEL','*ELASTIC','205000,0.29',*nset('FIX',fixed),'*BOUNDARY','FIX,1,3,0',
             '*STEP','*STATIC','0.1,1','*CLOAD']
    deck += [f'{n},2,{F*a/total:.12g}' for n,a in w.items()]
    deck += ['*NODE PRINT,NSET=FIX','RF','*NODE FILE','U,RF','*EL FILE','S','*END STEP','']
    deck_text='\n'.join(deck)
    if '--reuse' in sys.argv and (work/'model.frd').exists():
        from run_calculix_v08 import parse_frd
        assert (work/'model.inp').read_text()==deck_text,'stale input deck'
        assert 'JOB FINISHED' in (work/'ccx.log').read_text().upper()
        data=parse_frd(work/'model.frd');data.update(status='SOLVED',omp_num_threads=1,negative_jacobian=False)
    else: data=solve(work,deck_text)
    # Legacy FRD helper assumes metres/Pa; this deck explicitly uses mm/MPa.
    data['max_displacement_mm']/=1000
    data['max_von_mises_mpa']*=1e6
    data['unit_system']='mm,N,MPa; explicit correction of legacy SI display conversion'
    measured={};mode=False
    for line in (work/'model.dat').read_text().splitlines():
        if 'forces' in line.lower():mode=True;continue
        if mode:
            cols=line.split()
            if len(cols)==4 and cols[0].isdigit() and int(cols[0]) in fixed:
                measured[int(cols[0])]=list(map(float,cols[1:]))
    assert len(measured)==len(fixed),'missing reaction nodes'
    reaction=[sum(v[i] for v in measured.values()) for i in range(3)]
    residual=abs(reaction[1]+F)/F
    assert residual<.01,'reaction imbalance'
    row={'revision':label,'size_mm':size,'load_n':F,'load_patch_mm2':total,'nodes':len(nodes),'elements':len(elements),
         'reaction_n':reaction,'reaction_error':residual,'solver':data,
         'source_sha256':sha(source),'deck_sha256':sha(work/'model.inp'),'frd_sha256':sha(work/'model.frd')}
    report.append(row);print('PLATE_CASE',label,size,json.dumps(data),flush=True)
result={'physical_validation':'NOT_RUN','machine_release':'HOLD','scope':'C3D10 cold elastic comparison; midpoint consistent flat triangular traction; no bolt preload, hot joint, frame or contact validation',
        'force_n':F,'cases':report,'source_sha256':{str(p.relative_to(R)):sha(p) for p in (Path(__file__).resolve(),new,R/'analysis/final_validation/run_calculix_v08.py')}}
(H/'retention_strength_quadratic.json').write_text(json.dumps(result,indent=2)+'\n')
print('PLATE_COMPARISON_COMPLETED',len(report),flush=True)
