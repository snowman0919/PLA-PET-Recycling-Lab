# 냉각·직경게이지·풀러 coupon 시험계획

## 1. 정적 형상·보호 점검

- 세 덕트 구간 총길이 440 mm, fan/strand 중심, 470 mm gauge 중심과 puller 중심선을 측정
- 모든 sheet edge, fan opening, nip/gear/shaft guard와 보호접지 연속성 확인
- Ø1.50/1.75/2.00/2.50 mm pin을 전체 경로에 통과시켜 접촉·막힘·광로 차폐 확인
- captive nip release와 guard interlock의 de-energized 동작 확인

합격 기준: rigid reference 간 의도하지 않은 접촉 0, filament 경로의 sharp edge 0, guard 제거 상태에서 motor 인가 불가, 모든 금속 덕트·frame의 접지 연속성이 승인 기준 이내다.

## 2. 공기유동·열 coupon

Strand 위치의 각 3개 구간에서 3×3 velocity map을 만들고 fan duty에 대한 2.5/4.0 m/s 점을 확인한다. 단일 fan off, 30% inlet blockage와 주변 cross-draft를 주입한다. 승인된 단일재질 PLA/PET를 200/250 g/h에서 각각 30 min 운전해 die, 각 구간 출구, gauge와 puller 직전의 표면 및 추정 중심온도, 직경·ovality를 기록한다.

합격 기준: 정상 운전에서 모든 점이 목표 유속의 ±15% 안, dead zone 없음, PLA puller 중심 ≤50 °C, PET ≤70 °C, 표면 tack/roller marking/냉각 유발 ovality 없음. Fan off 또는 막힘 때 3 s 이내 경고 후 안전한 feed/puller 상태로 전환한다.

## 3. 광학 교정·불확도

교정된 1.50/1.75/2.00/2.50 mm pin을 X/Y 광로의 field 중앙과 각 모서리에서 각각 30 frame 측정한다. Homography, distortion, scale와 threshold를 독립 fit하고 repeatability, pin 인증 불확도, 온도 drift, focus drift와 algorithm bias를 합성해 U95를 계산한다. Clear/black/translucent strand, 오염 보호창, 진동, stray light와 1–5 s frame dropout을 별도 주입한다.

합격 기준: 전 field의 bias ≤0.010 mm, `U95≤0.020 mm`, 두 축 frame ID 동기, 10 Hz 처리율 유지, ovality 기준물 판별 성공. Dropout 3 s까지 bounded command 유지, 그 이후 feed/extrusion pause 및 manual recovery log가 남아야 한다.

## 4. Puller·slip 시험

Nip force를 3/6/9/12/15 N에서 교정하고 0.5–1.6 m/min ramp를 실행한다. Drive encoder 속도와 독립 odometer를 traceable length reference에 비교하며 dry/warm/분진 tyre 조건, 조인트와 직경 step을 통과시킨다. Locked roller와 filament break를 안전하게 모사한다.

합격 기준: steady speed error ≤1%, drive–odometer slip ≤2% 정상, 3% 초과 1 s에서 경고, 5% 초과 또는 jam에서 latched stop. Filament flattening, surface bite와 permanent set이 acceptance 직경/ovality를 넘지 않는다.

## 5. 폐루프 재료 시험

각 재료에서 180 s 후 mass flow +8%, 480 s 후 −6% step을 넣어 최소 900 s 운전한다. 1 Hz로 mass flow, command/actual line speed, 두 직경, ovality, camera state, odometer slip, fan duty와 온도를 기록한다. 최초 gain은 계산값보다 낮게 시작하고 stability를 증명한 뒤만 높인다.

합격 기준: 30 min 안정구간에서 직경 1.75±0.05 mm, ovality ≤0.05 mm, overshoot로 인한 jam/neck/break 0, dropout fail-safe 성공. 물리시험에서 RMS·최대오차·settling을 보고하며, 충분한 lot와 장시간 결과가 쌓인 뒤에만 1.75±0.03 mm 개선 gate를 승인한다.

현재 결과: 미실시 — 실제 fan P–Q, 열전대/열화상, traceable pin, 광학계, puller tyre·bearing·encoder와 폐루프 rig가 필요하다.
