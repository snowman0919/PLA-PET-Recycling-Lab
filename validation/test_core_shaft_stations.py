"""실제 CAD 지지점이 반올림 없이 deck에 들어가는지 검사한다."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/final_validation'))
import run_calculix_v08 as solver

stations = json.loads((solver.INPUT/'geometry_manifest.json').read_text())['shredder_stations']
assert set(stations)=={'105','153'}
assert 'chain_sprocket_y_mm' in stations['153']
assert 'chain_sprocket_y_mm' not in stations['105']
for key,row in stations.items():
    for case in ('LC02','LC05'):
        if case=='LC05' and 'chain_sprocket_y_mm' not in row:
            try:
                solver.shaft_deck(case,24,row)
            except ValueError:
                continue
            raise AssertionError('chain load accepted on shaft without sprocket')
        for refinement in (24,48,96):
            deck,p,selected,coords = solver.shaft_deck(case,refinement,row)
            support_x = [(v-row['shaft_y_min_mm'])/1000 for v in row['bearing_y_mm']]
            for x in support_x:
                node = next(n for n,v in coords.items() if abs(v[0]-x)<1e-12)
                assert node in selected
                assert f'{node},2,3,0' in deck or f'{node},1,3,0' in deck
            load_y = sum(row['cutter_y_mm'])/len(row['cutter_y_mm']) if case=='LC02' else row['chain_sprocket_y_mm']
            expected = load_y-row['bearing_y_mm'][0]
            assert abs(p['load_position_from_front_bearing_mm']-expected)<1e-8
try:
    solver.shaft_deck('TYPO',24,stations['105'])
except ValueError:
    pass
else:
    raise AssertionError('unknown case accepted')
print('CORE_SHAFT_STATIONS_PASS')
