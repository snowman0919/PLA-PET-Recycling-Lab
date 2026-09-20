"""Reproducible C1 engineering screens. No empirical cutting/thermal data is implied."""
from pathlib import Path
import json,math,csv,itertools,hashlib
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq
from shapely.geometry import Polygon,Point
from geometry import cycloid_profile,hooks
ROOT=Path(__file__).resolve().parents[1];P=json.loads((ROOT/'design/parameters.json').read_text())
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)

def shaft_beam(diameter_mm,supports,loads,torque,ends):
    """Euler-Bernoulli beam with free rotation/simple-support translations; SI internals."""
    xs=np.array(sorted(set(list(np.linspace(*ends,33))+list(supports)+[x for x,f in loads])))/1000
    n=len(xs);K=np.zeros((2*n,2*n));F=np.zeros(2*n)
    E=200e9;d=diameter_mm/1000;I=math.pi*d**4/64
    for i,L in enumerate(np.diff(xs)):
        k=E*I/L**3*np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],[-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
        ix=[2*i,2*i+1,2*i+2,2*i+3];K[np.ix_(ix,ix)]+=k
    for x,f in loads:F[2*np.argmin(abs(xs-x/1000))]+=f
    fixed=[2*np.argmin(abs(xs-x/1000)) for x in supports];free=np.setdiff1d(np.arange(2*n),fixed)
    u=np.zeros(2*n);u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free]);R=K@u-F
    mom=[]
    for i,L in enumerate(np.diff(xs)):
        k=E*I/L**3*np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],[-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
        ff=k@u[2*i:2*i+4];mom.extend([abs(ff[1]),abs(ff[3])])
    M=max(mom);sb=M*d/2/I;tau=16*torque/(math.pi*d**3);vm=(sb*sb+3*tau*tau)**.5
    return {'shaft_mm':diameter_mm,'supports_mm':supports,'loads_N_at_mm':loads,'assumed_E_GPa':200,'torque_Nm':torque,'max_deflection_mm':float(max(abs(u[::2]))*1000),'max_bending_Nm':float(M),'nominal_vm_MPa':float(vm/1e6),'screen_vm_with_assumed_Kt2_MPa':float(2*vm/1e6),'support_reactions_N':[float(R[i]) for i in fixed],'status':'ELASTIC_BEAM_SCREEN_NOT_3D_STRESS_OR_FATIGUE_QUALIFICATION'}

def cooling(h,n=32):
    rho=1240;cp=1800;k=.13;r=.00175/2;Tamb=25;T0=200;target=50
    edge=np.linspace(0,r,n+1);rc=(edge[:-1]+edge[1:])/2;mass=rho*cp*math.pi*(edge[1:]**2-edge[:-1]**2)
    A=np.zeros((n,n))
    for i in range(n-1):
        g=2*math.pi*k*edge[i+1]/(rc[i+1]-rc[i]);A[i,i]-=g/mass[i];A[i,i+1]+=g/mass[i];A[i+1,i]+=g/mass[i+1];A[i+1,i+1]-=g/mass[i+1]
    # Convection and last half-cell conduction in series.
    g=1/(math.log(r/rc[-1])/(2*math.pi*k)+1/(2*math.pi*r*h));A[-1,-1]-=g/mass[-1]
    init=np.full(n,T0-Tamb)
    def center(t):return float((expm(A*t)@init)[0]+Tamb)
    t=brentq(lambda t:center(t)-target,.01,400)
    v=(100/1000/3600)/(rho*math.pi*r*r)
    return {'h_W_m2K_assumed':h,'nodes':n,'center_cool_time_s':t,'length_at_100gh_mm':v*t*1000,'length_with_25pct_margin_mm':1.25*v*t*1000,'max_g_h_in_275mm_with_margin':100*275/(1.25*v*t*1000),'rho_assumed':rho,'cp_assumed':cp,'k_assumed':k,'initial_C':T0,'ambient_C':Tamb,'target_center_C':target}

def clearance_metric(R,e,r,cl,samples=720,phases=49):
    pts=np.array(cycloid_profile(R,e,9,r,cl,samples));polygon=Polygon(pts)
    if not polygon.is_valid:return -10.,float(np.linalg.norm(pts,axis=1).max()),False
    a=pts;b=np.roll(pts,-1,axis=0);ab=b-a;den=(ab*ab).sum(axis=1)
    worst=1e10
    for th in np.linspace(0,2*math.pi,phases,endpoint=False):
        ps=-th/8;rot=np.array([[math.cos(ps),math.sin(ps)],[-math.sin(ps),math.cos(ps)]])
        ph=np.arange(9)*2*math.pi/9
        pin=np.column_stack((R*np.cos(ph)-e*math.cos(th),R*np.sin(ph)-e*math.sin(th)))@rot.T
        diff=pin[:,None,:]-a[None,:,:]
        tt=np.clip(np.sum(diff*ab[None,:,:],axis=2)/den[None,:],0,1)
        dist=np.linalg.norm(diff-tt[:,:,None]*ab[None,:,:],axis=2).min(axis=1)
        worst=min(worst,float(dist.min()-r))
    return worst,float(np.linalg.norm(pts,axis=1).max()),True

def allocate(ia,ib,requests,priority):
    fixed=47.84;used=fixed+24*(max(0,ia)+max(0,ib));on=[False]*4
    for i in priority:
        w=[100,100,100,60][i]
        if requests[i] and used+w<=500+1e-9:on[i]=True;used+=w
    return on,used

def main():
    m1=P['M1']['rated_kgf_cm']*.0980665;m2=P['M2']['rated_kgf_cm']*.0980665
    drive=[]
    for name,t1,t2 in [('low',8,1),('nominal_assumed',14,2),('upper_assumed',20,3),('jam_sensitivity_not_permitted',30,5)]:
        tin=t1/(40/15*.9)+t2*2/.9
        drive.append({'case':name,'S1_Nm':t1,'S2_orbit_Nm':t2,'M1_required_Nm':tin,'M1_rated_Nm':m1,'remaining_Nm':m1-tin,'within_rated':tin<=m1})
    beams=[shaft_beam(d,[147.5,338.5],[(244,2000),(358,-20/(9.525/2000/math.sin(math.pi/24)))],20,[100,382]) for d in [20,25,30]]
    beams.append(shaft_beam(12,[227,339],[(275,3/.007),(378,-3/(9.525/2000/math.sin(math.pi/12)))],3,[205,394]))
    cool=[cooling(h) for h in [40,80,120,160]]
    conv=[cooling(80,n) for n in [16,32,64]]
    S=P['S2'];clear,rr,valid=clearance_metric(S['pin_ring_R_mm'],S['eccentric_mm'],8,.2,S['guide_samples'],721)
    # Axial cutter interference test uses exact intervals, not an arbitrary rotation snapshot.
    intervalsA=[(163+12.4*i,169+12.4*i) for i in range(13)]
    intervalsB=[(169.2+12.4*i,175.2+12.4*i) for i in range(13)]
    clearax=min(max(a[0]-b[1],b[0]-a[1]) for a in intervalsA for b in intervalsB)
    budget={'psu_rated_W':800,'PSU_current_at24V_A':800/24,'M1_rated_electrical_W':24*8.2,'M2_rated_electrical_W':24*1.8,'heater_installed_W':360,'fans_W':2*7.92,'controls_pull_spool_allowance_W':32,'nominal_all_on_W':24*(8.2+1.8)+360+47.84,'hardware_limit_proposal_A':[12,3],'bounded_all_on_at24V_W':24*(12+3)+360+47.84,'operational_cap_W':500,'actual_current_limit_and_transient_testing':'NOT_RUN'}
    tests=0;maxallowed=0
    for ia in np.linspace(0,12,25):
      for ib in np.linspace(0,3,13):
       for mask in itertools.product([False,True],repeat=4):
        for shift in range(4):
         _,used=allocate(ia,ib,mask,list(np.roll(np.arange(4),shift)));tests+=1
         assert used<=500+1e-7;maxallowed=max(maxallowed,used)
    # The installed inner buffer volume is integrated from exact loft endpoint rectangles.
    z=np.linspace(0,73,10001);wi=44+(184-44)*(z+1)/75;di=34+(42-34)*(z+1)/75
    buf=float(np.trapezoid(wi*di,z))/1000
    results={'revision':'C1','drive':drive,'speeds_rpm':{'M1':58,'S1':58*15/40,'S2_orbit':116,'S2_self':-14.5,'M2_screw':12},'shaft_beam_screens':beams,'cooling_sensitivity':cool,'cooling_mesh_check':conv,'stage1':{'cutters_total':26,'axial_gap_nominal_mm':clearax,'individual_stack_mm':13*6+12*6.4,'combined_stack_mm':13*6+12*6.4+6.2,'radial_tip_spacer_clearance_mm':60-40-18,'note':'Stack grinding/tolerance accumulation and shim inspection required.'},'stage2':{'ideal_orbit_self_ratio':-.125,'e_mm':7,'chamber_ID_mm':125.6,'tip_OD_mm':110,'tip_chamber_nominal_gap_mm':.8,'guide_profile_valid':valid,'profile_vertices':S['guide_samples'],'full_revolution_phases':721,'fixed_pins_per_phase':9,'minimum_pin_profile_clearance_mm':clear,'profile_max_radius_mm':rr,'tolerance_screen':'Nominal CAD only; loaded contacts/backlash/wear are not simulated.'},'power':budget,'power_allocator_exhaustive':{'cases':tests,'max_admitted_W':maxallowed,'passed':True,'scope':'Exact arithmetic reference; no firmware timing or hardware fault validation'},'buffer':{'internal_geometric_mL':buf,'usable_at75pct_mL':.75*buf,'needs_resize':buf<300},'extrusion_pressure_sensitivity':{'assumed_MPa':[5,10],'thrust_N':[p*math.pi*16**2/4 for p in [5,10]],'actual_pressure':'NOT_MEASURED'},'limitations':['DEM/breakage/particle size NOT_RUN','3D structural/thermal stress solve NOT_RUN','Hardware material and load validation NOT_RUN','Kinematic clearance is not contact fatigue or a machine safety certificate']}
    (OUT/'engineering.json').write_text(json.dumps(results,indent=2))
    with (OUT/'power_trace.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['t_s','M1_A','M2_A','heater100a','heater100b','heater100c','heater60','admitted_W'])
        for t in range(240):
            ia=0 if t<60 or t>=180 else 8.2+2*math.sin(t*.2);ib=0 if t<60 else 1.8
            on,p=allocate(ia,ib,[True]*4,list(np.roll(np.arange(4),t%4)));w.writerow([t,ia,ib,*map(int,on),p])
    print(json.dumps({'power_cases':tests,'S2_gap':clear,'buffer_internal_mL':buf,'drive_margin_nominal_Nm':drive[1]['remaining_Nm'],'cooling_80':cool[1]},indent=2),flush=True)
if __name__=='__main__':main()
