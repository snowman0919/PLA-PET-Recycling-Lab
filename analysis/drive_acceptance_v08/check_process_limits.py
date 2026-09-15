"""Compare actual drive setpoints to conditional demand, without raising limits."""
from pathlib import Path
import hashlib, importlib.util, json, shutil
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEMAND = ROOT / 'analysis/motor_sizing_v08'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    contract_path = ROOT / 'control/ggm_drive_contract.json'
    source_paths = [contract_path, DEMAND/'run_study.py', DEMAND/'SequenceDemand.mo',
                    DEMAND/'runtime.json', DEMAND/'results.json', Path(__file__)]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
    contract = json.loads(contract_path.read_text())
    evidence = json.loads((DEMAND/'results.json').read_text())
    exe = DEMAND/'raw/SequenceDemand'
    if sha(exe) != evidence['executable_sha256']:
        raise ValueError('Demand executable does not match source evidence')
    for name, digest in evidence['source_sha256'].items():
        if sha(ROOT/name) != digest: raise ValueError('Stale demand source: '+name)
    spec = importlib.util.spec_from_file_location('drive_demand', DEMAND/'run_study.py')
    study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    work = HERE/'raw/process'; (work/'raw').mkdir(parents=True, exist_ok=True)
    runtime_names = ('SequenceDemand', 'SequenceDemand_init.xml', 'SequenceDemand_JacA.bin',
                     'SequenceDemand_external_functions.json', 'SequenceDemand_info.json')
    for name in runtime_names:
        shutil.copy2(DEMAND/'raw'/name, work/'raw'/name)
    hashes.update({str((DEMAND/'raw'/name).relative_to(ROOT)):sha(DEMAND/'raw'/name) for name in runtime_names})
    shutil.copy2(DEMAND/'runtime.json', work/'runtime.json')
    study.HERE = work
    rows = []
    limit = contract['protection']['command_limit_gearbox_nm']
    for material in ('PLA', 'PET'):
        base = dict(next(p for n,p in study.scenarios() if n == material+'_recommended'))
        rpm = contract['screw']['target_'+material.lower()+'_rpm']
        for label, speed, viscosity_scale in [('selected', rpm, 1.0),
                ('selected_high_viscosity', rpm, 1.5), ('reduced_high_viscosity', 12, 1.5),
                ('startup_high_viscosity', 10, 1.5)]:
            params = dict(base, throughputGph=base['deliveryGphPerRpm']*speed,
                          viscosityPaS=base['viscosityPaS']*viscosity_scale)
            row = study.run_case(material+'_'+label, params)
            row['gearbox_torque_trip_nm'] = limit
            row['expected_guard_response'] = ('NO_TORQUE_TRIP_IN_THIS_ASSUMED_CASE'
                if row['screw_peak_nm'] <= limit else 'OVERLOAD_STOP_EXPECTED')
            row['automatic_derating_implemented'] = False
            rows.append(row)
            print(row['case'], row['screw_peak_nm'], row['expected_guard_response'], flush=True)
    if any(sha(ROOT/p) != h for p,h in hashes.items()):
        raise RuntimeError('Source changed during review')
    report = {'status':'CONDITIONAL_OPERATING_ENVELOPE_REVIEW',
        'scope':'Imposed demand only; not motor transient/pressure/heat-transfer qualification',
        'physical_validation':'NOT_RUN', 'machine_release':'HOLD',
        'existing_trip_preserved':True, 'source_sha256':hashes,
        'source_executable_sha256':sha(exe), 'case_count':len(rows), 'cases':rows}
    (HERE/'process_limits.json').write_text(json.dumps(report, indent=2)+'\n')
    print('COMPLETED', len(rows))

if __name__ == '__main__': main()
