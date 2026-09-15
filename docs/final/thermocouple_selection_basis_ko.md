# TH-TC-01 맞춤 열전대 선정 근거

## 디지털 구매 계약

배럴 T1–T3과 다이 T4는 Tempco `MTA1` 맞춤 MI thermocouple assembly를 기준품으로
지정한다. 제조사가 실제 MPN을 견적 시 부여하므로 아래는 주문 옵션과 승인도면 계약이며
재고품 MPN이 아니다.

- MTA1 옵션: `K / 2 / M / A / Q / U / B / B / Y / 0 / H`
- Type K, single element, 96% MgO, Alloy 600 sheath, ungrounded junction
- sheath `Ø3.00 ±0.03 mm`, 전체 길이 `25.40 ±0.25 mm`
- 12 in lead, 482 °C fiberglass with stainless overbraid, split leads
- strain relief spring, compression fitting 없음, 538 °C ceramic high-temperature potting
- 공급자 용접 304SS stop collar: OD `6.00 ±0.05`, 두께 `0.80 ±0.05`
- T1–T3 tip-to-collar `5.20 ±0.05 mm`; T4 tip-to-collar `10.00 ±0.05 mm`
- flat closed tip, junction은 tip에서 `1.0 mm` 이내이며 sheath와 전기적으로 절연

Tempco 공개 MTA1 표는 Type K, ungrounded, Q=`3.0 mm ±0.03`, Alloy 600, fiberglass
lead와 538 °C potting을 조합할 수 있음을 명시한다. stop collar와 짧은 tip-to-collar
치수는 공개 표준품이 아니므로 제조사 승인도면에 별도 기재되어야 한다. 승인도면이 없으면
구매하지 않는다.

## 기계 인터페이스

EX-BAR-01 보어 `3.20–3.25 mm`와 probe `2.97–3.03 mm`의 최악 diametral
clearance는 `0.17–0.28 mm`다. 보어 깊이 `5.35–5.45 mm`와 T1–T3 stop
`5.15–5.25 mm`의 tip gap은 `0.10–0.30 mm`다. EX-DIE-01도 같은 직경
clearance를 쓰며 보어 깊이 `11.95–12.05 mm`와 T4 stop `9.95–10.05 mm`는
바닥 여유 `1.90–2.10 mm`를 남긴다.

각 stop collar는 `TH-TCR-01` 304SS t1.5 bridge와 2×M3 A4-80 screw로 눌러
인발을 막는다. 배럴은 각 센서 양쪽 axial pitch10의 M3-6H depth4, 다이는 센서
양쪽 pitch10의 M3-6H depth4를 쓴다. MI sheath 자체를 set screw로 누르거나
임의 절단·swage·납땜하지 않는다.

## 승인도면·수령 합격기준

- 위 치수, 접점 형식, sheath/transition/lead 개별 연속온도와 polarity를 승인도면으로 확인
- 20 °C에서 sheath-to-junction insulation `≥100 MΩ @ 100 VDC`; 제조사 시험전압 확인
- 장착 전/후 연속성 및 얼음점·비등점 비교, Class 1 또는 더 엄격한 오차 확인
- bridge 체결 0.5 N·m 후 냉간 및 270 °C 열사이클 뒤 axial pull `20 N`, 이동 `≤0.10 mm`
- 실제 barrel coupon에서 기준 센서 대비 정상상태 편차 `≤2 °C`, 90% step response
  `≤30 s`; `ProbeThermalContact.mo`의 접촉/스템 비 `Gc/Gs≥121.5`에 해당하는
  수령시험 경계다. 해석 모델 PASS는 실물 시험을 대신하지 않는다.

## 공식 근거

- [Tempco MTA1 custom assembly](https://www.tempco.com/Tempco/Resources/14-Temp-Sensors-Resources/MTA1TCAssemblyCatalogPages.pdf)
- [Tempco metric MI cable](https://www.tempco.com/wp-content/uploads/Resources/14-Temp-Sensors-Resources/MICableforSensorsCatalogPages.pdf)
- [Tempco MTA1 product page](https://www.tempco.com/Products/Temperature-Sensors/Thermocouples/Style-MTA1-MI-Cable-TC-Assembly.htm)

현재 상태는 디지털 치수·고정·수령시험 계약 `PASS`, 제조사 승인도면·견적·구매·수령·
열응답 시험 `HOLD/NOT_RUN`이다. AliExpress 판매자 회신은 대체품 평가에만 사용하며
이 계약보다 약한 자료로 승인 MPN을 바꾸지 않는다.
