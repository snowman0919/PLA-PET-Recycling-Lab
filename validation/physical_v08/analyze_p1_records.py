#!/usr/bin/env python3
"""Fail-closed P1 inventory/receipt analyzer; never authorizes procurement or fabrication."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SURVEY_STATES = {
    'USER_REPORTED_AVAILABLE', 'MEASURE_STOCK',
    'CHECK_PROJECT_LAB_FIRST', 'CHECK_PROJECT_LAB_FIRST_THEN_BUY',
}
GGM_IDS = {'BUY-GGM-SH', 'BUY-GGM-EX'}
ALLOWED_RESULTS = {'PASS','NOT_FOUND','IDENTITY_PENDING','SEEN_NOT_MEASURED','NOT_RUN'}
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))

def verify_evidence(row, root: Path):
    rel=row.get('evidence_path','').strip(); digest=row.get('sha256','').strip().lower()
    if not rel or not SHA256_RE.fullmatch(digest):
        raise ValueError(f"{row['item_id']}: PASS requires evidence_path + sha256")
    path=(root/rel).resolve(); resolved_root=root.resolve()
    if resolved_root not in path.parents and path != resolved_root:
        raise ValueError(f"{row['item_id']}: evidence outside repository")
    if not path.is_file(): raise ValueError(f"{row['item_id']}: missing evidence {rel}")
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest: raise ValueError(f"{row['item_id']}: evidence sha256 mismatch")

def evaluate(rows, evidence_root: Path):
    by_id={r['item_id']:r for r in rows}
    if len(by_id)!=len(rows): raise ValueError('duplicate item_id')
    unresolved=[]; failures=[]; passed=[]
    for row in rows:
        result=row.get('result','').strip().upper()
        if result not in ALLOWED_RESULTS: raise ValueError(f"{row['item_id']}: invalid result {result!r}")
        if result=='PASS':
            for field in ('observed_quantity','condition','instrument_id','measured_at','operator'):
                if not row.get(field,'').strip(): raise ValueError(f"{row['item_id']}: PASS missing {field}")
            verify_evidence(row,evidence_root); passed.append(row['item_id'])
        elif result in {'NOT_FOUND','IDENTITY_PENDING','SEEN_NOT_MEASURED'}:
            failures.append(row['item_id'])
        if row.get('planned_state','').strip() in SURVEY_STATES and result=='NOT_RUN':
            unresolved.append(row['item_id'])
    missing_ggm=sorted(x for x in GGM_IDS if x not in by_id or by_id[x].get('result','').strip().upper()!='PASS')
    if failures: status='P1_REJECTED'
    elif unresolved: status='P1_SURVEY_INCOMPLETE'
    elif missing_ggm: status='P1_STOCK_SURVEY_PASS_GGM_PENDING'
    else: status='P1_RECORD_CHECK_PASS'
    return {
      'status':status,'stage_p1_pass':status=='P1_RECORD_CHECK_PASS',
      'hardware_authorization':False,'procurement_authorization':False,
      'passed_count':len(passed),'survey_unresolved':sorted(unresolved),
      'nonconforming_or_missing':sorted(failures),'ggm_receipt_pending':missing_ggm,
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('inventory',type=Path); ap.add_argument('--output',type=Path)
    args=ap.parse_args(); result=evaluate(read_csv(args.inventory),ROOT)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output: args.output.write_text(text,encoding='utf-8')
    print(text,end='')
    raise SystemExit(0 if result['status'] in {'P1_STOCK_SURVEY_PASS_GGM_PENDING','P1_RECORD_CHECK_PASS'} else 2)
if __name__=='__main__': main()
