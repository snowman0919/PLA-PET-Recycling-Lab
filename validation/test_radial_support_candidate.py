"""A review candidate must retain support contacts and actual service clearances."""
import copy,hashlib,sys
from pathlib import Path
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.radial_support_v08.cad_candidate import build_candidate,validate_candidate
from cad.freecad.final_v08 import generate as final

path=ROOT/'cad/parameters/final_v08.json'
prior=hashlib.sha256(path.read_bytes()).hexdigest(); params=copy.deepcopy(final.PARAMS)
items=build_candidate(); result=validate_candidate(items)
assert final.PARAMS==params
assert hashlib.sha256(path.read_bytes()).hexdigest()==prior
assert result['unexpected_count']==0
assert result['thermal_alignment_verified'] is False and result['load_capacity_verified'] is False
assert result['design_state']=='REVIEW_CANDIDATE_NOT_ACTIVE_MACHINE'
assert all(v>399.9 for v in result['support_face_contacts_mm2'].values())
assert result['service_gaps_mm']['TemperatureProbeRetainerT3']>=3-1e-6


def reject(rows):
    try: validate_candidate(rows)
    except (ValueError,KeyError): return
    raise AssertionError('invalid candidate geometry accepted')


def modified(name, operation):
    rows=[dict(r,shape=r['shape'].copy()) for r in items]
    target=next(r for r in rows if r['name']==name)
    operation(target)
    return rows


reject([r for r in items if r['name']!='ExtruderFrontSlidingGuide'])
reject(modified('MidRail320',lambda r:r['shape'].translate(App.Vector(0,0,-.1))))
reject(modified('ExtruderFrontSlidingGuide',lambda r:r.update(shape=r['shape'].fuse(
    Part.makeBox(18,8,12,App.Vector(294,125,376))).removeSplitter())))
assert final.PARAMS==params
assert hashlib.sha256(path.read_bytes()).hexdigest()==prior
print('RADIAL_SUPPORT_CANDIDATE_TEST_PASS cases=4 active_design_unchanged=1 physical=NOT_RUN',flush=True)
