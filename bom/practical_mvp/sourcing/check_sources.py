"""Validate reviewed source records; no checkout or orders."""
import csv,hashlib,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def read(name):
    with (HERE/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def validate(parts,prices):
    if len({r['item_id'] for r in parts})!=len(parts):raise ValueError('Duplicate item')
    sources={r['source_id'] for r in prices}
    if len(sources)!=len(prices):raise ValueError('Duplicate source')
    for row in parts:
        if row['confirmed_available_quantity'] or row['purchase_quantity']:raise ValueError('Stock reply not supplied yet')
        if set(row['source_ids'].split('|'))-sources:raise ValueError('Unknown source')
        if not row['minimum_specification'] or not row['lab_question']:raise ValueError('Missing decision input')
    for row in prices:
        value=row['display_price_krw'];shipping=row['shipping_krw']
        if value and (not value.isdigit() or int(value)<=0):raise ValueError('Quote missing is not zero price')
        if shipping and (not shipping.isdigit() or int(shipping)<0):raise ValueError('Invalid shipping')
        if row['tax_basis']=='QUOTE_REQUIRED' and value:raise ValueError('Unquoted price populated')
        if row['availability']=='VERIFIED_IN_STOCK' or row['evidence_scope']=='CHECKOUT_VERIFIED':raise ValueError('Live checkout not performed')
    return {'status':'SOURCE_RECORDS_CONSISTENT','confirmation_groups':len(parts),'price_observations':sum(bool(r['display_price_krw']) for r in prices),'total_cost':'NOT_ESTABLISHED','purchases':0,'physical_validation':'NOT_RUN'}

def main():
    parts,prices=read('minimum_confirmation_bom.csv'),read('price_observations.csv')
    result=validate(parts,prices)
    result['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'minimum_confirmation_bom.csv',HERE/'price_observations.csv')}
    (HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
