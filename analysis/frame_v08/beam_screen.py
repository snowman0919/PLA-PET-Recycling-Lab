"""Conditional 3D Euler-Bernoulli comparison, not assembled-joint qualification."""
import json, hashlib
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/frame_v08/results'
# Conditional comparative screen, not joint/slip or machine qualification.
E=69000.0
G=E/2.6

def stiffness(a,b,area,iy,iz,j,e=E):
 d=b-a; length=np.linalg.norm(d); ex=d/length
 ref=np.array([0.,0.,1.]) if abs(ex[2])<.9 else np.array([0.,1.,0.])
 ey=np.cross(ref,ex); ey/=np.linalg.norm(ey); ez=np.cross(ex,ey)
 rot=np.vstack([ex,ey,ez]); trans=np.zeros((12,12)); k=np.zeros((12,12))
 for i in range(4):trans[3*i:3*i+3,3*i:3*i+3]=rot
 def add(indices,values):k[np.ix_(indices,indices)]+=values
 add([0,6],e*area/length*np.array([[1.,-1.],[-1.,1.]]))
 add([3,9],(e/2.6)*j/length*np.array([[1.,-1.],[-1.,1.]]))
 for indices,inertia,sign in [([1,5,7,11],iz,1),([2,4,8,10],iy,-1)]:
  l=length; s=sign
  values=np.array([[12,s*6*l,-12,s*6*l],[s*6*l,4*l*l,-s*6*l,2*l*l],[-12,-s*6*l,12,-s*6*l],[s*6*l,2*l*l,-s*6*l,4*l*l]])
  add(indices,e*inertia/l**3*values)
 return trans.T@k@trans

def closest(a,u,b,v):
 mat=np.column_stack((u,-v)); t=np.linalg.lstsq(mat,b-a,rcond=None)[0]
 return a+u*t[0],b+v*t[1]

def model(source_rows, torsion_fraction=.1, joint_scale=1.0, tie_scale=1.0):
 rows=[r for r in source_rows if not r['id'].startswith('GGM_SH_Post_')]
 specs={}; points={}
 for r in rows:
  lo=np.array(r['box'][:3]);hi=np.array(r['box'][3:]);ax=r['axis'];mid=(lo+hi)/2
  if 'section_properties' in r:
   mid[1:]=lo[1:]+np.array(r['section_properties']['centroid_yz_mm'])
  a=mid.copy();b=mid.copy();a[ax]=lo[ax];b[ax]=hi[ax]
  specs[r['id']]=(a,b);points[r['id']]=[a,b,(a+b)/2]
 links=[]
 for r in rows:
  a,b=specs[r['id']];u=(b-a)/np.linalg.norm(b-a)
  for c in r['contacts']:
   if c['id'] not in specs or c['id']<=r['id'] or c['gap_mm']>.001:continue
   p,q=specs[c['id']];v=(q-p)/np.linalg.norm(q-p)
   if abs(u@v)>.99:
    pairs=[(x,y) for x in [a,b] for y in [p,q]]
    x,y=min(pairs,key=lambda z:np.linalg.norm(z[1]-z[0]))
   else:x,y=closest(a,u,p,v)
   # Clamp to real span; offset link represents the touching joint envelope.
   x=a+u*np.clip((x-a)@u,0,np.linalg.norm(b-a))
   y=p+v*np.clip((y-p)@v,0,np.linalg.norm(q-p))
   points[r['id']].append(x);points[c['id']].append(y)
   if np.linalg.norm(x-y)>.0001:links.append((x,y))
 coords=[];index={};members=[]
 def node(p):
  key=tuple(np.round(p,6))
  if key not in index:index[key]=len(coords);coords.append(np.array(key))
  return index[key]
 for r in rows:
  a,b=specs[r['id']];ax=r['axis']
  ps=sorted({tuple(np.round(p,6)) for p in points[r['id']]},key=lambda p:p[ax])
  ids=[node(np.array(p)) for p in ps]
  for n,m in zip(ids,ids[1:]):members.append((n,m,r['id'],False))
 for a,b in links:members.append((node(a),node(b),'OFFSET',True))
 xyz=np.array(coords);K=np.zeros((len(xyz)*6,len(xyz)*6))
 by={r['id']:r for r in rows}
 for n,m,name,offset in members:
  if offset:area,iy,iz,j=1000.*joint_scale,1e6*joint_scale,1e6*joint_scale,1e6*joint_scale
  else:
   r=by[name];dims=np.array(r['box'][3:])-np.array(r['box'][:3])
   section=sorted([dims[i] for i in range(3) if i!=r['axis']])
   area,iy,iz=(180.,7200.,7200.) if section==[20.,20.] else (332.,51400.,14100.)
   j=(iy+iz)*torsion_fraction
  e=E
  if not offset and 'section_properties' in by[name]:
   props=by[name]['section_properties']
   area,iy,iz,j=[props[k]*tie_scale for k in ('area_mm2','iy_mm4','iz_mm4','j_mm4')]
   e=props['e_mpa']
  k=stiffness(xyz[n],xyz[m],area,iy,iz,j,e)
  dofs=list(range(6*n,6*n+6))+list(range(6*m,6*m+6));K[np.ix_(dofs,dofs)]+=k
 fixed=[]
 for x in [10.,460.]:
  for y in [20.,680.]:
   target=np.array([x,y,10.]);n=int(np.argmin(np.linalg.norm(xyz-target,axis=1)))
   fixed.extend(range(6*n,6*n+6))
 free=np.array(sorted(set(range(len(K)))-set(fixed)));loads=[];labels=[]
 for name in ['MidRail500','GGM_ShredRail','GGM_HotRearRail','GGM_ThrustRail','GGM_ExMotorRail','GGM_FeederTopRail','FrameBottomCross405','FrameBottomCross440','FrameBottomCross608']:
  a,b=specs[name];n=node((a+b)/2)
  for axis in range(3):
   f=np.zeros(len(K));f[6*n+axis]=100.;loads.append(f);labels.append((name,axis,n))
 F=np.array(loads).T;U=np.zeros(F.shape,dtype=np.longdouble)
 block=K[np.ix_(free,free)]; scale=1/np.sqrt(np.diag(block))
 balanced=block*scale[:,None]*scale[None,:]
 U[free,:]=scale[:,None]*np.linalg.solve(balanced,F[free,:]*scale[:,None])
 for _ in range(10):
  rr=F[free,:].astype(np.longdouble)-block.astype(np.longdouble)@U[free,:].astype(np.longdouble)
  if np.max(np.abs(rr)) < 1e-7: break
  U[free,:]+=np.asarray(scale[:,None]*np.linalg.solve(balanced,np.asarray(rr,dtype=float)*scale[:,None]),dtype=np.longdouble)
 residual=float(np.max(np.abs(F[free,:].astype(np.longdouble)-block.astype(np.longdouble)@U[free,:].astype(np.longdouble))))
 assert np.allclose(np.sum(U.astype(np.longdouble)*(K.astype(np.longdouble)@U.astype(np.longdouble)),axis=0),np.sum(U.astype(np.longdouble)*F,axis=0),rtol=1e-6,atol=1e-6), 'strain energy mismatch'
 assert residual<1e-4,residual
 compliance=[float(abs(U[6*n+axis,i])) for i,(_,axis,n) in enumerate(labels)]
 return {'labels':[f'{n}:{a}' for n,a,_ in labels],'compliance_mm':compliance,'max_translation_mm':float(abs(U.reshape(-1,6,U.shape[1])[:,:3,:]).max()),'residual_n':float(residual),'nodes':len(xyz)}

def benchmark():
    a=np.zeros(3);b=np.array([500.,0.,0.]); area=180.;iy=iz=7200.;j=1440.
    k=stiffness(a,b,area,iy,iz,j)
    for dof, expected in [(0,100*500/(E*area)),(1,100*500**3/(3*E*iz)),
                           (2,100*500**3/(3*E*iy)),(3,100*500/(G*j))]:
        force=np.zeros(6);force[dof]=100.
        u=np.linalg.solve(k[6:,6:],force)
        assert np.isclose(u[dof],expected,rtol=1e-9)
        assert np.allclose(k[:6,6:]@u+np.array([100 if i==dof else 0 for i in range(6)]),
                           np.array([0,0,0,0,50000 if dof==2 else 0,-50000 if dof==1 else 0]),atol=1e-6)
    return 'CANTILEVER_AXIAL_BIAXIAL_BENDING_TORSION_PASS'

def main():
    data=json.loads((OUT/'geometry.json').read_text()); contract=ROOT/'cad/parameters/ggm_frame_revision.json'
    limit=json.loads(contract.read_text())['comparative_screen_limit_ratio']; results=[]
    unit=benchmark()
    for torsion in (.03,.1,1.):
        for joints in (.01,1.,100.):
            baseline=model(data['before'],torsion,joints)
            for factor in (.5,1.):
                reduced=model(data['after'],torsion,joints,factor)
                ratio=np.array(reduced['compliance_mm'])/np.array(baseline['compliance_mm'])
                results.append({'torsion_fraction':torsion,'joint_scale':joints,'tie_section_scale':factor,
                 'max_compliance_ratio':float(max(ratio)),'worst_case':baseline['labels'][int(np.argmax(ratio))],
                 'pass':bool(max(ratio)<=limit),'before':baseline,'after':reduced})
    report={'status':'FRAME_COMPARATIVE_SCREEN_PASS' if all(r['pass'] for r in results) else 'FAIL',
      'unit_benchmark':unit,'cases_per_configuration':27,'configurations':len(results),
      'criterion_max_ratio':limit,'worst_ratio':max(r['max_compliance_ratio'] for r in results),'results':results,
      'assumptions':['100 N unit loads at nine retained rail stations in X/Y/Z; ratios only',
       'T-slot screening sections A=180/332 mm2, Iy/Iz=7200/7200 and51400/14100 mm4; not measured stock',
       'E_Al=69000 MPa, E_steel=200000 MPa, nu=.3; nominal properties, not material acceptance',
       'Profile torsion J=(Iy+Iz)*.03/.1/1 and connector stiffness*.01/1/100 are sensitivity parameters',
       'Channel centroid from CAD; thin-wall J=A*t^2/3 plus 50% effective-section sensitivity; no local hole/bend/warping qualification',
       'Four bolted-to-shelf SH posts excluded from frame skeleton; loads represented on supporting rails',
       'Fixed base, linear elastic, no slip/bolt preload/contact plasticity/fatigue or dynamics',
       'Diagonal equilibration and extended-precision accumulated iterative refinement; residual criterion unchanged at 1e-4'],
      'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in (Path(__file__).resolve(),OUT/'geometry.json',contract)},
      'physical_validation_state':'NOT_RUN','assembled_frame_strength_qualified':False}
    (OUT/'beam_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],'configs',len(results),'worst_ratio',report['worst_ratio'])
    if report['status']!='FRAME_COMPARATIVE_SCREEN_PASS':raise SystemExit(2)

if __name__=='__main__': main()
