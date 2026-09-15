# P5 screw/barrel 공정 coupon 실행안

P5의 목적은 full screw/barrel을 먼저 사는 것이 아니라 **공급업체가 우리 Ø16 hot-zone 공정을 실제로 만들 수 있는지 EX-CPN-SCR 1개와 EX-CPN-BAR 1개로 확인하는 것**이다. 이 문서는 견적 전송·주문·가공 승인이 아니며, 현재 상태는 `DESIGN_ONLY_NOT_ORDERED`다.

## 1. 공급사 응답을 먼저 닫는다

공급사는 SCM440/JIS G4105 MTC, Q&T 28–32 HRC, gas nitriding, 후처리 screw grind/barrel final hone, 검사 장비와 최종 책임주체를 명시한다. Coupon 가격/납기와 full-part 가격/납기를 분리한다. baseline SCM440의 245–270 °C 물성은 있으면 받되, 없다는 이유만으로 P5를 자동 탈락시키지 않는다. 대신 재료/열처리 deviation을 제안하면 그때는 고온 물성 및 재해석이 필수다.

## 2. coupon만 제작한 뒤 비파괴 검사를 먼저 한다

EX-CPN-SCR은 L48.00±0.05, pitch 16.00±0.03, flight OD15.90–15.92, root OD10.88±0.03, land1.60±0.05다. EX-CPN-BAR은 L60.00±0.05, OD34.00±0.05, final bore ID16.20–16.22다. 18–22 °C에서 측정하고, critical 치수는 측정값±U95/MPE가 limit 안에 들어와야 한다.

Screw OD는 세 pitch에서, barrel ID는 axial 20/40 mm의 직교 두 방향에서 기록한다. `minimum clearance = min(barrel ID)-max(screw OD)`, `maximum clearance = max(barrel ID)-min(screw OD)`로 계산하고 둘 다 0.28–0.32 mm 범위여야 한다.

조도는 destructive section 전에 측정한다. Screw flight OD Ra≤0.8 µm, root/flank Ra≤1.6 µm, barrel bore Ra0.4–0.8 µm를 기록한다.

## 3. 열처리/질화 증거

Q&T core hardness는 28–32 HRC다. Screw surface는 900–1100 HV0.3, barrel surface는 ≥900 HV0.3다. Screw effective case는 **최종 grind 후 0.30–0.50 mm**를 확인한다. Barrel은 gas-nitride 공정 목표 0.30–0.50 mm를 certificate에 남기고, **final hone 후 실제 잔존 effective case ≥0.25 mm**를 microsection에서 확인한다. Final hone 제거량도 기록한다. HRC/HV/case-depth report에는 적용 method/standard, test load와 effective-case 판정 정의를 함께 적어 공급사마다 다른 정의를 같은 숫자로 오인하지 않게 한다.

Microsection/case-depth 검사는 마지막에 한다. 즉 치수·clearance·Ra를 모두 확보한 다음 coupon을 절단해 측정한다. Coupon이 이 단계에서 파괴되는 것은 정상이며 설치용 부품으로 재사용하지 않는다.

## 4. 판정

`analyze_p5_records.py`는 수치/문서 완전성만 offline으로 검사한다. `NUMERIC_RECORD_CHECK_PASS`가 나와도 full part 주문 승인이 아니다. P5 PASS 검토 후에도 EX-SCR-01/EX-BAR-01 발주는 별도의 사용자 승인이 있어야 한다.

## 5. 공급사 문의 review package

`python3 validation/physical_v08/build_p5_inquiry_package.py`로 `dist/PPR-v0.8-P5-COUPON-CAPABILITY-INQUIRY-REVIEW.zip`을 재생성한다. 이 ZIP은 `REVIEW_ONLY_NOT_SENT`이며 coupon-only geometry만 포함한다. 생성/검토는 전송·견적 수락·주문 승인이 아니다.
