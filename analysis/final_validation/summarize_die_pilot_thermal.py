"""기존 lumped OpenModelica 온도의 pilot 유격 진단; 접합면 qualification 아님."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(folder):
    output = ROOT/'analysis/final_validation/results/v0.8/die_pilot_thermal.json'
    output.write_text(json.dumps({'status':'INCOMPLETE', 'physical_validation_state':'NOT_RUN'})+'\n')
    cases = []
    paths = []
    for name in ('PilotPET', 'PilotPETDieOpen', 'PilotPETBarrelOpen', 'PilotPETBarrelStuck', 'PilotPETDieStuck', 'PilotPETWeakJoint', 'PilotPETVeryWeakJoint'):
        path = folder / (name+'_res.csv')
        rows = list(csv.DictReader(path.open()))
        times = [float(r['time']) for r in rows]
        assert len(set(times)) >= 3601 and times[0] == 0 and times[-1] == 3600
        assert all(0 <= b-a <= 1.000001 for a,b in zip(times,times[1:]))
        temperatures = [(float(r['T3']),float(r['Tdie'])) for r in rows]
        assert all(math.isfinite(float(r[k])) for r in rows for k in ('T1','T2','T3','Tdie'))
        assert all(float(r['fuseBlown']) in (0,1) for r in rows)
        injected = {'PilotPETDieOpen':('powerDie',0), 'PilotPETBarrelOpen':('power3',0),
                    'PilotPETBarrelStuck':('power3',100), 'PilotPETDieStuck':('powerDie',60),
                    'PilotPETWeakJoint':('powerDie',0), 'PilotPETVeryWeakJoint':('powerDie',0)}
        if name in injected:
            field, expected = injected[name]
            assert all(math.isclose(float(r[field]),expected,abs_tol=1e-9) for r in rows), (name,field)
        peak_temperature = max(float(r[k]) for r in rows for k in ('T1','T2','T3','Tdie'))
        gaps = [(19.05*(1+12e-6*(d-20))-19*(1+12e-6*(b-20)))/2 for b,d in temperatures]
        deltas = [b-d for b,d in temperatures]
        cases.append({'case':name, 'radial_gap_mm':[min(gaps),max(gaps)],
                      'T3_minus_Tdie_k':[min(deltas),max(deltas)],
                      'injected_power_check':'PASS' if name in injected else 'NOT_APPLICABLE',
                      'peak_zone_temperature_c':peak_temperature,
                      'fuse_ever_blown':any(float(r['fuseBlown'])!=0 for r in rows)})
        paths.append(path)
    paths += [Path(__file__).resolve(), ROOT/'simulation/openmodelica/scripts/run_die_pilot_screen.mos',
              ROOT/'simulation/openmodelica/PLA_PET_Recycler/Systems/ThermalExtruderSystem.mo']
    result = {'status':'HOLD', 'physical_validation_state':'NOT_RUN', 'cases':cases,
              'scope':'Nominal19/19.05 mm fit; assumed alpha12e-6/K. Lumped T3/Tdie; coupling0.8 default, weak0.08 and very weak0.008 W/K diagnostic assumptions, no local joint/contact qualification.',
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(cases,indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
