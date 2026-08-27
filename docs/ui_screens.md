# TFT UI 화면·동작 명세

상태: **portable view model implemented; donor TFT adapter not selected**. `firmware/arduino_mega/src/ui_core.*`가 화면 내용, 메뉴 상태, 입력 debounce와 run gate를 결정한다. SPI controller command, pixel geometry, font와 logic-level adapter는 `UI-TFT-001`의 controller/전압을 식별한 뒤 얇은 renderer로 연결한다. 식별 전 firmware는 TFT CS를 HIGH, RESET을 LOW로 유지한다.

UI는 safety PLC가 아니다. E-stop, monitored contactor, thermal fuse, interlock을 대체하지 않으며 rotary 조작에서 `RUN` 또는 `RESET`을 직접 만들지 않는다.

## 화면 목록

| 우선순위 | 화면 | 표시·동작 |
|---:|---|---|
| 강제 1 | STARTUP SAFETY | 환기, PLA/clean PET, PVC/ABS/TPU/unknown 금지, label/metal/food 제거, guard/bin 설치; SAFE_OFF/READY에서 PUSH 확인 전 RESET/RUN 폐기 |
| 강제 2 | STOP / FAULT | 우선 fault 원인, 32-bit mask, E-stop/격리/원인검사 안내; BACK으로 clear 불가 |
| 1 | STATUS | FSM/phase, 자동 material와 confidence, 선택 profile/color, batch, hopper, qualification/purge warning |
| 2 | MATERIAL OVERRIDE | AUTO/PLA/PET 요청만 생성; UNKNOWN/TPU는 REJECT, 물리 START와 분리 |
| 3 | COLOR BIN | 0–6 fixed bin과 7 Reject 선택, full-bin mask |
| 4 | BATCH SELECT | 1–999 batch 요청; 생산 이력 record의 실제 ID와 Pi application이 매핑 |
| 5 | HEATERS + MOTOR LOAD | Extruder 4-zone, dryer/air, shredder/extruder/forming current; invalid는 `--` |
| 6 | DIAMETER X/Y | 두 축 mm, gauge qualification, 1.70–1.80 mm와 ovality 기준 |
| 7 | PRODUCTION | 길이, 중량, ETA와 batch |
| 8 | CALIBRATION | color/gauge/load/feed wizard 요청; SAFE_OFF/PAUSED 외에는 차단, qualification lock 해제 불가 |
| 9 | MAINTENANCE | lockout/no-guard-override 경고와 checklist 요청; SAFE_OFF/PAUSED 외에는 차단 |

## 입력·안전 규칙

- Quadrature는 4개 유효 transition마다 한 step이며 불가능한 transition은 무시한다.
- Rotary PUSH와 BACK은 40 ms 안정 후 rising press event 하나만 낸다.
- 편집 중 BACK은 취소, 평상시 BACK은 STATUS 복귀다. Fault 화면에서는 아무 메뉴 입력도 fault를 clear하지 않는다.
- Startup 확인 전 들어온 Pi `RESET/RUN`은 보류하지 않고 폐기하므로 확인 뒤 새 명령과 물리 버튼이 필요하다.
- Profile 변경은 purge latch를 set한다. `EXTRUDE_SPOOL`은 차단되며 정지 상태에서 받은 `PURGE_ACK` 후 5 s 안의 local BACK/ABORT 동시 확인으로만 해제된다.
- `UI_CLASS/UI_PROD/UI_STOCK`은 CRC·sequence가 있는 표시 snapshot이며 local sensor와 interlock을 대신하지 않는다.

## TFT adapter 완료 Gate

1. Donor label, controller IC, resolution, SPI mode/maximum clock, reset polarity, backlight와 3.3/5 V tolerance를 기록한다.
2. 필요하면 bidirectional/one-way level shifter를 선정하고 D47–D52 loading과 boot pin 상태를 측정한다.
3. `UiFrame`의 24-byte title과 8×32-byte line을 화면 밖 clipping 없이 그리는 adapter를 구현한다.
4. 장갑·진동·노이즈 상태에서 1,000회 rotary/button event, boot brownout, unplug/replug와 E-stop 독립성을 시험한다.
5. 모든 화면, 한글/영문 glyph 선택, 햇빛/작업등 가독성, fault preemption과 startup acknowledgement를 실물 사진·log로 승인한다.

현재 host test는 화면·상태 로직을 증명하지만 위 물리 Gate 또는 TFT 동작을 승인하지 않는다.
