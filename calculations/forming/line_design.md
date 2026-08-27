# 냉각·직경게이지·풀러·스풀러 설계 계산

상태: `CALCULATED_NOT_PHYSICALLY_VALIDATED`. 원자료는 `line_design.py`, 기계판독 결과는 `simulation/forming/line_design.json`이다.

## 기준 선속과 공랭 선택

200 g/h, Ø1.75 mm에서 질량보존으로 계산한 선속은 PLA 1.118 m/min, PET 0.997 m/min이다. 250 g/h에서는 각각 1.397, 1.246 m/min이다. 1.75 mm 장원통을 24개 radial finite-volume cell로 나누고 다음 물성·gate를 사용했다.

| 재료 | ρ kg/m³ | cp J/kgK | k W/mK | die °C | puller 중심 gate °C |
|---|---:|---:|---:|---:|---:|
| PLA | 1240 | 1800 | 0.13 | 200 | 50 |
| bottle PET | 1390 | 1200 | 0.15 | 280 | 70 |

PLA density와 Tg 55–60 °C는 NatureWorks의 공개 grade 자료, PET density 1.39는 bottle-resin specification, Tg 81.5 °C는 GEHR PET TDS를 참고했다. cp와 k는 보수적 sensitivity assumption이며 폐기물 lot의 결정화도·첨가제에 따라 달라진다. [NatureWorks Ingeo grades](https://www.natureworksllc.com/~/media/Technical_Resources/one-pagers/ingeo-resin-grades-brochure_pdf), [bottle PET specification](https://stavianchem.com/sites/default/files/product-specs/YSC01.pdf), [GEHR PET TDS](https://en.gehr.de/wp-content/uploads/2022/03/GEHR-PET_Technical-data-sheet.pdf)

1.75 mm 원통 횡류에는 Churchill–Bernstein 상관식을 적용했다. 25 °C air assumption에서 2.5 m/s는 `h=127.7 W/m²K`, 4.0 m/s는 `h=160.9 W/m²K`다. 계산된 중심온도 도달 길이는 다음과 같다.

| case | 필요 길이 mm | 440 mm tunnel 여유 mm |
|---|---:|---:|
| PLA 200 g/h, 2.5 m/s | 365.0 | 75.0 |
| PLA 250 g/h, 4.0 m/s | 385.5 | 54.5 |
| PET 200 g/h, 2.5 m/s | 211.6 | 228.4 |
| PET 250 g/h, 4.0 m/s | 222.4 | 217.6 |

따라서 donor 80 mm fan 3개를 위치·duty 조절 가능한 440 mm enclosed cross-flow tunnel에 배치한다. 물통은 기준 BOM에서 제외한다. 실제 air velocity와 filament 중심/표면온도, ovality가 실패할 때만 전기부와 분리된 금속 수조를 변경안으로 검토한다. 계산 여유 55 mm는 fan 유량표나 duct 손실 검증을 대신하지 않는다.

## Dual-view optical gauge

Raspberry Pi Camera Module 3 standard의 제조사 값은 4608×2592, horizontal FOV 66°, 초점 약 100 mm–∞이다. Native 100 mm working distance의 폭은 129.9 mm, 35.48 px/mm이므로 1.75 mm는 약 62.1 px이다. 이는 0.0282 mm/px일 뿐 측정 불확도가 아니다. [Raspberry Pi camera documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)

한 카메라와 45° front-surface mirror, 서로 직교하는 두 backlight를 light-shield enclosure에 넣는다. Close-up optic을 포함한 calibrated field 목표 32 mm에서는 144 px/mm, 1.75 mm 폭 252 px다. 1.50/1.75/2.00/2.50 mm traceable pin으로 각 ray path의 homography, distortion, threshold와 scale을 독립 교정한다. 초기 ±0.05 mm 판정에는 `U95≤0.020 mm`가 필요하며 실패하면 HQ/M12 optics로 교체한다. `d_avg=(dx+dy)/2`, `ovality=|dx-dy|`를 원 frame ID와 함께 10 Hz로 기록한다.

## Transport delay와 제어 비교

Gauge 중심을 die에서 470 mm에 두면 PLA 명목 delay는 `470/(1117.6/60)=25.23 s`다. 900 s 모델에서 mass flow를 180 s에 +8%, 480 s에 −6% step으로 바꾸고, 60 s flow time constant와 모델에 없는 ±1.5%/180 s conveying ripple을 넣었다.

| controller | RMS error(120 s 이후) mm | 최대 절대오차 mm | ±0.05 밖 시간 s |
|---|---:|---:|---:|
| aggressive PID | 0.260 | 0.835 | 623.7 |
| filtered PI | 0.0363 | 0.0614 | 83.5 |
| bounded Smith PI | 0.0339 | 0.0586 | 70.6 |
| mass-flow FF + bounded Smith PI | 0.0093 | 0.0146 | 0.0 |

따라서 100 Hz encoder speed inner loop, 1 Hz mass-flow feed-forward + bounded Smith/filtered-PI diameter loop를 선택한다. Puller command는 0.5–1.6 m/min, slew는 0.02 m/min/s로 제한한다. Camera dropout은 마지막 bounded command를 최대 3 s만 유지하고 이후 feed/extrusion을 pause한다. 이 결과는 model-match 성능이며 실제 neck-down 위치, melt elasticity, nip compliance, camera jitter와 odometer slip을 포함하지 않는다. 물리 step-response로 gain을 낮추는 방향에서만 재조정한다.

## Puller와 spooler 역학

Puller는 Ø40×16 mm 동기 nip roller, 3–15 N 조절 force, drive encoder와 Ø30 mm 저하중 odometer를 쓴다. PLA 명목 roller 속도는 약 8.9 rpm이다. Drive/odometer 속도 차로 slip을 탐지하고 gauge는 두 접촉부보다 upstream에 둔다.

일반 1 kg spool은 하나의 치수 표준으로 단정하지 않는다. Bambu TDS의 Ø200×67 mm와 eSUN 제품 자료의 최대 Ø200×73 mm envelope를 받아 Ø80 mm 이상 core를 adapter로 지지한다. [Bambu filament TDS](https://cdn.shopify.com/s/files/1/0584/7236/6216/files/Bambu_PLA-CF_Technical_Data_Sheet_V3.pdf), [eSUN eBOX product data](https://www.esun3d.com/ebox-product/)

12 mm steel shaft, bearing span 105 mm, 1.35 kg spool과 4 g proof에서 중앙하중 52.96 N, bending stress 8.19 MPa, 250 MPa yield 기준 SF 30.5, 중앙처짐 0.0063 mm다. 6001-2RS 두 개와 금속 bearing plates를 사용하고 printed adapter는 torque 전달·축 지지의 단독 하중경로로 쓰지 않는다.

PLA 명목 spool 속도는 Ø80 core에서 4.45 rpm, Ø200 full에서 1.78 rpm이다. 0.5 N 장력의 full-radius torque는 0.05 N·m이며 0.25 N·m limit는 2.5 N line tension에 해당한다. 120 mm dancer ±30°는 총 240 mm, 약 12.9 s line buffer를 제공한다. Traverse는 spool 회전당 1.80 mm, 70 mm travel이며 core→full에서 8.00→3.20 mm/min이다. Dancer guard, angle sensor, home/end switch, torque limit와 full-spool tip test가 모두 필요하다.
