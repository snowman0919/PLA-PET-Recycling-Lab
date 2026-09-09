# HS-R1-S2 HOLD 폐쇄 시험계획

상태: PREPARATION_ONLY. 현재 실측은0건이다. 아래는 구매·가공·가열·본체 장착 승인이 아니다. 실행은 재료와 치구 정격, 독립 차단, 보호판, 계측 및 단계별 승인을 검토한 뒤 진행한다.

## 중요한 신규 하중
기존 sheet 해석에 축방향 sliding 마찰의 하중 방향이 빠져 있었다. `run_axial_drag.py`가 기존 mesh/support에서 해당 방향을 따로 계산했다. 기존1,100 MPa 문구만으로 재료를 승인하지 않는다. `results/axial_drag.json`의1,222 MPa 부근 요구도 mu0.25·sheet별 균등분담·선형 중첩 가정의 값이지 확정된 설계 허용값이 아니다.

## M01 — 재료 식별·가공·온도별 강도
시험편과 부품마다 lot/heat number, 공급 두께, 압연방향, 냉간가공 상태, 열처리 순서/실제 furnace chart, 최종 가공/표면 공정을 결박한다. 3 mm CH900을 annealed stock+단순 시효로 자동 대체하지 않는다.

동일 lot 및 최종 열처리를 거친 witness coupon으로 지정 실사용 온도에서 RP0.2, 인장강도, 연신율과 가능한 E를 시험한다. 20/100/200/300°C는 현재 수치검토의 표본 온도이며 실제 시험 온도/공차/수량은 시험기관과 확정한다. 원주 방향 flexure에는 압연/직각 방향을 모두 검토한다. ASTM E21은 기관이 정식 방법과 적합성을 확인할 참고기준이다. 공개 개요만 읽고 준수 인증을 주장하지 않는다.

성적서에는 원시 force/strain/temperature trace, 계측 교정·불확도, coupon 치수와 파단 위치, 열 노출시간을 포함한다. 열처리 완료 뒤 shoe radius/web/slot/평면도/edge 상태를 측정한다. ATI의 A→RH/TH0.4% 팽창을 보정값으로 자동 사용하지 않는다.

판정: 공급 lot/두께/상태/온도/방향이 맞고 불확도를 뺀 RP0.2가 최신 결합 하중 요구를 충족하는지 검토한다. 공개 전형값, 상온값, 다른 두께/상태의 논문은 합격 성적서가 아니다. 정적 RP0.2만으로 피로·열이완까지 닫지 않는다.

## F01 — 실제 조립체의 마찰·stick-slip
실제 접촉쌍, 표면조도/가공방향, 질화/코팅상태, 청정/오염상태, 윤활 유무를 고정한다. 상용 마찰계수표를 실측 대체로 쓰지 않는다. 기준 가열에 윤활제를 임의로 추가하지 않는다.

힘 센서는 양방향 교정하고, 지그/가이드 자체의 empty tare를 같은 방향·속도·온도에서 별도 측정한다. 실제 조립체를 천천히 왕복시키며 time/travel/force, 두 횡방향 중심, 각 carrier 반력, sheet 양면과 inner/outer 및 mandrel 온도를 동시에 기록한다. 시작 peak와 steady drag를 구분하고 reversal 직후 stick-slip을 버리지 않는다.

`friction_summary()`는 부호 있는 pull에서 같은 방향 tare를 빼고 불확도를 더해 drag 상한을 계산한다. 두 방향의 BREAKAWAY와 STEADY가 모두 필요하다. 실제 접촉 법선력 합을 독립 측정하지 않았다면 mu는 NOT_IDENTIFIABLE로 남긴다. carrier의25 N 횡하중은 슈 preload 법선력 합이 아니다.

본체에 필요한 것은 우선 drag의 직접 측정 상한이다. mu를 산출하지 못해도 개별 carrier drag와 총 drag는 설계 입력으로 쓸 수 있다. 다만 각 sheet의 분담·접촉변형/온도구배는 따로 검토해야 한다. 기존300 N은 protocol 중단 경계이지 입증된 사용 정격이 아니다. 현재 재료/하중 검토로 더 낮은 중단값이 필요하면 더 낮은 값을 적용한다.

## H01 — 고온 위치 유지·이완·온도장
재료/표면 조건이 확정되지 않으면 가열하지 않는다. 독립 thermal cutoff, 금속 차폐, 치구 고정 및 사용자 승인을 먼저 확인한다. 온도시험은 승인된 저온 단계부터 진행하며, 이전 문서의2°C/min와 양면 온도차10°C는 계측 불확도를 포함한 잠정 경계다. 고온에서 차가운 spring에 mandrel을 강제로 끼우지 않는다.

같은 deflection을 유지한 상태에서 온도/시간별 shoe force 또는 carrier drag 감소, 중심 이동과 endplay를 기록한다. ASTM E328 공개 개요가 다루는 응력이완과 같은 현상이나, 이 조립체가 표준 시험편이라고 주장하지 않는다. 참고 노출시간10/60/240분 및 냉각 반복은 초기 특성파악용이고, 예상 duty·보관기간·수명에 대한 최종 요구는 별도로 확정해야 한다.

국부 온도는 mandrel, spring inner/outer, 앞/뒤 sheet, carrier, thrust bearing 주변을 구분한다. 한 개 평균 온도를 전체 접합부 온도로 대체하지 않는다. 가열 전·유지 중·냉각 후의 drag/centre/preload를 비교한다. 정상 운전 온도까지 PASS해도 독립 차단기의 설정 온도/overshoot 또는 장기 피로가 자동 검증되지는 않는다.

판정: 최신 모델을 측정된 온도장·강성·잔류 접촉력으로 다시 풀고, sheet contact loss/stack contact와 centre budget, 재료 강도·이완·피로를 함께 검토한다. 응력이 낮다는 이유로 미끄러짐 마찰을0으로 지정하지 않는다.

## A01 — 본체 추력 경로와 접합부
압력 사례는6 MPa x bore16.22 mm 단면적=약1,239.775 N이다. 이는 정의된 blocked-die 계산 사례이며 전류센서로 실제 압력을 측정했다는 뜻이 아니다. 최대 관찰/상한 drag를 retainer 경로에 불리한 방향으로 합산한다. 현재mu0.25 가정의 두 carrier drag237.059 N를 더하면1,476.834 N다. screw bearing 경로에는 무조건 같은 drag를 이중 가산하지 않는다.

실제 경로를 분리해 변위와 반력을 측정한다: screw shoulder→NSK51102→thrust plate→profile, barrel shoulder→rear datum/retainer→체결부→profile, 별도 sliding carrier→frame. 51102 카탈로그는 단방향 thrust bearing이므로 반대방향 하중이 생기는 경우 실제 지지·retention 경로를 추가로 확인한다.

전체 경로 시험은 HS-R1 치구에1.48 kN을 가하는 시험이 아니다. 별도로 정격·차폐·고정이 검토된 무가압 cold load fixture에서 교정된 load cell과 변위계로 실시한다. 승인된 하중의0/25/50/75/100% 단계에서 반력 합·모멘트 평형, 접합면 opening, bolt elongation/preload, 축/배럴 변위와 unload residual을 기록한다. 구체적 proof 하중 배수와 허용변위는 최종 설계 담당자가 확정하기 전 자동 적용하지 않는다.

조임토크만으로 예압을 실측했다고 하지 않는다. 직접 장력 또는 적격한 bolt elongation 방법을 사용하며, 온도별 bolt/접합부 열팽창과 잔류예압을 기록한다. `bolt_screen()`은 초기예압+외력 분담을 proof capacity와 함께 비교한다. 접합면이 열리면 일정 stiffness fraction 가정은 더 이상 유효하지 않다.

## 증거 묶음 및 해제 경계
`evidence_packet_template.json`은 performed=false이며 실제 시험 자료는 gitignored measurements/에 둔다. source/cache/certificate의 존재나 hash만으로 진위를 인증하지 않는다. `review_packet()`은 기록 무결성만 판정하며 machine_release=HOLD를 유지한다.

M01은 정확한 lot/상태/두께/온도 강도와 최종 치수, F01은 실측 drag/centre, H01은 실측 온도장/이완/주기적 유지성, A01은 실제 양방향 경로·예압·정격을 각각 닫는다. 한 항목의 성공을 나머지 HOLD 해제로 사용하지 않는다. 신뢰할 수 있는 raw trace, 교정 자료, 적용범위, 독립 검토와 승인이 모였을 때만 해당 범위의 판정을 승격한다.
