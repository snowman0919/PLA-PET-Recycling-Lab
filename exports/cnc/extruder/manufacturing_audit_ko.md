# 16 mm x 16 L/D screw/barrel 제조성 audit — RFQ 기준

## Controlling geometry

STEP은 3D 견적/간섭 기준, SVG와 본 문서는 치수·GD&T 기준이다. STL/DXF는 CAM reference이며 공차를 대체하지 않는다. 공급사는 임의로 clearance나 heat treatment를 변경하지 않는다.

- 모든 치수는 mm, 표면조도는 Ra µm, 별도 표기 없는 선형치수 공차는 ±0.10 mm, 각도는 ±0.5°다.
- 재료는 SCM440 KS D3867/JIS G4105 또는 동등 chemical/mechanical certificate를 제출한다. Supplier stock allowance는 임의이지만 추천 rough blank는 screw Ø22 x330, barrel solid/seamless Ø42 x295다.
- 임의 대체재·공정·공차 이탈은 deviation list에 써서 회신하며 무응답은 수락으로 간주하지 않는다.

## EX-SCR-01 screw

- SCM440, normalized blank → rough turn → QT 28–32 HRC → centres 유지.
- Total 316.0 ±0.10. Rear drive 0–35, thrust journal 35–55, neck 55–60, active 60–316. Active 256.0; single-start RH; pitch 16.00 ±0.03; flight land 1.60 ±0.05. Flight은 두 active-section end plane과 만나며 end burr R0.2 max, undercut·weld build-up은 금지한다.
- Zone 8D/4D/4D. Root Ø10.88 feed, linear compression, Ø14.08 meter. Flight OD Ø15.92 -0.02/0.
- Drive Ø12 h6 x35 with KS/DIN 4 x4 key, shaft keyseat 4 P9 wide x2.5 +0.10/0 deep; thrust journal Ø15 h6 x20; neck root Ø10.88 x5. Datum A는 Ø12/Ø15 journal의 common axis이며 shoulder/end face는 A에 직각도 0.03. Flight start angle은 active start에서 key centre plane 기준 0° ±5°.
- 4-axis flight mill leaving 0.15 mm grind/polish allowance. Root/flank Ra≤1.6 µm, flight OD Ra≤0.8 µm.
- Gas nitride 0.30–0.50 mm effective case, surface 900–1100 HV0.3; mask drive/thrust journals and keyseat. Final flight-OD grind between retained centres. Nitriding distortion 후 journal h6/TIR을 최종 확인한다.
- Flight OD TIR ≤0.05 over active 256; drive-to-flight concentricity ≤0.03; straightness ≤0.05/256. No weld repair.

## EX-BAR-01 barrel

- SCM440 solid/seamless blank, QT 28–32 HRC. OD Ø34.00 ±0.05, length 280.00 ±0.05. Rear face=Datum B, front face=Datum C, final bore axis=Datum D. Assembly에서 B는 screw active start와 일치하고 screw tip은 C 뒤 24.0 ±0.2에 위치한다.
- Bore after final hone Ø16.20 +0.02/0, Ra≤0.4–0.8 µm. Bore straightness ≤0.05/256 and concentricity to OD/register ≤0.05.
- Feed opening은 축방향 18.00 ±0.10 x chord width 20.00 ±0.10, rear edge B+12.00 ±0.10. Port centre plane을 전면 bolt pattern의 0° 각도 기준으로 삼는다. Bore-intersection edge R0.5 ±0.2; screw flight 위 sharp edge 금지.
- Front die interface는 4x M4 x0.7-6H, full thread depth 8 minimum, tap-drill depth 11 minimum, PCD26.00 ±0.05 at 45/135/225/315° ±0.2° from feed-port centre plane이다. Ø3.3 tap drill 기준 nominal outer ligament 2.35 mm, bore-side ligament 3.25 mm이고 M4 major envelope 기준으로도 각각 2.0/2.9 mm 이상이다. 나사·counterbore가 OD 또는 bore로 breakthrough하면 FAIL이다. B/C faces은 D에 직각도 0.03; OD concentricity to D ≤0.05.
- Rough turn/deep drill → 600–650 °C stress relieve(재료 공급사 표준 cycle, certificate 기록) → datum-face/OD finish → semi-finish ream/hone leaving 0.05–0.08 mm on diameter → feed port/thread machine → gas nitride 0.30–0.50 mm, ≥900 HV0.3 → final hone. Effective case after final hone is ≥0.25 mm.
- Report bore at 20/140/260 mm and roundness ≤0.02 at each station. Front/rear face perpendicularity 0.03 to bore axis.

## Matched clearance and inspection

Specified drawing-limit diametral clearance is 0.28–0.32 mm and radial clearance is 0.14–0.16 mm. Supplier는 20 ±2 °C에서 screw OD를 active z=20/140/240, barrel ID를 B+20/140/260의 서로 직교하는 2개 방향으로 측정하고 최소/최대 clearance가 범위 안인 pair만 표식한다. Air/bore-gauge report, hardness/case-depth certificate, material certificate, Ra trace, pitch check과 TIR inspection sheet은 RFQ deliverable이다.

## DFM decision

SCM440 was selected over stainless for local availability, machinability and nitriding cost. PET-temperature metal compatibility is adequate for a research coupon, but corrosion/wear life is not certified. `EX-CPN-SCR` 3-pitch와 `EX-CPN-BAR` 60 mm process coupon만 먼저 견적·가공할 수 있다. Coupon의 치수·경도·case depth·Ra가 본 도면을 만족하고 공급사 DFM이 닫힌 뒤에도 Gate-3 cold proof 전 full screw/barrel 발주는 HOLD다. No physical result is claimed here.

Coupon controlling dimensions: EX-CPN-SCR L48.00 ±0.05, three RH pitches 16.00 ±0.03, OD/root/land와 열처리는 EX-SCR-01 feed zone과 동일하며 journal은 없다. EX-CPN-BAR L60.00 ±0.05, OD Ø34.00 ±0.05, final ID Ø16.20 +0.02/0, bore Ra/case는 EX-BAR-01과 동일하다. 두 coupon의 ends는 axis에 0.03 이내 수직이다. Coupon은 matched pair로 표식하고 실측 diametral clearance 0.28–0.32 mm여야 한다.

## EX-DIE connected open-die assembly

`EX-DIE-01`은 barrel 전면에 4×M4×45 class 10.9 bolt와 `EX-DIE-05` annealed copper gasket로 체결되는 40×40×48 SCM440 body다. Ø8 수평 유로와 Ø8 수직 유로는 X20/Z0에서 실제로 교차하며, 공급사는 교차부를 borescope로 확인하고 burr·step을 R0.3 이하로 제거한다. Barrel-side에는 Ø15.90×2 `EX-DIE-02` seven-hole 304 breaker가 Ø16.20×3 seat에 갇힌다. Bottom에는 OD Ø11.90×14 `EX-DIE-03` 17-4PH H900 insert가 Ø12.00×14 seat에 들어가고 Ø3.00×10 land와 4 mm conical transition으로 open discharge한다. 직접 hot path에 polymer는 없다.

Body sealing face flatness는 0.03, melt channel Ø8 H9, insert seat Ø12.00 +0.03/0, breaker seat Ø16.20 +0.05/0이다. Heater bore Ø6.20 H9 through와 sensor bore Ø3.20 +0.05/0 blind12는 유로와 bolt를 관통하지 않는다. Body는 6-face datum machining → intersecting drill/ream → stress relieve → final seat/face → gas nitride → sealing face lap 순서다. Channel/seat에는 weld repair와 plating을 금지한다.

`EX-DIE-04`는 304 stainless t1.5의 교환식 sacrificial retainer다. 두 10 mm wide ×2.5 mm long web, 265 °C 보수 항복강도 150 MPa와 Ø11.9 insert에서 Ø3 orifice를 뺀 투영면적을 쓴 단순 탄성 항복 screening은 약 4.32 MPa이며 normal 3 MPa와 motor-trip equivalent 6 MPa 사이를 겨냥한다. 이는 release 값이 아니다. 동일 lot coupon 3개를 shielded heated hydraulic fixture에서 265 °C 조건으로 시험해 최초 영구변형/우회 개방이 3–6 MPa이고 fragment/ejection이 없을 때만 사용한다. Retainer는 insert를 포획한 채 우회 유로를 열어야 하며, grounded metal shield와 remote first-hot-test 없이는 가열하지 않는다. Full die assembly 역시 process coupon, relief coupon 및 Gate-3 전 `HOLD_PROCESS_COUPON_AND_GATE3`다.
