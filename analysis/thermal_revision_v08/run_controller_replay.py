"""Execute source-bound offline heater replay without asserting plant qualification."""
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analysis.thermal_revision_v08.compare import configurations
from analysis.thermal_revision_v08.coupled_replay import run_case
from analysis.thermal_revision_v08.power_loop import build_library, DEPENDENCIES
from analysis.thermal_revision_v08.steady_state import required_power


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(record):
    return [record['barrel_peak_c'], record['die_peak_c'],
            *record['heater_peaks_c'], *record['final_sensor_c']]


def main():
    base, mount, reference, configs = configurations()
    library = build_library()
    paths = set(DEPENDENCIES)
    paths.update(Path(__file__).parent/name for name in (
        'power_loop.py', 'coupled_replay.py', 'run_controller_replay.py',
        'model.py', 'model_inputs.json', 'compare.py', 'reference_geometry.json', 'steady_state.py'))
    paths.update(ROOT/name for name in ('cad/parameters/baseline.json',
        'cad/parameters/final_v08.json', 'firmware/arduino_mega/arduino_mega.ino',
        'firmware/arduino_mega/src/machine_supervisor.cpp'))
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    records = []
    for geometry, (stations, zones) in configs.items():
        for contact, air, support in itertools.product((200.0,1000.0),(8.0,15.0),(0.05,0.2)):
            result = run_case(base, stations, zones, library, contact=contact,
                              air=air, support=support)
            result['geometry_case'] = geometry
            records.append(result)
            print('REPLAY', geometry, contact, air, support, result['fault_bits'],
                  result['process_targets_held'], max(result['heater_peaks_c']), flush=True)
    stations, zones = configs['combined']
    sensitivity = []
    for contact, lag, extrusion in ((200.0,13.0,False),(1000.0,13.0,False),
                                    (200.0,0.0,True),(1000.0,0.0,True)):
        sensitivity.append(run_case(base, stations, zones, library, contact=contact,
            sensor_tau_s=lag, extrusion=extrusion))
    refinement = []
    refinement_runs = []
    for contact in (200.0,1000.0):
        coarse = next(r for r in records if r['geometry_case']=='combined'
            and r['contact_h_w_m2k']==contact and r['air_h_w_m2k']==8
            and r['support_g_w_k']==0.05)
        temporal = run_case(base,stations,zones,library,contact=contact,dt=0.025)
        spatial = run_case(base,stations,zones,library,contact=contact,dt=0.025,dx=0.00125)
        final_time = run_case(base,stations,zones,library,contact=contact,dt=0.0125,dx=0.00125)
        refinement_runs.extend((temporal, spatial, final_time))
        changes = [max(abs(a-b) for a,b in zip(metrics(left),metrics(right)))
            for left,right in ((coarse,temporal),(temporal,spatial),(spatial,final_time))]
        refinement.append(dict(contact_h_w_m2k=contact, changes_c=changes,
            same_fault_status=len({r['fault_bits'] for r in (coarse,temporal,spatial,final_time)})==1,
            fine=final_time, limit_c=1.0))
    faults = {}
    for name, arguments in [('open_chain',dict(chain_open_s=1)),
                            ('nonfinite_sensor',dict(sensor_nan_s=1)),
                            ('permission_loss',dict(permit_off_s=1))]:
        faults[name] = run_case(base,stations,zones,library,duration=10,**arguments)
    steady_cases = [dict(contact_h_w_m2k=h, air_h_w_m2k=a, support_g_w_k=g,
        **required_power(base,stations,zones,contact=h,air=a,support=g))
        for h,a,g in itertools.product((200.,1000.),(8.,15.),(.05,.2))]
    all_runs = records+sensitivity+refinement_runs+list(faults.values())
    checks = dict(steady_balance=all(abs(r['global_residual_w'])<1e-7 and r['local_residual_w']<1e-7 for r in steady_cases),
        component_and_plant_checks=all(all(r['checks'].values()) for r in all_runs),
        four_way_geometry=set(r['geometry_case'] for r in records)==set(configs),
        temporal_and_spatial_refinement=all(max(r['changes_c'])<=1 and r['same_fault_status'] for r in refinement),
        chain_loss_latches=faults['open_chain']['first_fault_s']==1,
        sampled_nan_latches=faults['nonfinite_sensor']['first_fault_s']==1,
        source_hashes_unchanged=all(digest(ROOT/p)==h for p,h in hashes.items()))
    result = dict(status='COMPILED_HEATER_PLANT_REPLAY_PASS' if all(checks.values()) else 'FAIL',
        source_sha256=hashes, library_sha256=digest(library), checks=checks,
        compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
        scope='Host compiled HeaterController and HeaterPowerAllocator; duplicated supervisor sequencing, not complete firmware',
        cases=records, sensitivity=sensitivity, refinement=refinement, fault_cases=faults,
        steady_demand=steady_cases,
        design_acceptance="HOLD_PROCESS_AND_HARDWARE_QUALIFICATION",
        process_acceptance=dict(status="HOLD",
            all_sensitivity_process_targets_met=all(r["process_targets_held"] for r in records+sensitivity),
            source="Model sensitivity outcomes, not physical tests",
            supplier_sheath_rating_verified=False),
        nominal_process_cases_passed=sum(r["process_targets_held"] for r in records),
        nominal_process_cases_total=len(records),
        physical_validation_state='NOT_RUN', machine_release='HOLD',
        fabrication_authorized=False, energization_authorized=False,
        limitations=[
            'The 50 ms host control schedule is an assumed scenario, not measured AVR timing.',
            'Production sensor sampling is 250 ms; clock, ADC and actual PWM waveforms are not emulated.',
            'Mechanical guards, full MachineSupervisor state machine and board adapters are outside this host bridge.',
            'Plant conductances and thermal properties are unmeasured sensitivities, not certified bounds.',
            'Fault detection and stable numerical integration do not imply process-temperature compliance.',
            'No screw, polymer, material flow, guard radiation exchange or contact nonlinearity.',
            'No GPIO, serial, firmware upload or physical energization occurs.'
        ])
    output = ROOT/'analysis/thermal_revision_v08/results/controller_replay.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['status'],json.dumps(checks),flush=True)
    print('PROCESS_TARGETS', result['nominal_process_cases_passed'], '/', len(records), flush=True)
    print('REFINEMENT', [(r['contact_h_w_m2k'],r['changes_c'],r['same_fault_status']) for r in refinement], flush=True)
    print('STEADY_DEMAND', json.dumps(steady_cases), flush=True)
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
