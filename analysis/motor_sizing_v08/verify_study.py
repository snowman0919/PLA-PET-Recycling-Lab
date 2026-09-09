"""Numerical qualification of declared demand models, not physical motor tests."""
from pathlib import Path
import csv, hashlib, json, math, os, subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(report):
    if report.get('physical_validation')!='NOT_RUN': raise ValueError('Physical claim')
    if report.get('scenario_count')!=20 or len(report['cases'])!=20: raise ValueError('Incomplete cases')
    if len({r['case'] for r in report['cases']})!=20: raise ValueError('Duplicate case')
    for name,value in report['source_sha256'].items():
        if sha(ROOT/name)!=value: raise ValueError('Stale source: '+name)
    if sha(HERE/'raw/SequenceDemand')!=report['executable_sha256']: raise ValueError('Stale executable')
    for r in report['cases']:
        folder=HERE/'raw'/r['case']
        if sha(folder/'result.csv')!=r['csv_sha256'] or sha(folder/'solver.log')!=r['log_sha256']: raise ValueError('Stale output')
        if r['exit'] or r['ready_s']>1000 or not r['no_cold_extrusion'] or not r['no_mode_overlap']: raise ValueError('Sequence invariant')
        if r['shred_peak_relative_error']>.01: raise ValueError('Peak sampling error')
        if not r['parameters']['fault'] and abs(r['shred_rms_nm']/r['closed_form']['shred_rms_nm']-1)>.001: raise ValueError('Missed cutting pulses')
    return True

def main():
    report=json.loads((HERE/'results.json').read_text()); validate(report)
    runtime=json.loads((HERE/'runtime.json').read_text()); checks=[]
    for name in ('PLA_recommended','PET_recommended'):
        old=next(r for r in report['cases'] if r['case']==name)
        folder=HERE/'raw'/(name+'_dt_half');folder.mkdir(exist_ok=True)
        out=folder/'result.csv';override=','.join(k+'='+str(v) for k,v in old['parameters'].items())
        command=[runtime['loader'],'--library-path',runtime['library_path'],str(HERE/'raw/SequenceDemand'),'-override='+override,'-maxStepSize=0.005','-s=dassl','-lv=LOG_STATS','-r='+str(out)]
        proc=subprocess.run(command,cwd=HERE/'raw',capture_output=True,text=True,timeout=120,env=dict(os.environ,OMP_NUM_THREADS='1'))
        log=proc.stdout+'\n'+proc.stderr;(folder/'solver.log').write_text(log)
        if proc.returncode or 'simulation finished successfully' not in log.lower(): raise RuntimeError('Convergence solve failed')
        with out.open() as f: rows=list(csv.DictReader(f))
        final=rows[-1]
        rms=math.sqrt(float(final['shSquare'])/float(final['shTime']))
        peak=max(float(r['screwTorqueNm']) for r in rows)
        delta={'shred_rms':abs(rms/old['shred_rms_nm']-1),'screw_peak':abs(peak/old['screw_peak_nm']-1)}
        if max(delta.values())>.002: raise ValueError('Time-step convergence failure')
        checks.append({'case':name,'relative_delta':delta,'max_step_s':.005,'csv_sha256':sha(out),'log_sha256':sha(folder/'solver.log')})
        print('TIME_STEP_CHECK',name,delta,flush=True)
    mutation_checks=[]
    for name,mutate in [('stale_source',lambda r:r['source_sha256'].update({'analysis/motor_sizing_v08/SequenceDemand.mo':'0'*64})),('physical_claim',lambda r:r.update(physical_validation='PASS')),('missing_case',lambda r:r.update(scenario_count=19))]:
        broken=json.loads(json.dumps(report));mutate(broken)
        try:validate(broken)
        except ValueError:mutation_checks.append({'mutation':name,'detected':True})
        else:raise AssertionError('Mutation accepted: '+name)
    result={'status':'NUMERICAL_IMPLEMENTATION_CHECKS_PASS','physical_validation':'NOT_RUN','final_demand_runs':20,'time_step_runs':2,'time_step_checks':checks,'mutation_checks':mutation_checks,'analytical_rms_checked':True,'source_sha256':{'verify_study.py':sha(Path(__file__)),'results.json':sha(HERE/'results.json')}}
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('QUALIFIED_NUMERICS_NOT_CALIBRATED_PHYSICS',flush=True)
if __name__=='__main__':main()
