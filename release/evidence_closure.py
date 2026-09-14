"""Audit packaged physics dependencies; integrity is not physical acceptance."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'validation'))
from evidence_freshness import audit_evidence, MAP_KEYS, SCALAR_BINDINGS


def is_physics_report(relative: str) -> bool:
    return relative.endswith('.json') and (
        relative.startswith('analysis/final_validation/results/v0.8/')
        or relative == 'validation/results/final_v08_cad.json'
        or relative == 'simulation/openmodelica/results_v0.8/summary.json')


def declared_map(data) -> bool:
    if isinstance(data, dict):
        return any(key in MAP_KEYS or declared_map(value)
                   for key, value in data.items())
    if isinstance(data, list):
        return any(declared_map(value) for value in data)
    return False


def validate_evidence_closure(root: Path, sources: set[str]) -> dict:
    """Require every declared transitive input to exist in the payload itself."""
    roots, audits, missing = [], [], set()
    for relative in sorted(sources):
        if not is_physics_report(relative):
            continue
        data = json.loads((root / relative).read_text())
        if not (declared_map(data) or relative in SCALAR_BINDINGS):
            continue
        roots.append(relative)
        audit = audit_evidence(root, relative)
        if audit['status'] != 'CURRENT':
            raise ValueError('stale packaged physics dependency: ' + relative
                             + ': ' + repr(audit['issues'][:5]))
        missing.update(edge['target'] for edge in audit['edges']
                       if edge['target'] not in sources)
        audits.append(audit)
    if not roots:
        raise ValueError('no declared physics evidence roots in package')
    if missing:
        raise ValueError('unpackaged physics dependencies: ' + repr(sorted(missing)))
    return {'status': 'PACKAGED_PHYSICS_DEPENDENCIES_CURRENT',
            'root_count': len(roots), 'roots': roots,
            'unique_dependencies': len({e['target'] for a in audits for e in a['edges']}),
            'scope': 'Declared source/dependency hashes only; not all raw solver output',
            'physical_validation_state': 'NOT_RUN', 'fabrication_authorized': False}
