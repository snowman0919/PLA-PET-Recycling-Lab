# 선택 배치 dryer·정량 feeder proof 계산

- 상태: 열수지/공급 후보, 물리 건조·수분·응집 시험 미검증
- 조회일: 2026-08-28
- 중요한 구분: PETG filament의 저온 건조값을 PET bottle flake에 적용하지 않는다.

## 자료 근거와 profile

Prusa의 Prusament 지침은 PLA/rPLA에 `45 °C, 6 h`를 제시한다. 반면 DAK Laser+ bottle-grade PET 지침은 실제 chip `149–166 °C`, 건조공기 dew point `-36.7 °C 이하`, 최소 4 h·권장 6 h를 요구하며, wet load는 `135–150 °C에서 2 h` 시작 후 최대 165 °C로 올리도록 한다. DuPont Rynite PET guide도 수분 0.02 wt% 미만, 120 °C 4 h, dew point -20 °C 이하를 요구한다.

따라서 baseline은 다음 두 물리적으로 분리된 heater safety branch를 쓴다.

| profile | 운전 | 독립 high limit | one-shot fuse | 상태 |
|---|---:|---:|---:|---|
| PLA | 45 °C, 6 h | 60 °C | 72 °C | Prusament 근거, flake coupon 필요 |
| bottle PET | 140 °C 2 h + 160 °C 4 h | 170 °C | 184 °C | -40 °C dew point와 ≤50 ppm endpoint 검증 전 미승인 |

PET 고온 branch와 PLA 저온 branch는 hardware contactor/interlock로 동시에 켜지지 않는다. PET flake가 crystallization 전에 Tg 부근에서 달라붙을 수 있으므로 저속 agitator, 단계 승온과 실제 agglomeration 시험이 필수다.

출처:

- Prusa Research, “Drying filament”, PLA/rPLA 45 °C 6 h: https://help.prusa3d.com/article/drying-filament_332086
- DAK Americas, Laser+ PET processing note, chip 300–330 °F, dew point preferably -40 °F, 4–6 h: https://www.liquidbottles.com/_wss/clients/1/assets/PKP150W-PA1.pdf
- DuPont, Rynite PET molding guide, 120 °C 4 h and dew point below -20 °C: https://dupont.materialdatacenter.com/links/processing/Rynite.pdf

## hopper와 체류시간

ID 140 mm × active height 320 mm의 금속 hopper는 기하 용적 `4.93 L`다. flake bulk density를 `250 kg/m³`로 가정하면 약 `1.23 kg`이고, 설계 inventory 1.20 kg은 200 g/h에서 정확히 `6 h` 체류한다. 실제 PLA/PET flake의 bulk density, channeling과 first-in/first-out은 weigh test로 갱신한다.

## 열수지

2.5 kg 금속 hopper, 1.2 kg flake, 40 mm 고온 단열재(`k=0.04 W/mK`), thermal bridge factor 1.3을 가정한다.

- PLA 45 °C: 60 W heater, sensible energy 약 53.8 kJ, 이상 ramp 약 15.6 min
- PET 160 °C: 240 W heater, sensible energy 약 363 kJ, 이상 ramp 약 27.3 min
- PET steady heat loss 약 36.6 W, 200 g/h cold-feed sensible load 약 9.0 W, 계산 duty 약 19%

이상 ramp에는 수분 탈착, 공기·덕트·desiccant, 누설과 제어 여유가 빠져 있으므로 실제 recipe의 최소 승온시간은 60 min으로 시작한다. 24 V 240 W는 10 A이므로 전용 branch fuse/MOSFET/contactor와 독립 fuse가 필요하다. PET 건조와 extruder 최대 heating은 600 W PSU에서 동시에 허용하지 않는다.

## 정량 feeder

30 mm OD, 10 mm shaft, 24 mm pitch auger의 이론 displacement는 약 15.1 cm³/rev다. bulk density 0.25 g/cm³, fill 25%에서 `0.94 g/rev`, 200 g/h는 `3.54 rpm`이다. 2–6 rpm 범위를 baseline으로 두고, 20 rpm agitator를 간헐 구동한다.

hopper load-cell의 120 s 질량감소와 auger motor current를 함께 사용한다. 명령 대비 질량감소가 50% 미만이면서 current가 상승하면 bridge/jam, current가 낮으면 empty/slip으로 분류한다. dry-air 역류를 막기 위해 auger 출구와 cooled feed throat 사이에 이중 gate 또는 rotary airlock을 둔다.

## 제작 승인 gate

1. 공급 PET flake의 agglomeration/crystallization 시험과 actual outlet moisture ≤50 ppm 확인
2. hopper 상·중·하 3점 온도 ±5 °C, dew point -40 °C 이하를 외부 계측기로 확인
3. 6 h residence tracer test와 200 g/h 질량 공급 CV ≤5%
4. heater stuck-on, fan loss, sensor open/short, agitator jam, Pi disconnect fault injection
5. 단열 외부 metal shield <45 °C 및 모든 PLA housing <45 °C 확인
