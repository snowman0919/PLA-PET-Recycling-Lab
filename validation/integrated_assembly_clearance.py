"""Audit live GGM assembly solids, not the compact base or a stale BRep cache."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE_MM3 = 0.01
REPAIRED_PAIRS = [
    ('FeederAgitatorDriveShaft', 'FeederAugerSpringPin'),
    ('FeederHousing', 'BarrelBandHeaterZ1'),
    ('TemperatureProbeRetainerT1', 'ExtruderFrontSlidingGuide'),
    ('SpoolBearingPlateFront', 'SpoolerTachSensorEnvelope'),
    ('DownDieBody', 'TemperatureProbeT4'),
    ('DownDieBody', 'TemperatureProbeRetainerT4'),
    ('TemperatureProbeT4', 'TemperatureProbeRetainerT4'),
]
for zone in range(1, 4):
    REPAIRED_PAIRS += [('Barrel', f'TemperatureProbeRetainerT{zone}'),
                      (f'TemperatureProbeT{zone}', f'TemperatureProbeRetainerT{zone}')]
REPAIRED_PAIRS.append(('BarrelBandHeaterZ1', 'TemperatureProbeRetainerT1'))
MINIMUM_GAPS_MM = {
    ('FeederHousing', 'BarrelBandHeaterZ1'): 2.0,
    ('TemperatureProbeRetainerT1', 'ExtruderFrontSlidingGuide'): 3.0,
}


def reference_interfaces():
    rules = {}
    def add(a, b, maximum, reason):
        rules[frozenset((a, b))] = (maximum, reason)
    add('Spool', 'SpoolCore', 155100, 'Purchased spool/core solid envelope; bore omitted')
    for target, maximum in [('SpoolSpindle', 8300), ('PPR-C09_SpoolAdapterFront', 24400),
                            ('PPR-C09_SpoolAdapterRear', 24400)]:
        add('Spool', target, maximum, 'Purchased spool envelope; fit requires received core dimensions')
    for target, maximum in [('SpoolSpindle', 8300), ('PPR-C09_SpoolAdapterFront', 13400),
                            ('PPR-C09_SpoolAdapterRear', 13400)]:
        add('SpoolCore', target, maximum, 'Generic solid core LOD; not a machined core drawing')
    for end, rail in [('Front', 'MidRail320'), ('Rear', 'GGM_HotRearRail')]:
        for side in ('Front', 'Rear'):
            add(rail, f'HotMountBolt{end}{side}', 400,
                'M5 fastener in solid profile reference; slot/clearance machining not represented')
    for side in ('L', 'R'):
        add('GGM_ExMotorRail', 'GGM_M5_EX_Mount'+side, 240,
            'M5 T-nut joint in solid profile LOD; slot void omitted')
    for y in (318, 376):
        add('ExtruderRearRetainer', f'RearRetainerM4_{y}', 49,
            'M4 major diameter in 3.3 mm tap-drill representation; thread engagement only')
    return rules

def reference_roles_match(left, right):
    roles = {
        'Spool': {'purchased_reference_envelope'},
        'SpoolCore': {'purchased_reference_lod'},
        'SpoolSpindle': {'manufactured_or_stock'},
        'PPR-C09_SpoolAdapterFront': {'manufactured_or_stock'},
        'PPR-C09_SpoolAdapterRear': {'manufactured_or_stock'},
        'MidRail320': {'manufactured_or_stock'},
        'GGM_HotRearRail': {'purchased_reference_lod'},
        'GGM_ExMotorRail': {'purchased_reference_lod'},
        'ExtruderRearRetainer': {'manufactured_or_stock'},
    }
    for row in (left, right):
        expected = ({'purchased_fastener'} if row['name'].startswith(
            ('HotMountBolt', 'GGM_M5_', 'RearRetainerM4_')) else roles.get(row['name'], set()))
        if row.get('classification') not in expected:
            return False
    return True


def boxes_overlap(a, b):
    x, y = a.BoundBox, b.BoundBox
    return all(min(getattr(x, k+'Max'), getattr(y, k+'Max')) >
               max(getattr(x, k+'Min'), getattr(y, k+'Min')) + 1e-7 for k in 'XYZ')


def audit(items):
    by = {r['name']: r for r in items}
    if len(by) != len(items):
        raise ValueError('duplicate assembly object identity')
    invalid = [n for n, r in by.items() if r['shape'].isNull() or
               not r['shape'].isValid() or not r['shape'].Solids]
    if invalid:
        raise ValueError('invalid solid: '+repr(invalid))
    policy = reference_interfaces()
    hits, unexpected, gaps = [], [], []
    for index, left in enumerate(items):
        for right in items[index+1:]:
            a, b = left['shape'], right['shape']
            if not boxes_overlap(a, b):
                continue
            volume = a.common(b).Volume
            if volume <= TOLERANCE_MM3:
                continue
            key = frozenset((left['name'], right['name']))
            maximum, reason = policy.get(key, (0, 'unclassified solid interference'))
            allowed = (key in policy and reference_roles_match(left, right) and
                       volume <= maximum + TOLERANCE_MM3)
            hit = {'left': left['name'], 'right': right['name'], 'volume_mm3': volume,
                   'left_class': left['classification'], 'right_class': right['classification'],
                   'reference_overlap_only': allowed, 'limit_mm3': maximum, 'reason': reason,
                   'component_roles_match': reference_roles_match(left, right)}
            hits.append(hit)
            if not allowed:
                unexpected.append(hit)
    for a, b in REPAIRED_PAIRS:
        volume = by[a]['shape'].common(by[b]['shape']).Volume
        if volume > TOLERANCE_MM3:
            raise ValueError(f'repaired interface regressed: {a}/{b}: {volume}')
    for (a, b), minimum in MINIMUM_GAPS_MM.items():
        distance = by[a]['shape'].distToShape(by[b]['shape'])[0]
        gaps.append({'left': a, 'right': b, 'gap_mm': distance, 'minimum_mm': minimum})
        if distance + 1e-6 < minimum:
            raise ValueError(f'clearance regressed: {a}/{b}: {distance}')
    if unexpected:
        raise ValueError('unexpected integrated overlaps: '+repr(unexpected))
    return {'status': 'GGM_NOMINAL_COLLISION_POLICY_PASS', 'object_count': len(items),
            'pairs': len(items)*(len(items)-1)//2, 'tolerance_mm3': TOLERANCE_MM3,
            'repaired_interface_checks': len(REPAIRED_PAIRS), 'clearances': gaps,
            'reference_overlaps': hits, 'unexpected_count': 0,
            'physical_validation_state': 'NOT_RUN', 'fabrication_authorized': False,
            'scope': 'Nominal rigid solids only; reference overlaps disclosed, not removed by blind cutting',
            'not_qualified': ['received extrusion slot and fastener fit', 'assembly/tool access',
                              'service and motion swept volumes', 'retainer fasteners and pull test',
                              'thermal performance after geometry changes']}

def geometry_source_paths():
    paths = set((ROOT/'cad/freecad/compact').glob('*.py'))
    paths.update((ROOT/'cad/freecad/drive_v08').glob('*.py'))
    paths.update((ROOT/'cad/freecad/final_v08').glob('*.py'))
    paths.update(ROOT/'cad/parameters'/name for name in
                 ('baseline.json', 'final_v08.json', 'ggm_frame_revision.json'))
    return sorted(paths)


def main():
    sys.path[:0] = [str(ROOT), str(ROOT/'cad/freecad/drive_v08')]
    from cad.freecad.final_v08.generate import final_objects
    from cad.freecad.drive_v08.assembly import integrated_objects
    items, _ = integrated_objects(final_objects())
    result = audit(items)
    sources = geometry_source_paths() + [Path(__file__).resolve()]
    result['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sources}
    output = ROOT/'analysis/frame_v08/results/integrated_clearance.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'], 'objects', result['object_count'], 'pairs', result['pairs'],
          'repaired', result['repaired_interface_checks'], 'reference_overlaps',
          len(result['reference_overlaps']), 'physical=NOT_RUN')


if __name__ == '__main__':
    main()
