# v0.6 가열계 RFQ 및 수령검사 계약

## 고정 아키텍처

Barrel은 Z1 `TH-BH-02` 24 V/100 W/ID34/W40 1개와 Z2/Z3 `TH-BH-01` W45 2개, die는 `TH-DIE-01` Tempco custom 24 V/60 W/Ø6.50×39.50 Type CG cartridge 1개를 쓴다. 공정가열 정격합계는 360 W(15.0 A)다. TH-DIE-01은 HTL lead, OAL, MFR flange를 포함한 승인 도면이 필요하며 일반 3D-printer cartridge 대체를 금지한다. Ø35 stock band를 Ø34 barrel에 느슨하게 쓰거나 PTC를 barrel 주가열에 쓰는 대체는 금지한다.

Zone 중심은 barrel datum B에서 65.0/137.5/212.5 mm이며 band 범위는 B+45–85, 115–160, 190–235 mm다. Band free-state ID는34.10–34.20 mm, clamp의 usable split-closure travel은 최소1.00 mm다. Barrel OD33.97–34.00 mm에 필요한 최악 원주방향 closure는 π(34.20−33.97)=0.723 mm이고 잔여 travel은 최소0.277 mm다. 냉간 체결 뒤 split ±10°를 제외한 8개 등간격 sector에서 0.05 mm feeler가 5 mm 넘게 들어가지 않아야 한다. 이 검사는 수령 후 `NOT_RUN`이며 디지털 closure 계산만 PASS다. T1/T2/T3 bore는 B+95/170/245 mm, Ø3.20 +0.05/0, flat-bottom 깊이5.40 ±0.05이며 보수적 최소 ligament3.345 mm(요구≥3.32)를 유지한다. TH-TC-01은 Tempco MTA1 K/U/Q 맞춤품으로 Ø3.00±0.03, sheath25.40±0.25와 공급자 용접 stop collar를 쓴다. T1–T3 stop5.20±0.05, T4 stop10.00±0.05이며 TH-TCR-01 bridge와 2×M3로 고정한다. 직경 clearance는0.17–0.28 mm다. 승인도면·절연·인발·열응답 수령검사는 HOLD다.

각 100 W band cold resistance는 5.76 Ω ±10%, 60 W cartridge는 Tempco 공개 resistance tolerance -5/+10%를 적용한 9.12–10.56 Ω를 수령 시 20 ±2 °C에서 기록한다. Sheath-to-lead 절연, PE bond, lead strain relief, 실제 외형과 clamp closure를 검사한다. 24 V 저전압이라도 각 channel은 F-H1..F-H4 5 A branch fuse와 40–60 V VDS/10 A continuous thermal-capable MOSFET를 사용한다. 이 branch fuse는 과전류 보호이며 thermal cutoff가 아니다.

`TH-FUSE-01`은 총 3개를 조달한다. `TF-BARREL` 1개와 `TF-DIE` 1개를 저전류 K0 coil safety chain에 직렬로 설치하고, 동일 사양 1개는 교체용 spare로 보관한다. 어느 installed cutoff 하나라도 open되면 K0 coil energy가 제거되어 motor와 네 heater branch 전체가 함께 차단된다. Mega/MOSFET은 이 두 independent cutoff를 우회할 수 없으며 spare를 installed safety element로 계산하지 않는다.

모든 heater 구매와 energization은 사용자 승인 대상이다. 수령검사·절연검사·두 installed thermal cutoff continuity·K0 hard-cut 검증·무부하 단계가 끝나기 전 PSU에 연결하지 않는다.
