# 18 mm single-screw extruder proof 계산

상태: `SENSITIVITY_MODEL_NOT_PHYSICALLY_VALIDATED`. 이 계산은 직경 후보를 고르는 1차원 감도모델이며 가공 승인, 압력용기 인증 또는 200 g/h 물리 달성을 뜻하지 않는다. 원자료는 `screw_design.py`, 기계판독 결과는 `simulation/extruder/screw_design_sweep.json`이다.

## 선택 결과

| 항목 | 기준값 |
|---|---:|
| screw 외경 | 18.0 mm |
| barrel 내경 / 외경 | 18.2 / 38.0 mm |
| L/D / 유효 길이 | 24 / 432 mm |
| pitch / flight 폭 | 18.0 / 1.8 mm |
| feed / metering depth | 2.8125 / 1.125 mm |
| compression ratio | 2.5:1 |
| feed / compression / metering | 144 / 144 / 144 mm |
| 운전 범위 | 20–45 rpm |
| 정상 압력 한계 / 구조 proof | 8 / 20 MPa |
| die bore / land | 3.0 / 12 mm |

NatureWorks의 PLA sheet extrusion guide는 general-purpose single screw에 24–36 L/D, feed-throat cooling, 180/190/200 °C barrel과 190 °C die를 출발점으로 제시하고, 목표 melt 210±10 °C 및 240 °C 초과 회피를 명시한다. 본 24 L/D·PLA profile은 그 하한을 택했다. PET bottle flake는 PLA와 다른 profile이며, Alpek extrusion-grade PET의 melting point 251±2 °C와 rPET 연구의 275–280 °C rheology/extrusion 조건을 참고해 250/270/280/275 °C를 **시험 시작점**으로만 둔다. 실제 폐병 lot의 IV와 수분에 따라 수정한다.

- [NatureWorks Ingeo sheet extrusion guide](https://www.natureworksllc.com/~/media/technical_resources/processing_guides/processingguide_sheet-extrusion_pdf.pdf)
- [Alpek SG02 PET resin data sheet](https://www.alpekpolyester.com/wp-content/uploads/2023/01/Spec-Resin-Octal-09.rev_.03-SG02.pdf)
- [rPET filament reactive extrusion/rheology study](https://www.mdpi.com/2673-9623/6/2/38)
- [rPET filament extrusion at a 280 °C die](https://pmc.ncbi.nlm.nih.gov/articles/PMC10519981/)

## 직경 sweep과 선택 여유

단일 flight의 metering-zone Couette drag를 helix 축으로 투영하고 압력 역류를 뺀다.

```text
Q_drag = 0.5 W H (pi D N cos(phi)) sin(phi)
Q_pressure = W H^3 DeltaP sin(phi)^2 / (12 eta L_meter)
Q_net = max(0, Q_drag - Q_pressure)
```

`W = pitch·cos(phi) − flight width`, `phi = atan(pitch/(pi D))`다. 이는 Penn State의 single-screw drag-flow 강의식과 동일한 Couette 출발점이다. 고형 flake의 마찰 이송, flight-tip leakage, 비등온 점도와 screen 오염은 생략되어 있으므로 결과를 상한에 가깝게 취급한다.

- [Penn State single-screw extrusion notes](https://zeus.plmsc.psu.edu/~manias/MatSE447/17-22_Processing.pdf)

| D (mm) | 45 rpm, 8 MPa, 300 Pa·s, 1100 kg/m³ (g/h) | 200 g/h 대비 | 1.25× margin 통과 |
|---:|---:|---:|:---:|
| 12 | 87.8 | 0.44 | 아니오 |
| 14 | 139.4 | 0.70 | 아니오 |
| 16 | 208.1 | 1.04 | 아니오 |
| 18 | 296.3 | 1.48 | 예 |

16 mm는 계산 목표를 4%만 넘고 누락 손실보다 여유가 작다. 그래서 계산 목표 250 g/h(200×1.25)를 요구했고, 18 mm가 그 조건을 만족하는 가장 작은 후보다. 명목 5 MPa·600 Pa·s에서는 25.6 rpm이 200 g/h에 해당한다. 이 결과는 실제 30분 질량수지로 재교정한다.

## residence·purge

18 mm channel의 기하 체적은 43.05 cm³다. melt occupied fraction 35–60% 가정에서 200 g/h residence는 4.97–8.52 min이다. NatureWorks가 이종 재료 전환에서 최소 7 residence time purge를 권고하므로 계산 purge는 34.8–59.7 min이다. PLA와 PET를 바로 이어 생산하지 않고, hopper·screen pack 청소, transition resin 절차와 purge waste catch를 강제한다. 이 시간은 센서로 잔류재가 제거됐음을 확인하기 전 단축하지 않는다.

## die·압력

3.0 mm bore×12 mm land를 power-law 유체(`n=0.4`)로 계산했다. 200 g/h에서 corrected wall shear rate는 26.2 s⁻¹이며, 20 s⁻¹ 점도 300/600/1500 Pa·s의 capillary-only loss는 0.107/0.214/0.535 MPa다. 식과 가정은 fully-developed capillary power-law 해석을 따른다. 급축소 entrance, 7×Ø1.5 breaker hole, screen pack과 오염은 이 값에 없으므로 clean-system budget은 3 MPa, warning 5 MPa, controlled reduction 6.5 MPa, latched trip 8 MPa로 별도 배정한다.

- [Power-law capillary-flow formulation and limitations](https://pmc.ncbi.nlm.nih.gov/articles/PMC8659291/)

Die 출구 3.0 mm에서 1.75 mm로의 면적 drawdown은 2.94:1이다. 200 g/h의 최종 filament 속도는 PLA 약 1.12 m/min, PET 약 1.01 m/min이므로 puller가 직경을 결정하고 die bore를 1.75 mm로 만들지 않는다.

## thrust·torque·barrel

- 8 MPa에서 screw projected thrust 2.04 kN, 20 MPa proof에서 5.09 kN
- 51102 후보(15×28×9 mm, static 16.8 kN)의 proof static SF = 3.30
- 30 N·m, root Ø12.375 mm, `Kt=1.5`, candidate 4140 yield 650 MPa에서 von Mises 209 MPa, SF = 3.10
- 30 N·m, tail Ø15 mm keyway `Kt=1.6`에서 von Mises 125 MPa
- barrel ID18.2/OD38, 20 MPa thick-wall hoop, feature factor 1.5에서 47.9 MPa; 300 °C hot allowable을 보수적으로 100 MPa로 가정한 SF = 2.09

51102의 제조사 정격은 dynamic 10.5 kN, static 16.8 kN, 최대 catalog 온도 120 °C다. 그래서 bearing plate 목표는 70 °C이며, feed-throat cooling·50 mm 이상 heat-break·별도 온도센서가 필요하다. 압력은 torque로 추정하지 않고 melt pressure sensor로 직접 측정한다. 8 MPa software trip만으로 구조 안전을 주장하지 않으며, 20 MPa proof보다 낮게 작동하는 검증된 mechanical rupture element가 필요하다.

- [NTN 51102 dimensions and ratings](https://eshop.ntn-snr.com/en/product/51102-NTN/51102)

## drive·열·전력

출력 목표는 45 rpm에서 continuous 20 N·m(94.2 W mechanical), 75% 효율 가정 125.7 W electrical이며 torque trip은 30 N·m다. NEMA17·donor motor 어느 것도 라벨과 dyno 없이 이 성능을 가진다고 보지 않는다.

3개 barrel heater 80 W와 die 60 W, 합계 300 W를 둔다. OD38 barrel에 40 mm insulation을 적용한 1-D radial model과 bridge/end factor 2.5에서 steady cold-feed 요구는 PLA 65.6 W, PET 83.9 W이고, heater duty는 21.9/28.0%다. 4.26 kg hot metal, heater coupling 85% 가정의 empty cold ramp는 PLA 28.2 min, PET 40.4 min이다. Hot-zone 설계 최대는 310 °C이며 shield 외부 PLA 구조물은 해석이 아니라 thermocouple 시험으로 45 °C 미만을 확인한다.

각 zone은 제어 sensor와 독립 high-limit monitor를 분리한다. Keyed recipe selection의 독립 한계는 PLA 230 °C, PET 295 °C이고, 각 heater branch에는 300 °C one-shot thermal fuse 후보와 전류 fuse를 직렬로 둔다. Fuse 공차의 최악 상한이 310 °C 설계한계보다 낮은 공급품을 고르기 전에는 hot test를 하지 않는다. Mega, Pi, SSR/MOSFET 중 하나가 고장나도 독립 monitor/contactor와 thermal fuse가 heater energy를 제거해야 한다.

PSU 600 W 명목값의 90%인 540 W를 label 확인 전 임시 ceiling으로 두고 feeder/blower 48 W, puller/spooler 40 W, controls 36 W, cooling fan 24 W를 reserve한다. Heat-up은 drive off에서 heater 300 W(합계 448 W), 정상 압출은 heater 250 W + drive 126 W(524 W), torque transient는 heater 150 W + drive 240 W(538 W)로 제한한다. 이 숫자는 donor 실측 후 낮아질 수 있으며 300 W heater와 drive peak를 동시에 허용하지 않는다.

열모델은 contact resistance, heater clamp 편차, feed-throat cooling, die 노출면과 케이블 bridge를 분해하지 않았다. PET 첫 ramp에는 45 min timeout, zone별 상승률·sensor disagreement·heater-off cooling fault gate를 둔다.
