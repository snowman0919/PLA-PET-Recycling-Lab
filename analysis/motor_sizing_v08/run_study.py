"""Run bounded process-demand studies with a real OpenModelica executable."""
from pathlib import Path
import csv, hashlib, json, math, os, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PI=math.pi

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mean(v): return sum(v)/len(v) if v else None

def independent(p):
    w=p['throughputGph']/p['deliveryGphPerRpm']*PI/30
    visc=2*PI*p['viscosityPaS']*w*.008**3*.160*((1-.0015/.016)/.00096+(.0015/.016)/.00015)
    press=p['pressureMPa']*1e6*PI*.01622**2/4*.016/(2*PI*p['conveyingEfficiency'])
    a=p['shearMPa']*p['effectiveCutAreaMM2']*29/1000*1.2
    return {'shred_peak_nm':.6+a,'shred_rms_nm':math.sqrt(.36+1.2*a*3/16+a*a*35/256),
            'screw_at_setpoint_nm':visc+press+p['solidFeedTorqueNm']+.2,
            'screw_rpm':w*30/PI,'pressure_work_component_nm':press,'viscous_component_nm':visc}

def scenarios():
    tiers=[('minimum',50,10,4,1.5,.4),('recommended',100,16,8,3,.8),('headroom',150,24,12,4,1.2)]
    out=[]
    for material in (1,2):
        for i,(tier,rate,rpm,area,pressure,feed) in enumerate(tiers):
            p=dict(material=material,fault=0,throughputGph=rate,deliveryGphPerRpm=6.209 if material==1 else 5.418,
                   shredRpm=rpm,shearMPa=35 if material==1 else 40,effectiveCutAreaMM2=area,
                   pressureMPa=pressure,viscosityPaS=((600,1200,2000) if material==1 else (800,1600,2600))[i],
                   conveyingEfficiency=.4,solidFeedTorqueNm=feed)
            out.append((('PLA' if material==1 else 'PET')+'_'+tier,p))
    return out

def run_case(name,p):
    folder=HERE/'raw'/name; folder.mkdir(exist_ok=True)
    exe=HERE/'raw/SequenceDemand'
    result=folder/'result.csv'
    override=','.join(k+'='+str(v) for k,v in p.items())
    started=time.time()
    runtime=json.loads((HERE/'runtime.json').read_text())
    proc=subprocess.run([runtime['loader'],'--library-path',runtime['library_path'],str(exe),'-override='+override,'-r='+str(result),'-s=dassl','-maxStepSize=0.01','-lv=LOG_STATS'],
                        cwd=HERE/'raw',capture_output=True,text=True,timeout=120,
                        env=dict(os.environ,OMP_NUM_THREADS='1'))
    log=proc.stdout+'\n'+proc.stderr; (folder/'solver.log').write_text(log)
    if proc.returncode or not result.is_file() or 'simulation finished successfully' not in log.lower():
        raise RuntimeError(name+': solve failed: '+log[-2000:])
    with result.open() as f: rows=list(csv.DictReader(f))
    def vals(key,predicate=lambda r:True): return [float(r[key]) for r in rows if predicate(r)]
    normal=[r for r in rows if float(r['stage'])==3 and float(r['processTime'])>60]
    final=rows[-1]; ref=independent(p)
    normal_w=mean([float(r['screwOmega']) for r in normal])
    summary={'case':name,'parameters':p,'method':'DASSL','exit':proc.returncode,'wall_s':time.time()-started,
      'records':len(rows),'ready_s':float(final['readyAt']), 'product_mass_g':float(final['accumulatedG']),
      'shred_peak_nm':max(vals('shredTorqueNm')), 'shred_rms_nm':math.sqrt(float(final['shSquare'])/float(final['shTime'])),
      'screw_normal_mean_nm':mean([float(r['screwTorqueNm']) for r in normal]),
      'screw_peak_nm':max(vals('screwTorqueNm')), 'normal_screw_rpm':normal_w*30/PI if normal_w else None,
      'screw_rms_nm':math.sqrt(float(final['exSquare'])/float(final['exTime'])) if float(final['exTime']) else None,
      'screw_peak_shaft_w':max(float(r['screwTorqueNm'])*float(r['screwOmega']) for r in rows),
      'shred_peak_shaft_w':max(float(r['shredTorqueNm'])*float(r['shredOmega']) for r in rows),
      'no_cold_extrusion':all(float(r['screwOmega'])==0 or float(r['tempC'])>=(205 if p['material']==1 else 270)-5 for r in rows),
      'no_mode_overlap':all(not (float(r['shredOmega']) and float(r['screwOmega'])) for r in rows),
      'csv_sha256':sha(result),'log_sha256':sha(folder/'solver.log'),'closed_form':ref}
    summary['shred_peak_relative_error']=abs(summary['shred_peak_nm']/ref['shred_peak_nm']-1)
    return summary

def main():
    base=scenarios(); cases=list(base)
    for name,p in base:
        if not name.endswith('recommended'): continue
        for label,fault in [('jam_stop',1),('die_stop',2),('starvation',3)]:
            cases.append((name+'_'+label,dict(p,fault=fault)))
        cases.append((name+'_viscosity_high',dict(p,viscosityPaS=p['viscosityPaS']*1.5)))
        cases.append((name+'_viscosity_low',dict(p,viscosityPaS=p['viscosityPaS']*.5)))
        cases.append((name+'_cut_strength_high',dict(p,shearMPa=50)))
        cases.append((name+'_pressure_work_eff_low',dict(p,conveyingEfficiency=.3)))
    bindings=[HERE/'runtime.json',HERE/'SequenceDemand.mo',Path(__file__),ROOT/'cad/parameters/baseline.json',
              ROOT/'simulation/openmodelica/PLA_PET_Recycler/Components/HookMaterialLoad.mo',
              ROOT/'simulation/openmodelica/PLA_PET_Recycler/Systems/ThermalExtruderSystem.mo',
              ROOT/'calculations/run_engineering.py']
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in bindings}
    result=[]
    for name,p in cases:
        r=run_case(name,p); result.append(r)
        print(name,round(r['shred_peak_nm'],3),round(r['screw_peak_nm'],3),flush=True)
    if any(sha(ROOT/p)!=h for p,h in source_hashes.items()): raise RuntimeError('Source changed during run')
    report={'status':'CONDITIONAL_DEMAND_SIZING','physical_validation':'NOT_RUN',
      'model_scope':'Imposed sequence/kinematic load demand; no PID, motor thermal, fragment DEM or measured rheology validation',
      'source_sha256':source_hashes,'executable_sha256':sha(HERE/'raw/SequenceDemand'),
      'cases':result,'scenario_count':len(result),'purchases':0}
    (HERE/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('COMPLETE',len(result))
if __name__=='__main__': main()
