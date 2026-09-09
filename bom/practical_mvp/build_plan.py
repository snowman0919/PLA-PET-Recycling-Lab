"""User-asset and fabrication allocation; not donor performance qualification."""
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
def target_material(part_id, policy):
    return 'ABS' if part_id in policy['housing']['abs_part_ids'] else policy['housing']['default_material']
def route(row, policy=None):
    policy = policy or json.loads((HERE/'policy.json').read_text())
    key = row['part_id']
    if row['make_or_buy'] == 'REFERENCE_ONLY':
        return 'REFERENCE_ONLY', 'No extra purchase quantity for an assembly alias'
    if key.startswith('PPR-C'):
        return target_material(key,policy)+'_PRINT_TARGET', 'Keep current geometry; material mismatch requires new slicing'
    if key in PRECISION:
        return 'RETAIN_FUNCTIONAL_PRECISION', 'Standard part first; retain cutting, pressure, fit and phase requirements'
    if key in CUT_FINISH:
        return 'CUT_DRILL_LOCAL_FINISH', 'Finish only functional bores/datums in plate or stock'
    if key in SHEET:
        return 'CUT_SHEET_DRILL_BEND', 'Keep specified metal barrier or load-path functions'
    if key in STOCK:
        return 'DONOR_OR_STANDARD_STOCK_REVIEW', 'Verify dimensions and rating; machine ends only if needed'
    if key in OUTER:
        return 'PLA_OUTER_SHELL_REDESIGN', 'Cold outer shell only; keep separate metal safety barriers'
    if key == 'FR-01':
        return 'RETAIN_2020_2040_FRAME', 'Reuse both available sections; measure cuttable lengths before cutting'
    if key == 'DRV-A42':
        return 'ALTERNATE_VARIANT_REVIEW', 'Only one selected motor adapter, never both'
    if row['make_or_buy'] in ('MIXED','MAKE_CNC'):
        return 'ASSEMBLY_OR_GROUP_REVIEW', 'Do not double-count assembly and children'
    if row['make_or_buy'] in ('BUY','BUY_TO_SPEC','BUY_CUSTOM','VERIFY_REUSE_OR_BUY'):
        return 'REUSE_FIRST_IF_COMPATIBLE', 'Asset presence alone is not interface compatibility'
    return 'REVIEW_EXISTING_ROUTE', 'No unreviewed process substitution'
def build(bom, prints, frame, policy):
    if set(policy['frame']['available_sections']) != {'2020','2040'} or policy['housing']['default_material'] != 'PLA':
        raise ValueError('Unexpected current manufacturing basis')
    ids=[r['part_id'] for r in bom]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate BOM IDs')
    routes=[dict(part_id=r['part_id'],description=r['description'],current_route=r['make_or_buy'],
                 proposed_route=route(r,policy)[0],scope_note=route(r,policy)[1],state='ALLOCATION_NOT_MANUFACTURING_APPROVAL') for r in bom]
    material=[]; rails=[]
    for row in prints:
        target=target_material(row['part_id'],policy)
        state='EXISTING_MATERIAL_MATCH_NOT_PHYSICALLY_VERIFIED' if target==row['material'] else 'MATERIAL_CHANGE_REQUIRES_RESLICE_AND_FIT'
        material.append(dict(part_id=row['part_id'],name=row['name'],quantity=row['quantity'],
                             current_material=row['material'],target_material=target,state=state))
    for row in frame:
        supported=row['stock'] in ('20x20 aluminum profile','20x40 aluminum profile')
        rails.append(dict(row,target_stock=row['stock'],change_state='RETAIN_SECTION_STOCK_LENGTH_PENDING' if supported else 'UNKNOWN_SECTION_REVIEW_REQUIRED'))
    return routes,material,rails
def main():
    paths=[ROOT/p for p in SOURCES]+[HERE/'policy.json',HERE/'donor_register.csv',Path(__file__)]
    before={str(p.relative_to(ROOT)):sha(p) for p in paths}
    policy=json.loads((HERE/'policy.json').read_text())
    bom,prints,frame=[read_csv(ROOT/p) for p in SOURCES]
    donors=read_csv(HERE/'donor_register.csv')
    if any(r['availability'] not in {'USER_REPORTED_AVAILABLE','CANDIDATE_UNINSPECTED','FAULT_REPORTED'} for r in donors):
        raise ValueError('Unsubstantiated donor verification')
    routes,material,rails=build(bom,prints,frame,policy)
    out=HERE/'generated';out.mkdir(exist_ok=True)
    for name,rows in [('manufacturing_route_review',routes),('abs_material_transition',material),('frame_transition',rails)]:
        write_csv(out/(name+'.csv'),rows,list(rows[0]) if rows else ['part_id','state'])
    summary={'state':policy['state'],'machine_release':'HOLD','physical_validation':'NOT_RUN','source_sha256':before,
             'bom_rows_reviewed':len(bom),'bom_count_not_purchase_quantity':True,'route_counts':dict(Counter(r['proposed_route'] for r in routes)),
             'printed_part_types':len(prints),'printed_piece_count':sum(int(r['quantity']) for r in prints),
             'material_changes_required':sum(r['current_material']!=r['target_material'] for r in material),
             'frame_section_changes_required':sum(r['change_state']=='UNKNOWN_SECTION_REVIEW_REQUIRED' for r in rails),'donor_register_rows':len(donors),'verified_donor_components':0,
             'cad_changed':False,'slicer_rerun':False,'structural_reanalysis':False,'purchases_performed':False}
    if any(sha(ROOT/p)!=v for p,v in before.items()):raise RuntimeError('Sources changed during allocation')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},ensure_ascii=False))
if __name__=='__main__': main()
