# v0.5.1 가열계 RFQ 및 수령검사 계약

## 고정 아키텍처

Barrel은 `TH-BH-01` 24 V/100 W/ID34/W45 mica band 3개, die는 `TH-DIE-01` 24 V/60 W/Ø6×38 cartridge 1개를 쓴다. 공정가열 정격합계는 360 W(15.0 A)다. Ø35 stock band를 Ø34 barrel에 느슨하게 쓰거나 PTC를 barrel 주가열에 쓰는 대체는 금지한다.

Zone 중심은 barrel datum B에서 67.5/137.5/212.5 mm이며 band 범위는 B+45–90, 115–160, 190–235 mm다. T1/T2/T3 blind bore는 B+95/170/245 mm, Ø3.20 +0.05/0, 깊이6.0 ±0.1이며 melt bore까지 명목 ligament 2.9 mm다. T4는 die Ø3.20 blind12, T5는 hopper metal wall을 측정한다. Probe junction은 ungrounded여야 하며 sheath-to-junction insulation을 수령 검사한다.

각 100 W band cold resistance는 5.76 Ω ±10%, 60 W cartridge는 9.60 Ω ±10%를 수령 시 20 ±2 °C에서 기록한다. Sheath-to-lead 절연, PE bond, lead strain relief, 실제 외형과 clamp closure를 검사한다. 24 V 저전압이라도 각 channel branch fuse와 40–60 V VDS/10 A continuous thermal-capable MOSFET를 사용한다. Mega는 저주파 time-proportioning을 수행하지만 independent thermal fuse를 우회할 수 없다.

Hopper PTC는 35×21×5 class 4개 시작 형상이며 외부 predry를 대체하지 않는다. PTC 1개의 cold current, 10/30/60분 전력과 spreader 평형온도를 먼저 측정하여 4–8개 범위를 확정한다. PTC는 aluminum spreader와 grounded keeper 사이에 절연·compliant pad로 고정하고 printed part에 직접 닿지 않는다.

모든 heater 구매와 energization은 사용자 승인 대상이다. 수령검사·절연검사·thermal fuse continuity·무부하 단계가 끝나기 전 PSU에 연결하지 않는다.
