# 비용 분석과 두 설계안

조회 기준일: 2026-08-28. 상태: `NOT_QUOTE_COMPLETE / NO_PURCHASE_AUTHORIZED`.

## 결론

신규 구매 200,000 KRW 목표는 현재 증거로 달성됐다고 볼 수 없다. 2채널 24 V E-stop/gate safety relay 후보 Dold `LG5925-48-61-24`의 공개가는 USD 143이고, Raspberry Pi Camera Module 3 standard는 USD 25부터다. 계획 비교용 환율 `1 USD=1,400 KRW`를 적용하면 각각 200,200 KRW와 35,000 KRW, 합계 235,200 KRW다. 이는 배송·세금·관세, E-stop actuator/contact block, contactor, fuse, sensor, heater, bearing, metal stock와 CNC를 모두 제외하고도 목표를 35,200 KRW 넘는다. [Dold safety relay 공개가](https://www.automationdirect.com/adc/shopping/catalog/safety/safety_relay_modules/2-channel_e-stop_-z-_safety_gate_relays/lg5925-48-61-24), [Camera Module 3 공식 제품 페이지](https://www.raspberrypi.com/products/camera-module-3/)

따라서 두 설계안을 다음처럼 분리한다.

## Target Budget Design

`target_budget_design.csv`가 source다. Pi와 Mega만 사용자 보유 진술에 따라 조건부 현금 0원으로 두며, PSU는 보유 진술이 있어도 label·terminal·부하검사와 replacement 판단 전 `TBD`다. Safety relay, contactor, E-stop, camera, driver, sensor, motor, profile와 metal stock은 프로젝트실에서 정확한 모델·정격이 확인된 재고가 있을 때만 0원 전략을 사용할 수 있다.

Target 설계는 기능이나 안전장치를 삭제하지 않는다. 다음 하나라도 재고로 충당되지 않으면 `BLOCKED_WITHOUT_VALIDATED_STOCK`이고, 200,000 KRW 목표를 포기하거나 scope가 아니라 예산을 재승인해야 한다.

- dual-channel monitored safety relay와 DC load에 맞는 contactor
- Camera/optic이 실제 `U95≤0.020 mm`를 만족하는 gauge
- pressure transducer와 독립 rupture/trip assembly
- 여섯 heater branch의 fuse, driver, sensor와 one-shot thermal fuse
- screw/barrel/die, cutter/shaft/plate와 필요한 가공

## Engineering Recommended Design

`engineering_recommended_design.csv`가 source다. 사용자 보유 Pi/Mega/PSU는 inspection 후 재사용할 수 있지만, 안전·압력·고온 부품은 정확한 MPN과 datasheet, landed price, lead time을 확정한다. 맞춤 cutter/screw/barrel은 quote-ready drawing package 이후 실제 CNC 견적을 받는다.

현재 총액은 `TBD_PENDING_DONOR_INVENTORY_MPN_SELECTION_AND_CNC_QUOTES`다. 총액을 임의 allowance로 채우지 않는다. 공개 후보가는 비교용 floor이며 구매 추천이나 회로 적합성 승인이 아니다. Safety relay 후보는 2채널, 24 VAC/VDC, 3 NO safety output과 1 NC monitoring output을 제공하지만 실제 contactor feedback, required performance level과 load category는 최종 risk assessment에서 확인한다.

## 비용 위험 순위

1. 18 mm screw/barrel/die의 deep-bore·honing·heat-treatment 가공
2. 세 파쇄단 cutter/rotor/shaft/plate와 balance·grinding
3. safety relay/contactor와 pressure relief/transducer
4. PET dryer의 금속 hopper, high-temperature airflow와 sensor
5. 충분한 torque의 24 V geared drive와 reduction
6. optical U95를 만족하는 close-up optic/mirror/backlight

`cost_evidence.csv`에는 조회일과 URL을, `cost_summary.json`에는 line count와 budget floor를 저장한다. `cost_rollup.csv`는 신규 구매·CNC/fabrication·print filament·project-lab replacement·donor replacement와 required/optional을 분리한다. 가격·재고는 주문 직전 다시 확인하고, 사용자 승인 없이 주문 또는 CNC 발주를 진행하지 않는다.
