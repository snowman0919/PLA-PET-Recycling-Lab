"""모델 수정 후 지정 그룹 재평가; 물리 시스템 합격으로 사용 금지."""
import hashlib
import json
import sys
from pathlib import Path
import summarize_results as base
sys.path.insert(0,str(base.SIM/'scripts'))
from generate_runner import duration

def main():
    base.RAW = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2])
    output.write_text(json.dumps({'status':'INCOMPLETE','physical_validation_state':'NOT_RUN'})+'\n')
    group = sys.argv[3] if len(sys.argv)>3 else 'shredder'
    assert group in base.C['scenario_groups']
    cases = {}
    for name in base.C['scenario_groups'][group]:
        rows = base.load(name)
        times = [r['time'] for r in rows]
        stop, intervals = duration(name)
        assert times[0]==0 and abs(times[-1]-stop)<1e-8
        assert all(0<=b-a<=stop/intervals+1e-6 for a,b in zip(times,times[1:]))
        item, failures = base.evaluate(name,rows)
        cases[name] = {**item,'failures':failures,
                       'csv_sha256':hashlib.sha256((base.RAW/f'{name}_res.csv').read_bytes()).hexdigest()}
    sources = list((base.SIM/'PLA_PET_Recycler').rglob('*.mo')) + [
        Path(__file__),Path(base.__file__),base.SIM/'acceptance_criteria.json',
        base.SIM/'scripts/generate_runner.py']
    result = {'status':'HOLD','physical_validation_state':'NOT_RUN',
              'scope':f'{group} group only; model assumptions remain unqualified; not full release or physical qualification',
              'raw_directory':str(base.RAW),'cases':cases,
              'failed_scenarios':[name for name,c in cases.items() if c['failures']],
              'source_sha256':{str(p.resolve().relative_to(base.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    if group=='shredder':
        result['peak_chain_radial_bound_n']=max(c['peak_chain_force_n'] for c in cases.values())
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('GROUP_RERUN_HOLD',group,len(cases),result['failed_scenarios'])

if __name__=='__main__':
    main()
