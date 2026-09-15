"""Current provisional strength floor; integrity is not material certification."""
from pathlib import Path, PurePosixPath
import hashlib,json,math

def minimum_yield_floor(experiment):
    root=Path(experiment).resolve()
    base=json.loads((root/'derived_requirements.json').read_text())
    extra=json.loads((root/'qualification/results/axial_drag.json').read_text())
    normal=json.loads((root/'sliding_envelope.json').read_text())
    for document in (base,extra):
        bindings=document.get('source_sha256')
        if not isinstance(bindings,dict) or not bindings: raise ValueError('Missing strength provenance')
        for name,expected in bindings.items():
            relative=PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name: raise ValueError('Unsafe strength provenance')
            path=(root/name).resolve()
            if not path.is_relative_to(root): raise ValueError('Outside strength source root')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected: raise ValueError('Stale strength source: '+name)
    old=base['proposed_certificate_minimum_mpa_at_actual_service_temperature']
    previous=base['conservative_combined_screen_requirement_mpa']
    stated=extra['strength_requirement_including_assumed_drag_mpa']
    if extra.get('assumed_mu')!=.25 or len(extra.get('runs',[]))!=2: raise ValueError('Unsupported drag-basis revision')
    peaks=[r['result']['max_von_mises_mpa'] for r in extra['runs']]
    values=[old,previous,stated,normal['maximum_total_normal_force_per_carrier_n'],*peaks]
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in values): raise ValueError('Invalid strength data')
    recomputed=previous+2*max(peaks)*normal['maximum_total_normal_force_per_carrier_n']*.25/6/25
    if not math.isclose(stated,recomputed,rel_tol=1e-10): raise ValueError('Strength result arithmetic mismatch')
    return max(float(old),float(math.ceil(recomputed)))
