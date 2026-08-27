# Zortrax M200 donor inventory 체크리스트

확정 정보는 베드 고장과 그 외 기능 정상이라는 사용자 설명뿐이다. 아래 측정 전에는 전압, 전류, torque, 축경과 sensor 형식을 BOM 확정값으로 사용하지 않는다.

## 안전 준비

1. 프린터를 정상 종료하고 AC plug를 분리한다.
2. nozzle/bed가 실온인지 접촉 없는 온도계로 확인한다.
3. PSU cover를 열기 전 최소 10분 대기하고, 자격 있는 감독 하에 DC bus가 1 V 미만인지 측정한다. PSU primary는 분해하지 않는다.
4. 축이 중력으로 움직일 수 있으면 cable tie 또는 block으로 고정한다.
5. connector를 뽑기 전 전체, 방향 key, wire colour가 함께 보이도록 촬영하고 임시 ID label을 붙인다.

## 요청 자료

| ID | 대상 | 촬영/측정 | 단위·방법 | 합격/판정 | 재사용 후보 |
|---|---|---|---|---|---|
| DON-PSU-01 | PSU | 전·후면 전체와 rating label 정면 | 사진, model/AC/DC/current | label 판독 가능; 손상/변색 없음 | 24 V main supply 후보 |
| DON-PSU-02 | PSU output | 무부하 Vout, terminal 수와 wire size 표기 | V DC, AWG/mm² | 24 V 계통 적합성은 label과 함께 판정 | main bus |
| DON-MOT-01 | X/Y/Z/E motor | motor별 6면, label, connector | model, phase 수, wire 수 | model 또는 winding 식별 가능 | reducer, feeder, traverse |
| DON-MOT-02 | motor shaft | shaft diameter, exposed length, flat | 0.01 mm caliper | coupling/gear 체결 길이 확보 | mechanical drive |
| DON-MOT-03 | motor winding | 분리 상태 phase-pair resistance | ohm, meter lead 보정 | phase pair 균형; 절연손상 없음 | driver matching |
| DON-DRV-01 | controller/driver | board 양면, IC top marking, connector | macro photo | IC와 supply trace 식별 | stepper control 후보 |
| DON-DRV-02 | driver cooling | heatsink/fan/air path | mm, photo | 변색·burn mark 없음 | enclosure cooling |
| DON-HTR-01 | hotend heater | cartridge label, diameter/length, cold resistance | mm, ohm | 정격은 저항만으로 확정하지 않음 | dryer/extruder는 검토 후 |
| DON-SEN-01 | hotend sensor | bead/cartridge 형상, connector, cold resistance | mm, ohm, 실온 °C | curve 미확정이면 donor hotend 전용 | temperature sensing 후보 |
| DON-FAN-01 | fan/blower | label 정면, 크기, connector | V, A, L×W×T mm | 24 V 여부와 bearing noise 확인 | cooling/dryer/electronics |
| DON-END-01 | endstop | board 양면, connector, actuating travel | continuity NO/NC | fail-safe NC 가능성 기록 | cover/traverse limit 후보 |
| DON-UI-01 | display/encoder | module 양면, cable, IC marking | photo, pin count | protocol 식별 가능 | UI 후보 |
| DON-SHAFT-01 | smooth rods/leadscrew | 직경, usable length, straightness | mm, V-block/dial indicator | runout 결과 기록 | rail/spooler/traverse |
| DON-BRG-01 | bearing/bushing | marking, ID/OD/width, 회전감 | 0.01 mm, photo | play/noise/rust 판정 | low-load axis 후보 |
| DON-PUL-01 | pulley/gear | tooth count/pitch, bore, belt marking | mm, count | matching belt와 한 세트로 식별 | reducer/traverse |
| DON-WIRE-01 | harness | connector 양쪽, wire marking/length | AWG/mm², mm | current 용도는 wire/connector 모두 만족 | low-voltage harness |
| DON-HW-01 | fasteners | head, thread, length, 수량 | M 규격, mm | thread 손상 없음 | enclosure/module assembly |
| DON-FRM-01 | metal plates/brackets | 전체/두께/구멍 pattern | mm | cutter 하중용은 material 미확정 시 금지 | enclosure/light bracket |

## 첫 요청 묶음

한 번에 전부 분해하지 않는다. 최초에는 `DON-PSU-01`, 각 motor의 `DON-MOT-01/02`, `DON-DRV-01`, `DON-FAN-01` 사진과 측정만 받으면 reducer와 power architecture의 1차 설계를 좁힐 수 있다.
