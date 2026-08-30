# v0.6 조달 폐쇄 상태

Revision: `implementation-crosssolver-v0.6` / 기준일: 2026-08-30

## 결론

- 조건부 계획 소계: **173,729 KRW** (`<=180,000`, PASS)
- 예비비 20,000 KRW 포함 절대 계획액: **193,729 KRW** (`<=200,000`, 여유 6,271 KRW)
- 검증 견적/영수증 소계: **0 KRW — NOT_ESTABLISHED**
- 실제 project-lab 재고: **NOT_VERIFIED**
- 외부 RFQ 회신: **NOT_REQUESTED / NOT_RECEIVED**
- 발주·결제: **수행하지 않음**

0 KRW verified subtotal은 무상 장비를 뜻하지 않는다. 증거 적격 quote/receipt가 한 건도 없다는 뜻이다. 기존 공개 vendor 후보와 planning allowance는 `bom/purchase_candidates.csv`와 v0.5.1 문서에 보존되지만 가격·납기 확정 증거로 승격하지 않는다.

## 준비된 실제 입력 양식

- `inventory_evidence_v0.6.csv`: 사진·라벨·실측 없이는 claimed quantity를 비워 둔다. donor motor 전압, 전류, 토크, 축경을 추측하지 않는다.
- `rfq_register_v0.6.csv`: CNC, heater, motor, chain의 전송 준비 scope. 외부 메시지 발송 권한과 사용자 승인 없이 전송하지 않았다.
- `verified_budget.csv`: receipt/quote evidence가 연결될 때만 `QUOTE_VERIFIED`/`RECEIPT_VERIFIED`로 집계한다.

## 상한 위험

공개 후보 가격으로 추정한 sensor/MOSF/PTC/heater delta는 현재 조건부 상한 여유 6,271 KRW보다 크다. 따라서 재고 확인과 실제 RFQ 없이는 200,000 KRW 실구매 가능성을 주장할 수 없다. 안전품(E-stop, interlock, branch/thermal fuse)을 삭제하거나 donor를 0원으로 가정해 상한을 맞추지 않는다.

## 다음 사용자 승인 지점

1. `inventory_evidence_v0.6.csv`에 physical evidence를 연결한다.
2. RFQ-01–08 중 보낼 범위를 승인한다. 이는 견적 요청 승인이지 발주 승인이 아니다.
3. quote 회신의 물품·세금·배송·납기·유효기간을 기록하고 conditional/verified budget을 다시 계산한다.
4. 각 구매는 별도 사용자 승인 후에만 실행한다.
