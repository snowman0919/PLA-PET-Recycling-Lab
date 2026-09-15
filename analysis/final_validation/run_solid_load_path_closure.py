"""Released keyed STEP + distributing bearing supports + balanced actual-station loads."""
from pathlib import Path
import os,sys,json,math,tempfile,hashlib
from collections import Counter,defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis/final_validation'))
from run_calculix_v08 import mesh_step,read_gmsh_inp,nset,solve,printed_reactions,helper_source_sha256
from load_path_contract_v08 import station_loads,support_reactions
from distributing_patch_v08 import rigid_fit_coefficients,resultant_loads

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def area(a,b,c):
    v=[b[i]-a[i] for i in range(3)];w=[c[i]-a[i] for i in range(3)]
    return math.sqrt(sum(x*x for x in [v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]))/2

def surface(nodes,elements):
    counts=Counter()
    for e in elements:
        v=list(map(int,e.split(',')))[1:]
        for face in [(v[0],v[1],v[2]),(v[0],v[1],v[3]),(v[0],v[2],v[3]),(v[1],v[2],v[3])]:counts[tuple(sorted(face))]+=1
    return [f for f,n in counts.items() if n==1]

def weights(nodes,faces,selector):
    w=defaultdict(float)
    for face in faces:
        centre=[sum(nodes[n][i] for n in face)/3 for i in range(3)]
        if selector(centre):
            a=area(*(nodes[n] for n in face))
            for n in face:w[n]+=a/3
    if len(w)<4 or sum(w.values())<=0:raise ValueError('empty/small patch')
    return dict(w)

def eq(terms):
    terms=[v for v in terms if abs(v[2])>1e-14]
    if len(terms)<2:raise ValueError('bad MPC')
    return ['*EQUATION',str(len(terms))]+[','.join(f'{n},{d},{c:.12g}' for n,d,c in terms[i:i+4]) for i in range(0,len(terms),4)]

def run_one(st,shaft,share,direction,size,raw,step):
    cases=[station_loads(st,shaft,22,share,direction,60,i) for i in range(6)]
    index=max(range(6),key=lambda i:support_reactions(cases[i],*st['bearing_y_mm'])['max_bearing_n'])
    loads=cases[index]
    name=f'{shaft}_q{share}_d{direction}_mesh{size}'
    folder=raw/name;folder.mkdir()
    nodes,elements=read_gmsh_inp(mesh_step(step,folder,size))
    xmin,xmax=min(p[0] for p in nodes.values()),max(p[0] for p in nodes.values())
    zmin,zmax=min(p[2] for p in nodes.values()),max(p[2] for p in nodes.values())
    ymin=min(p[1] for p in nodes.values())
    cx,cz=(xmin+xmax)/2,(zmin+zmax)/2
    # Exact manufactured local shaft is converted into machine axes with its own origin.
    pts={n:((p[0]-cx)/1000,(p[1]-ymin+st['shaft_y_min_mm'])/1000,(p[2]-cz)/1000) for n,p in nodes.items()}
    faces=surface(pts,elements)
    a,b=[v/1000 for v in st['bearing_y_mm']]
    wa=weights(pts,faces,lambda c:abs(c[1]-a)<=.0044)
    wb=weights(pts,faces,lambda c:abs(c[1]-b)<=.0044)
    y0=st['shaft_y_min_mm']/1000
    wg=weights(pts,faces,lambda c:abs(c[1]-y0)<1e-8)
    ref1,ref2,refg=max(pts)+1,max(pts)+2,max(pts)+3
    centroid=lambda w:tuple(sum(pts[n][i]*v for n,v in w.items())/sum(w.values()) for i in range(3))
    support_a,support_b,gauge_c=centroid(wa),centroid(wb),centroid(wg)
    allpts=dict(pts);allpts.update({ref1:(0,a,0),ref2:(0,b,0),refg:(0,y0,0)})
    deck=['*HEADING','Released keyed shaft; distributed resultant model; SI m N Pa','*NODE']
    deck += [f'{n},{x:.12g},{y:.12g},{z:.12g}' for n,(x,y,z) in allpts.items()]
    deck += ['*ELEMENT,TYPE=C3D4,ELSET=ALL',*elements,'*SOLID SECTION,ELSET=ALL,MATERIAL=STEEL','*MATERIAL,NAME=STEEL','*ELASTIC','2.05e11,0.29']
    support_a,support_b=(0.,a,0.),(0.,b,0.)
    for w,ref,origin,dofs in [(wa,ref1,support_a,[1,2,3]),(wb,ref2,support_b,[1,3])]:
        coefficients=rigid_fit_coefficients(pts,w,origin)
        for dof in dofs:
            terms=[(n,k+1,float(c[dof-1,k])) for n,c in coefficients.items() for k in range(3)]
            terms.sort(key=lambda row:-abs(row[2]))
            deck+=eq(terms+[(ref,dof,-1.)])
    r=.0125
    coefficients=rigid_fit_coefficients(pts,wg,(0.,y0,0.))
    terms=[(n,k+1,float(c[4,k])*r) for n,c in coefficients.items() for k in range(3)]
    terms.sort(key=lambda row:-abs(row[2]))
    deck+=eq(terms+[(refg,1,-1.)])
    deck += nset('REACTION',[ref1,ref2,refg])
    deck += ['*BOUNDARY',f'{ref1},1,3,0',f'{ref2},1,1,0',f'{ref2},3,3,0',f'{refg},1,1,0','*STEP','*STATIC','0.1,1']
    nodal=defaultdict(lambda:[0.,0.,0.]); actual=[]
    for force in loads:
        if max(abs(force[k]) for k in ['fx_n','fz_n','torque_nm'])<1e-10:continue
        yc=force['y_mm']/1000
        width=.0085 if 'gear' in force['source'] else .0028
        w=weights(pts,faces,lambda c:abs(c[1]-yc)<=width)
        total=sum(w.values());x0=sum(pts[n][0]*v for n,v in w.items())/total;z0=sum(pts[n][2]*v for n,v in w.items())/total
        yy=sum(pts[n][1]*v for n,v in w.items())/total
        exact=resultant_loads(pts,w,[force['fx_n'],0.,force['fz_n']],[0.,force['torque_nm'],0.],[0.,yc,0.])
        for n,f in exact.items():
            for axis in range(3):nodal[n][axis]+=float(f[axis])
        actual.append({**force,'nominal_y_mm':force['y_mm'],'y_mm':yy*1000,'patch_area_mm2':total*1e6,'patch_centroid_xz_mm':[x0*1000,z0*1000],'nodes':len(w)})
    deck += ['*CLOAD']+[f'{n},{i+1},{f:.12g}' for n,v in nodal.items() for i,f in enumerate(v) if abs(f)>1e-12]
    deck += ['*NODE PRINT,NSET=REACTION','RF','*NODE FILE','U,RF','*EL FILE','S','*END STEP','']
    result=solve(folder,'\n'.join(deck))
    values={}
    for text in (folder/'model.dat').read_text().splitlines():
        fields=text.split()
        if len(fields)==4 and fields[0].isdigit() and int(fields[0]) in (ref1,ref2,refg):values[int(fields[0])]=tuple(float(v) for v in fields[1:])
    if set(values)!={ref1,ref2,refg}:raise ValueError('missing support reaction')
    rf=[sum(values[n][i] for n in (ref1,ref2)) for i in range(3)]
    rm=np.cross(np.array(support_a),np.array(values[ref1]))+np.cross(np.array(support_b),np.array(values[ref2]))
    rm[1]+=values[refg][0]*r
    reaction={'force_n':rf,'moment_about_origin_nm':rm.tolist(),'gauge_torque_nm':values[refg][0]*r,'support_centroids_m':[support_a,support_b]}
    netf=[sum(f[i] for f in nodal.values()) for i in range(3)]
    netm=[0.,0.,0.]
    for n,(fx,fy,fz) in nodal.items():
        x,y,z=pts[n];netm[0]+=y*fz-z*fy;netm[1]+=z*fx-x*fz;netm[2]+=x*fy-y*fx
    residualf=[a+b for a,b in zip(netf,reaction['force_n'])]
    residualm=[a+b for a,b in zip(netm,reaction['moment_about_origin_nm'])]
    acceptable=max(abs(v) for v in residualf)<.03 and max(abs(v) for v in residualm)<.003
    analytic_support=support_reactions(loads,*st['bearing_y_mm'])
    data={'shaft':shaft,'share':share,'direction':direction,'cut_index':index,'mesh_mm':size,'nodes':len(nodes),'elements':len(elements),'actual_load_patches':actual,'applied_force_n':netf,'applied_moment_nm':netm,'reaction':reaction,'analytic_support_reaction':analytic_support,'force_residual_n':residualf,'moment_residual_nm':residualm,'equilibrium_pass':acceptable,'result':result,'step_sha256':sha(step),'deck_sha256':sha(folder/'model.inp'),'frd_sha256':sha(folder/'model.frd'),'dat_sha256':sha(folder/'model.dat'),'raw_dir':str(folder.relative_to(ROOT))}
    (folder/'run.json').write_text(json.dumps(data,indent=2)+'\n')
    print('SOLID_LOAD_CASE',name,acceptable,result['max_displacement_mm'],flush=True)
    if not acceptable:raise RuntimeError('equilibrium check failed')
    return data

def main():
    stations=json.loads((ROOT/'analysis/final_validation/input/geometry_manifest.json').read_text())['shredder_stations']
    raw=Path(tempfile.mkdtemp(prefix='solid-load-',dir=ROOT/'analysis/final_validation/results/v0.8/raw'))
    runs=[]
    for shaft,share in [('153',0.),('153',1.),('105',1.)]:
        step=ROOT/'analysis/final_validation/input'/('CUT-05R.step' if shaft=='153' else 'CUT-05.step')
        for direction in [-1,1]:
            for size in [3.,2.,1.5]:runs.append(run_one(stations[shaft],shaft,share,direction,size,raw,step))
    conv=[]
    for i in range(0,len(runs),3):
        a,b=runs[i+1]['result']['max_displacement_mm'],runs[i+2]['result']['max_displacement_mm']
        conv.append({'shaft':runs[i]['shaft'],'share':runs[i]['share'],'direction':runs[i]['direction'],'displacement_relative_change':abs(a-b)/max(b,1e-12)})
    om_path=ROOT/'analysis/load_cases/openmodelica_dynamic_envelope.json'
    om=json.loads(om_path.read_text())['loads']
    max_bearing=max(r['analytic_support_reaction']['max_bearing_n'] for r in runs)
    max_chain=max(math.hypot(p['fx_n'],p['fz_n']) for r in runs for p in r['actual_load_patches'] if p['source'].startswith('chain'))
    max_stress=max(r['result']['max_von_mises_mpa'] for r in runs)
    checks={'all_18_solver_cases_pass':len(runs)==18 and all(r['result']['status']=='PASS' and not r['result']['negative_jacobian'] for r in runs),
            'all_equilibrium_checks_pass':all(r['equilibrium_pass'] for r in runs),
            'medium_to_fine_displacement_change_le_5pct':max(c['displacement_relative_change'] for c in conv)<=.05,
            'modeled_bearing_envelope_ge_openmodelica_peak':max_bearing>=om['peak_bearing_load_n'],
            'modeled_chain_envelope_ge_openmodelica_peak':max_chain>=om['peak_chain_force_n'],
            'keyed_solid_stress_below_177p5mpa_screen':max_stress<=177.5}
    output={'status':'PASS' if all(checks.values()) else 'FAIL','physical_validation_state':'NOT_RUN','runs':runs,'convergence':conv,'checks':checks,
      'envelope_comparison':{'modeled_max_bearing_n':max_bearing,'openmodelica_peak_bearing_n':om['peak_bearing_load_n'],'modeled_max_chain_n':max_chain,'openmodelica_peak_chain_n':om['peak_chain_force_n'],'max_solid_stress_mpa':max_stress},
      'scope':'Actual keyed STEP C3D4 with force/moment-consistent surface resultants and distributed bearing supports. 22 N.m jam/chain cases exceed the current OpenModelica bearing and chain envelopes; contact/fatigue remain later physical/service observations, not extra hidden load multipliers.',
      'calculix_helper_source_sha256':helper_source_sha256(),
      'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'analysis/final_validation/distributing_patch_v08.py',ROOT/'analysis/final_validation/load_path_contract_v08.py',ROOT/'analysis/final_validation/results/v0.8/journal_keyseat_closure/result.json',om_path,ROOT/'analysis/structural/run_load_checks.py',ROOT/'analysis/final_validation/input/geometry_manifest.json',ROOT/'analysis/final_validation/input/CUT-05.step',ROOT/'analysis/final_validation/input/CUT-05R.step']}}
    (ROOT/'analysis/final_validation/results/v0.8/solid_load_path_closure.json').write_text(json.dumps(output,indent=2)+'\n')
    print('SOLID_LOAD_DONE',len(runs),max(c['displacement_relative_change'] for c in conv),flush=True)
if __name__=='__main__':main()
