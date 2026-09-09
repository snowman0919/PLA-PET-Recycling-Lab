"""Build a proposal from observed BOMs; never certify donor parts or new CAD."""
from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = ('exports/final/bom/BOM.csv', 'exports/final/print/print_manifest.csv',
           'exports/fabrication/frame_cut_list.csv')
PRECISION = set('CUT-01 CUT-05 CUT-05R DRV-03 DRV-03R EX-SCR-01 EX-BAR-01 EX-DIE-01 EX-DIE-03 DRV-F01P'.split())
CUT_FINISH = set('CUT-03 CUT-10 EX-MT-01 EX-MT-02 EX-MT-03 EX-THR-01 DRV-02 FD-CP-01'.split())
SHEET = set('CUT-04 CUT-07 CUT-08 DRV-01 DRV-A60 DRV-GD-01 EX-SH-01 EX-DIE-04 EX-DIE-05 TH-TCR-01'.split())
STOCK = set('CUT-02 CUT-06 CUT-09 FM-AX-01 FM-GA-01 SP-AX-01 SP-SH-01 SP-MM-01 SP-TR-01'.split())
OUTER = set('CT-ENC-01 FD-BIN-01 IN-HOP-01'.split())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))
def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
def route(row):
    key = row['part_id']
    if row['make_or_buy'] == 'REFERENCE_ONLY':
        return 'REFERENCE_ONLY', 'No additional purchase or manufacture quantity'
    if key.startswith('PPR-C'):
        return 'ABS_PRINT_TARGET', 'Re-slice with chosen ABS; check fit, load and thermal location'
    if key in PRECISION:
        return 'RETAIN_FUNCTIONAL_PRECISION', 'Use suitable standard part first; retain cutting/pressure/fit/phase requirements'
    if key in CUT_FINISH:
        return 'CUT_DRILL_LOCAL_FINISH', 'Blank from plate/stock; finish only functional bores and datums; geometry review required'
    if key in SHEET:
        return 'CUT_SHEET_DRILL_BEND', 'Retain specified metal thickness and local tolerances; not a billet-CNC default'
    if key in STOCK:
        return 'DONOR_OR_STANDARD_STOCK_REVIEW', 'Match shaft, length, rating and interface; local end machining only as needed'
    if key in OUTER:
        return 'ABS_OUTER_SHELL_REDESIGN', 'Separate outer cover from any structural, pressure, fire or fragment barrier'
    if key == 'FR-01':
        return '2020_FRAME_TARGET', 'Legacy 2040 rails need support-span/joint redesign before replacement'
    if key == 'DRV-A42':
        return 'ALTERNATE_VARIANT_REVIEW', 'Do not procure both motor adapters; confirm selected drive first'
    if row['make_or_buy'] in ('MIXED', 'MAKE_CNC'):
        return 'ASSEMBLY_OR_GROUP_REVIEW', 'Do not add assembly quantity to child-part quantities'
    if row['make_or_buy'] in ('BUY', 'BUY_TO_SPEC', 'BUY_CUSTOM', 'VERIFY_REUSE_OR_BUY'):
        return 'REUSE_FIRST_IF_COMPATIBLE', 'Retain safety/rating/interface checks; availability alone is not compatibility'
    return 'REVIEW_EXISTING_ROUTE', 'No unreviewed material or process substitution'
def build(bom, prints, frame, policy):
    if policy['frame']['default_section'] != '2020' or policy['housing']['default_material'] != 'ABS':
        raise ValueError('Unexpected user manufacturing target')
    ids = [r['part_id'] for r in bom]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate BOM IDs')
    routes = [dict(part_id=r['part_id'], description=r['description'], current_route=r['make_or_buy'],
                   proposed_route=route(r)[0], scope_note=route(r)[1], state='PROPOSAL_NOT_MANUFACTURING_RELEASE') for r in bom]
    material = [dict(part_id=r['part_id'], name=r['name'], quantity=r['quantity'], current_material=r['material'],
                     target_material='ABS', state='ABS_MATERIAL_CHANGE_REQUIRES_RESLICE_AND_FIT' if r['material'] != 'ABS' else 'ABS_ALREADY_LISTED_NOT_PHYSICALLY_VERIFIED') for r in prints]
    rails = [dict(r, target_stock='20x20 aluminum profile', change_state='SECTION_AND_JOINT_REVIEW_REQUIRED') for r in frame if r['stock'] != '20x20 aluminum profile']
    return routes, material, rails
def main():
    paths = [ROOT/p for p in SOURCES] + [HERE/'policy.json', HERE/'donor_register.csv', Path(__file__)]
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    policy = json.loads((HERE/'policy.json').read_text())
    bom, prints, frame = [read_csv(ROOT/p) for p in SOURCES]
    donors = read_csv(HERE/'donor_register.csv')
    if any(r['availability'] not in {'USER_REPORTED_AVAILABLE', 'CANDIDATE_UNINSPECTED', 'FAULT_REPORTED'} for r in donors):
        raise ValueError('Sourcing plan must not invent verified donor stock')
    routes, material, rails = build(bom, prints, frame, policy)
    out = HERE/'generated'; out.mkdir(exist_ok=True)
    write_csv(out/'manufacturing_route_review.csv', routes, list(routes[0]))
    write_csv(out/'abs_material_transition.csv', material, list(material[0]))
    write_csv(out/'frame_transition.csv', rails, list(rails[0]) if rails else ['part_id','target_stock','change_state'])
    summary = {'state':'TARGET_ACCEPTED_IMPLEMENTATION_PENDING', 'machine_release':'HOLD',
               'physical_validation':'NOT_RUN', 'source_sha256':before,
               'bom_rows_reviewed':len(bom), 'bom_count_not_purchase_quantity':True,
               'route_counts':dict(Counter(r['proposed_route'] for r in routes)),
               'printed_part_types':len(prints), 'printed_piece_count':sum(int(r['quantity']) for r in prints),
               'non_abs_types':sum(r['material'] != 'ABS' for r in prints),
               'non2020_rail_rows':len(rails), 'non2020_rail_pieces':sum(int(r['quantity']) for r in rails),
               'donor_register_rows':len(donors), 'verified_donor_components':0,
               'cad_changed':False, 'slicer_rerun':False, 'structural_reanalysis':False,
               'price_savings':'NOT_ESTABLISHED', 'purchase_performed':False}
    if any(sha(ROOT/p) != value for p,value in before.items()): raise RuntimeError('Inputs changed during plan build')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},ensure_ascii=False))
if __name__ == '__main__':
    main()
