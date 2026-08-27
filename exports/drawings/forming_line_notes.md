# 냉각·직경게이지·풀러 proof 도면 주기

## 기준 배치

- die 기준 냉각 시작 `X=0`, 총 440 mm, 3개 구간 각 146.667 mm
- 각 구간: 140×120 mm 외곽 덕트, donor/buy 80 mm fan envelope 1개
- 명목 횡류 2.5 m/s, 250 g/h 검증점 4.0 m/s
- gauge 중심: die에서 470 mm, enclosure 110×160×140 mm
- puller: Ø40×16 mm 동기 roller 2개, 명목 nip gap 1.50 mm, nip force 3–15 N
- line speed 0.5–1.6 m/min, drive encoder loop 100 Hz
- odometer: Ø30 mm, 최소 256 CPR, filament에 저하중 접촉
- 공통 frame 길이 760 mm, filament 기준 중심선 `Y=80`, `Z=100`

첫 hot-strand-facing 덕트는 sheet metal 또는 실제 strand 온도에 적합성이 확인된 재료로 만든다. PLA 출력물은 온도 검증 전 이 위치에 사용하지 않는다. Fan block, camera, mirror, backlight, gear와 encoder는 선정 전 공간 envelope이며 mounting hole·배선 굽힘·connector service가 포함된 공급자 도면으로 교체한다.

## 냉각 성능 gate

200 g/h, Ø1.75 mm의 계산 선속은 PLA 1.118 m/min, PET 0.997 m/min이다. 250 g/h에서는 PLA 1.397 m/min, PET 1.246 m/min이다. 440 mm tunnel의 계산상 puller 중심온도 gate 여유는 PLA worst case 54.5 mm, PET worst case 217.6 mm다. 이 값은 균일한 횡류와 깨끗한 열물성을 가정하므로 실제 duct loss, fan P–Q curve, 재생수지의 결정화도와 주변기류를 대체하지 않는다.

각 fan 구간에 독립 duty 조절과 removable flow straightener를 둔다. 열선풍속계로 strand 위치의 9점 velocity map을 만들고 fan failure/부분 막힘을 탐지한다. 냉각 후 PLA 중심 ≤50 °C, PET 중심 ≤70 °C를 puller 진입 gate로 사용한다. Ovality나 표면결함이 남으면 duty와 구간 위치를 먼저 조정하고, 수조는 전기부와 격리된 금속 변경안으로만 재검토한다.

## Dual-view 직경 게이지

Raspberry Pi Camera Module 3 standard 후보와 close-up optic, 45° front-surface mirror, 직교 backlight 2개를 불투광 enclosure에 넣는다. 목표 calibrated field width는 32 mm, full-resolution 처리율은 10 Hz다. Native 100 mm working distance는 약 35.48 px/mm이고 목표 macro field에서는 약 144 px/mm다.

1.50/1.75/2.00/2.50 mm traceable pin을 `gauge_calibration_fixture`에 장착해 두 광로의 homography, lens distortion, threshold와 scale을 각각 교정한다. `d_avg=(dx+dy)/2`, `ovality=|dx-dy|`를 동일 frame ID로 기록한다. 초기 ±0.05 mm 판정을 위한 요구는 `U95≤0.020 mm`다. 충족하지 못하면 공차를 느슨하게 보고하는 것이 아니라 optic, lighting, focus 또는 camera를 변경한다.

Window와 mirror는 먼지·수지 증기가 쌓이지 않게 양압 purge 또는 쉽게 분리되는 보호창을 둔다. Scratch 없는 승인 세정법과 교체주기를 기록한다. CAD의 검은 ray solid는 두 직교 측정선이 filament를 가로지르는 reference일 뿐 focus, telecentricity, mirror flatness나 측정불확도를 증명하지 않는다.

## Puller와 제어

Roller는 금속 shaft와 교체 가능한 compliant tyre를 사용하고 두 축을 gear/belt로 동기화한다. 1.50 mm gap은 1.75 mm filament의 의도된 압착 기준이며 실제 tyre 경도·압축률과 nip force는 coupon으로 정한다. Gauge는 nip upstream에 두며, drive encoder와 odometer 속도 차이로 slip을 검출한다.

Die–gauge 470 mm의 PLA 명목 수송지연은 25.23 s다. 선택 제어는 1 Hz mass-flow feed-forward + bounded Smith/filtered PI diameter loop이며 command slew는 0.02 m/min/s 이하로 제한한다. Camera dropout은 마지막 bounded command를 최대 3 s만 유지한 뒤 feed/extrusion을 pause한다. 최초 acceptance는 직경 1.75±0.05 mm, ovality ≤0.05 mm이고 충분한 실측 증거 뒤에만 ±0.03 mm 개선 gate를 연다.

## 제작·서비스·금지사항

Fan plate DXF는 1.5 mm sheet outline, Ø68.8 mm airflow opening과 M4 후보 hole만 담은 proof다. Sheet bend relief, flange, hem, gasket, fastener와 grounding tab은 제작 승인도에서 확정한다. Roller shaft, bearing seat, tyre, gear, spring adjuster와 interlocked guard는 STL로 제작하지 않는다.

덕트·보호창·roller tyre는 tool-less cleaning 또는 captive-fastener service가 가능해야 한다. 정비 전 heater, extruder와 puller를 모두 격리하고 strand 장력·잔류열·축회전이 0임을 확인한다. Guard open 상태에서는 puller가 energize되지 않아야 하며, 손으로 nip을 벌릴 수 있는 captive release를 둔다.
