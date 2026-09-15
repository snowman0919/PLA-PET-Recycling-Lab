"""Overlay user-reported inventory, without approving electrical compatibility."""
import csv
import json
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def apply_reply(source_rows, reply):
    rows = deepcopy(source_rows)
    count = reply['stock']['BTS7960']['quantity']
    if type(count) is not int or count < 0:
        raise ValueError('BTS7960 quantity must be an explicitly reported nonnegative integer')
    for row in rows:
        row['latest_evidence'] = 'UNCHANGED_FROM_PREVIOUS_REQUEST'
        key = row['item_id']
        if key == 'CTRL-01':
            row.update(state='USER_REPORTED_AVAILABLE', lab_question='Mega 보유 회신 완료; 추가 구매 보류', latest_evidence='User-reported availability; quantity not enumerated')
        elif key == 'DRV-POWER':
            required = int(row['required_quantity'])
            row.update(confirmed_available_quantity=str(count), purchase_quantity=str(max(0, required-count)),
                       state='USER_COUNT_COVERS_PLAN_RATING_PENDING' if count >= required else 'USER_COUNT_SHORTFALL_RATING_PENDING',
                       lab_question='수량 확인 완료; 선정 모터에 대한 정격/방열/배선 확인만 남음',
                       latest_evidence='Explicit user count; one BTS7960 module per independent DC axis; not bench qualification')
        elif key == 'SAFETY-01':
            row.update(state='ESTOP_AVAILABLE_OTHER_PROTECTION_UNCONFIRMED', lab_question='E-stop 보유; 인터록/차단부/과열차단/퓨즈는 별도', latest_evidence='E-stop does not imply a complete safety set')
        elif key in ('DRV-SH', 'DRV-EX'):
            if reply['motor_ownership'] != 'NOT_PURCHASED_PURCHASE_CANDIDATES':
                raise ValueError('Motor ownership decision changed; review allocation')
            row.update(confirmed_available_quantity='0', purchase_quantity='', state='NOT_PURCHASED_OPTION_RESELECTION_REQUIRED',
                       lab_question='구매 전임을 확인; 정격토크와 속도를 맞춘 옵션 선정 후 주문',
                       latest_evidence='User explicitly confirmed no purchase; selected screenshot is not inventory')
            selected = reply.get('motor_design_reference', {}).get(key)
            if selected:
                row.update(state='DESIGN_REFERENCE_SELECTED_NOT_ORDERED', minimum_specification=selected['specification'], lab_question='선정 기준 모터의 최종 옵션/재고/장착 및 보호설정 확인; 주문은 별도 승인', latest_evidence=reply['motor_design_reference_source']+'; '+selected['model'])
        elif key in ('HEAT-BAND', 'HEAT-DIE'):
            row.update(state='PURCHASE_REQUIRED_SPEC_CONFIRMATION', lab_question='24V 제어히터 구매 규격 확정', latest_evidence='Integrated bed/PTC not allocated; no order placed')
    return rows


def main():
    source = ROOT/'sourcing/minimum_confirmation_bom.csv'
    with source.open(newline='', encoding='utf-8') as stream:
        source_rows = list(csv.DictReader(stream))
    reply = json.loads((HERE/'user_reply.json').read_text())
    rows = apply_reply(source_rows, reply)
    with (HERE/'remaining_confirmation_bom.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    print('STOCK_VIEW_UPDATED', len(rows), 'actual_orders=0')


if __name__ == '__main__':
    main()
