"""Overlay the user's replies on the historical minimum-confirmation BOM."""
import csv, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def main():
    source=ROOT/'sourcing/minimum_confirmation_bom.csv'
    with source.open(newline='',encoding='utf-8') as stream: rows=list(csv.DictReader(stream))
    reply=json.loads((HERE/'user_reply.json').read_text())
    for row in rows:
        row['latest_evidence']='UNCHANGED_FROM_PREVIOUS_REQUEST'
        if row['item_id']=='CTRL-01':
            row.update(state='USER_REPORTED_AVAILABLE',lab_question='Mega 보유 회신 완료; 추가 구매 보류',latest_evidence='Current user item 4; exact quantity not enumerated')
        elif row['item_id']=='DRV-POWER':
            row.update(state='USER_REPORTED_AVAILABLE_COUNT_PENDING',lab_question='BTS7960 보유; 독립 DC축 2채널에 쓸 모듈 수량 확인',latest_evidence='Current user item 3; two modules not assumed')
        elif row['item_id']=='SAFETY-01':
            row.update(state='ESTOP_AVAILABLE_OTHER_PROTECTION_UNCONFIRMED',lab_question='E-stop 보유 회신 완료; NC interlocks/차단 relay/thermal cutoff/branch fuses는 별도',latest_evidence='Current user item 5; complete safety set not implied')
        elif row['item_id'] in ('DRV-SH','DRV-EX'):
            row.update(state='SCREENSHOT_OPTION_RATED_POINT_REVIEW',lab_question='신규 구매 전인지 이미 보유인지 확인; 같은 브랜드 정격표의 해당 옵션 적용성 확인',latest_evidence='source_rows.json and result.json; no automatic acceptance')
        elif row['item_id'] in ('HEAT-BAND','HEAT-DIE'):
            row.update(state='PURCHASE_REQUIRED_SPEC_CONFIRMATION',lab_question='bed 내장 열선/PTC는 공용 주가열원 제외; 24V 제어히터 구매 규격 확정',latest_evidence='Current user item 2; no order placed')
    target=HERE/'remaining_confirmation_bom.csv'
    with target.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    assert reply['stock']['BTS7960']['quantity'] is None
    print('STOCK_VIEW_UPDATED',len(rows),'purchase_count=0')
if __name__=='__main__': main()
