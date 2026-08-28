# 비용 분석과 두 설계안

조회 기준일: 2026-08-28. 상태: `NOT_QUOTE_COMPLETE / NO_PURCHASE_AUTHORIZED`.

## 결론

신규 구매 200,000 KRW 목표는 현재 증거로 달성됐다고 볼 수 없다. 현재 `PRIMARY_CANDIDATE` 다섯 행의 수량 반영 planning floor만 426,165 KRW이며 cap을 226,165 KRW 초과한다.

| Part ID | 후보 | 수량 반영 floor |
|---|---|---:|
| SAF-REL-001 | Dold `LG5925-48-61-24` | 200,200 KRW |
| SAF-EST-001 | Omron `A22E-M-02` 2NC | 143,001 KRW |
| ELE-BUCK-001 | MEAN WELL `DDR-30G-5` 5 V/6 A | 42,644 KRW |
| GAU-CAM-001 | Camera Module 3 standard | 35,000 KRW |
| GRN-BRG-001 | `6203-2RS-GLD` 2개 | 5,320 KRW |

이는 배송·세금·관세, fuse link coordination, 전체 sensor/heater, metal stock와 CNC를 포함하지 않은 **불완전 하한**이다. [Dold 후보](https://www.automationdirect.com/adc/shopping/catalog/safety/safety_relay_modules/2-channel_e-stop_-z-_safety_gate_relays/lg5925-48-61-24), [Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/), [A22E-M-02](https://www.digikey.kr/en/products/detail/omron-automation-and-safety/A22E-M-02/549568), [DDR-30G-5](https://www.digikey.kr/en/products/detail/mean-well-usa-inc/DDR-30G-5/8681204), [6203-2RS-GLD](https://www.digikey.kr/en/products/detail/mechatronics-bearing-group/6203-2RS-GLD/9608381)

실배치 병행을 위해 추가한 다섯 개 qualification/sizing 후보까지 합치면 현재 MPN이 있는 10개 BOM 행의 engineering candidate floor는 **5,240,261 KRW**다. 이 값도 전체 시스템 견적이 아니며 구매 승인이 아니다.

| 추가 Part ID | 실제 배치 수량 | 후보 | 수량 반영 floor |
|---|---:|---|---:|
| SAF-CON-001 | 2 | ABB `AFS30-30-22-11` | 885,892 KRW |
| SAF-FUS-HLD | 14 | Eaton `CHCC1DU` holder only | 1,863,960 KRW |
| ELE-HTR-DRV | 6 | Sensata `84137860` DC SSR | 977,676 KRW |
| ELE-HTR-HS | 2 | Sensata `HS103DR` | 445,704 KRW |
| CTL-ENC-001 | 1 | nVent HOFFMAN `MAS0405021R5` | 640,864 KRW |

`CHCC1DU`는 현재 DigiKey 재고 0 관측이므로 실제 조달 대안이 필요하다. 퓨즈 link와 main holder는 전류 실측 전까지 별도 placeholder다.

따라서 두 설계안을 다음처럼 분리한다.

## Target Budget Design

`target_budget_design.csv`가 source다. Pi와 Mega만 사용자 보유 진술에 따라 조건부 현금 0원으로 두며, PSU는 보유 진술이 있어도 label·terminal·부하검사와 replacement 판단 전 `TBD`다. Safety relay, contactor, E-stop, camera, driver, sensor, motor, profile와 metal stock은 프로젝트실에서 정확한 모델·정격이 확인된 재고가 있을 때만 0원 전략을 사용할 수 있다.

Target 설계는 기능이나 안전장치를 삭제하지 않는다. 다음 하나라도 재고로 충당되지 않으면 `BLOCKED_WITHOUT_VALIDATED_STOCK`이고, 200,000 KRW 목표를 포기하거나 scope가 아니라 예산을 재승인해야 한다.

- dual-channel monitored safety relay와 Tower A/Tower B용 DC load 안전 contactor 2개
- Camera/optic이 실제 `U95≤0.020 mm`를 만족하는 gauge
- pressure transducer와 독립 rupture/trip assembly
- 여섯 heater branch의 fuse, driver, sensor와 one-shot thermal fuse
- screw/barrel/die, cutter/shaft/plate와 필요한 가공

## Engineering Recommended Design

`engineering_recommended_design.csv`가 source다. 사용자 보유 Pi/Mega/PSU는 inspection 후 재사용할 수 있지만, 안전·압력·고온 부품은 정확한 MPN과 datasheet, landed price, lead time을 확정한다. 맞춤 cutter/screw/barrel은 quote-ready drawing package 이후 실제 CNC 견적을 받는다.

현재 총액은 `TBD_PENDING_DONOR_INVENTORY_MPN_SELECTION_AND_CNC_QUOTES`다. 총액을 임의 allowance로 채우지 않는다. 공개 후보가는 비교용 floor이며 구매 추천이나 회로 적합성 승인이 아니다. Safety relay 후보는 2채널, 24 VAC/VDC, 3 NO safety output과 1 NC monitoring output을 제공하지만 K2A/K2B series EDM feedback, required performance level과 load category는 최종 risk assessment에서 확인한다. AFS30 후보는 ABB가 요구하는 DC 차단 pole 직렬구성을 반영하고 실측 branch current로 재정격해야 한다.

## 구매처 증거와 marketplace 경계

`procurement_routes.csv`는 BUY 32행 모두에 primary/alternate channel과 필수 검증 항목을 지정한다. `cost_evidence.csv`는 28개 후보·거절 기록을 담으며, 실제 가격 페이지가 확보된 BUY Part ID는 21개다. 사람이 읽는 링크 표는 `procurement_candidates.md`다.

- DigiKey: traceable MPN·datasheet·재고가 있는 전자/안전/전원 후보에 우선 사용한다. 60,000 KRW 미만 주문의 20,000 KRW 배송과 CPT 세금은 개별 단가에서 분리한다.
- 디바이스마트: 국내 VAT 포함가·준비기간을 기록한다. 확인된 24 V fan과 PT100은 alternate/partial이며, AC-output `CKRD2420` SSR은 24 VDC heater용에서 명시적으로 거절했다.
- AliExpress: Playwright Chromium으로 6004/6203 bearing, M5 isolator, 24 V fan 검색 결과를 수집했다. seller·variant·배송·세금·정품성이 확정되지 않아 전부 `SAMPLE_ONLY`다.
- E-stop, safety relay/contactor/interlock, thermal fuse, heater driver, melt-pressure/rupture 부품은 AliExpress 금지다.

## 비용 위험 순위

1. 18 mm screw/barrel/die의 deep-bore·honing·heat-treatment 가공
2. 세 파쇄단 cutter/rotor/shaft/plate와 balance·grinding
3. safety relay/contactor와 pressure relief/transducer
4. PET dryer의 금속 hopper, high-temperature airflow와 sensor
5. 충분한 torque의 24 V geared drive와 reduction
6. optical U95를 만족하는 close-up optic/mirror/backlight

`cost_evidence.csv`에는 조회일·URL·MOQ/pack·재고·배송/세금 상태·수집 방법을, `cost_summary.json`에는 line count와 선택된 budget floor를 저장한다. `cost_rollup.csv`는 신규 구매·CNC/fabrication·print filament·project-lab replacement·donor replacement와 required/optional을 분리한다. 가격·재고는 주문 직전 다시 확인하고, 사용자 승인 없이 주문 또는 CNC 발주를 진행하지 않는다.
