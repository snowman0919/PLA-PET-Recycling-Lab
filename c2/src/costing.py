"""Full incremental procurement coverage. A missing quotation is not zero cost."""
from __future__ import annotations
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def evaluate(rows: list[dict], soft_limit_KRW: float=100000):
    known=0.;missing=[]
    for r in rows:
        if r['owned_verified']:
            continue
        price=r.get('landed_line_KRW')
        if price is None:
            missing.append(r['item_id'])
        elif price<0:
            raise ValueError('Negative cost')
        else:
            known+=price
    return dict(soft_limit_KRW=soft_limit_KRW,known_incremental_KRW=known,
                unknown_cost_lines=missing,complete=not missing,
                total_KRW=known if not missing else None,
                within_budget=(known<=soft_limit_KRW) if not missing else None,
                status='INCOMPLETE_QUOTES' if missing else ('WITHIN_SOFT_LIMIT' if known<=soft_limit_KRW else 'OVER_SOFT_LIMIT'),
                not_included_free_assumptions=[])


def main():
    rows=json.loads((ROOT/'bom/cost_ledger.json').read_text())
    (ROOT/'results/cost_status.json').write_text(json.dumps(evaluate(rows),indent=2)+'\n')
    print(json.dumps(evaluate(rows),indent=2))

if __name__=='__main__':main()
