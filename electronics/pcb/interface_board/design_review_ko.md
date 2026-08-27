# PPR 감시·로직 인터페이스 보드 설계 검토

날짜: 2026-08-28
판정: **회로/레이아웃 자동 검증 PASS · 제작 HOLD**

## 범위와 안전 경계

이 190×130 mm, 2층 보드는 8개 24 V dry-contact 보조접점을 Mega가 읽을 수 있게 절연하고, Mega의 8개 명령을 외부 정격 드라이버로 전달한다. E-stop과 guard chain은 외부 dual-channel safety relay와 contactor가 직접 에너지를 차단한다. 본 보드나 펌웨어 진단은 그 경로를 우회할 수 없으며 기능 안전 credit을 주장하지 않는다.

## 전원 트리

```text
외부 보호 24 V sense -> J1 -> 4.7 kΩ -> opto LED -> FIELD_0V
외부 regulated 5 V  -> J2/J3 -> U9 + C1 -> J4 logic only
FIELD_0V  ||  6.35 mm copper barrier  ||  GND
```

24 V 고전류 branch는 이 PCB에 들어오지 않는다. +5 V source의 정격·퓨즈·역전류 방지는 외부 전원 설계에서 확정해야 한다.

## 채널 회로와 데이터시트 검산

- 입력 1채널: `(+24V − 1.2V) / 4.7kΩ = 4.85 mA`(명목). LTV-817 계열의 검토 기준 CTR 최소 50% @ IF=5 mA라면 collector 여유는 약 2.4 mA이고, 10 kΩ/5 V pull-up 요구 0.5 mA보다 크다. 실제 source tolerance, 온도, 노화, 접점/케이블 전압강하를 포함한 bench sweep이 필요하다.
- 1N4148-TAP는 DO-35, VR 75 V, 연속 IF 300 mA 등급으로 LED 역전압 clamp 여유가 있다. D1–D8의 K는 `LED_*_A`, A는 `FIELD_0V`다.
- SN74AHCT541N은 4.5–5.5 V 권장, VIH 최소 2.0 V, VIL 최대 0.8 V, IOH/IOL ±8 mA 조건을 확인했다. OE1/OE2는 GND, VCC pin 20, GND pin 10이며 C1 100 nF가 3.17 mm에 있다. 출력은 100 Ω 직렬과 47 kΩ pulldown을 거친다.
- 로컬 공식 PDF: TI/Vishay. Lite-On PDF는 공식 URL만 확보했고 로컬 CA 검증 실패로 파일/해시가 없어 release blocker다.

## 커넥터 핀맵

### J1 FIELD_DRY_CONTACTS

| 핀 | 신호 | 핀 | 신호 |
|---:|---|---:|---|
| 1 | +24V_SENSE | 2 | FIELD_E_STOP_AUX |
| 3 | +24V_SENSE | 4 | FIELD_CONTACTOR_FB |
| 5 | +24V_SENSE | 6 | FIELD_LID_AUX |
| 7 | +24V_SENSE | 8 | FIELD_SERVICE_AUX |
| 9 | +24V_SENSE | 10 | FIELD_THERMAL_AUX |
| 11 | +24V_SENSE | 12 | FIELD_PRESSURE_AUX |
| 13 | +24V_SENSE | 14 | FIELD_AIRFLOW_AUX |
| 15 | +24V_SENSE | 16 | FIELD_FORMING_GUARD_AUX |
| 17–18 | +24V_SENSE | 19–20 | FIELD_0V |

### J2 MEGA_DIAGNOSTICS

1–8은 순서대로 `DIAG_E_STOP_AUX`, `CONTACTOR_FB`, `LID_AUX`, `SERVICE_AUX`, `THERMAL_AUX`, `PRESSURE_AUX`, `AIRFLOW_AUX`, `FORMING_GUARD_AUX`; 9는 +5 V, 10은 GND다. Mega D22–D29에 같은 순서로 연결하며 접점 정상 시 LOW, open/fault 시 HIGH다.

### J3/J4 COMMANDS

핀 1–8은 `HEATER_EXT_Z1`, `Z2`, `Z3`, `DIE`, `DRYER_PLA`, `DRYER_PET`, `CONTACTOR_REQUEST`, `SHREDDER_ENABLE`; 9는 +5 V, 10은 GND다. J3는 Mega D4–D9, D30, D31 입력이며 J4는 같은 순서의 외부 드라이버 logic output이다. 외부 driver에도 독립 gate pulldown과 branch fuse가 필요하다.

## PCB·제조 검증

- KiCad 9.0.9 ERC: 0 violation.
- KiCad 9.0.9 DRC: 0 violation, 0 unconnected.
- 2개 분리 copper zone, 최소 field/default clearance 6.0 mm, 눈금상 장벽 6.35 mm.
- 장착: M3 NPTH 4개. 조립 기준 fiducial 3개. 서비스 포인트 12개(+24, FIELD_0V, +5, GND, 8 diagnostics).
- Gerber/Excellon/POS, schematic PDF, top/bottom/isometric render를 재생성했다.
- 최신 Gerber/Drill 전체 분석은 0 findings다. Edge.Cuts와 drill은 동일 absolute origin이며 KiCad DRC/렌더로 교차 확인했다.

## SPICE·열·EMC

- ngspice 45(Nix 임시 환경): 9/9 pass. 8개는 100 Ω + 47 kΩ 네트워크의 이상적 ratio 검증, 1개는 C1 임피던스 검증이다. 자동 도구의 3.3 V source 가정은 실제 5 V AHCT 출력 동작 보증이 아니다.
- 열 분석: 정량 power/θJA cache 부족으로 SKIPPED. 명목 입력 저항 손실은 `(22.8V)^2/4.7kΩ ≈ 111 mW/channel`; 선택할 저항은 tolerance·ambient·derating을 포함해 최소 0.25 W로 검증한다.
- CISPR 32 Class A 지향 EMC 정적 점수 52/100. 분리 양면 reference zone을 추가했지만 2층 signal routing의 plane void, layer-transition stitching, cable filtering/ground pin 수가 남는다. 옵토 U1–U8 “decoupling 없음”은 광트랜지스터를 전원 IC로 오인한 false positive다. 이 분석은 인증 예측이 아니며 enclosure/cable을 포함한 실측을 대체하지 않는다.

## 자동 분석 경고 분류

- 실제 조치 필요: connector/수동소자 MPN, mating harness, ESD/필터 전략, 2층 return path, enclosure/chassis/PE, thermal derating, 실제 CTR/logic threshold 시험.
- 의도된 제약: J2/J3/J4 8:1 signal/GND는 짧은 내부 harness 가정이며 긴 케이블에는 부적합하다.
- false positive: J1은 `GND` 대신 절연된 `FIELD_0V` 두 핀을 사용한다. U1–U8은 전원 decoupling 대상 IC가 아니다. `TBD` 문자열을 MPN 완성으로 세는 BOM 자동 집계는 무효다.
- 수행하지 않음: lifecycle/재고/가격 조회, 공인 EMC, 절연 내전압, 온도상승, fault injection, 실제 Mega/driver/harness 통합시험.

## 제작 HOLD 해제 조건

1. J1–J4 keyed/latching connector와 mating housing/contact/wire gauge MPN 확정.
2. 모든 resistor/capacitor power·voltage·temperature 등급과 MPN 확정, LTV 공식 PDF 로컬 검증.
3. 외부 +5 V/24 V source, fuse, safety relay, contactor, heater/motor driver 회로·정격 확정.
4. enclosure에서 6.35 mm barrier, 오염도/고도/creepage 요구와 harness 분리를 안전 담당자가 승인.
5. 18–30 V 입력 sweep, 접점 open/short/reverse, 온도, noise/EFT/ESD pre-compliance, power-cycle default-OFF를 실제 하드웨어로 통과.

현재 파일은 제작 견적·배선 검토용 proof이며 PCB 주문 승인본이 아니다.
