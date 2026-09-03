#set document(title: "Arduino Mega pinmap")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= Arduino Mega pinmap
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`


== 설계 기준

`24 V / 600 W PSU (25 A)` → main fuse → 분기 보호. Hazardous motion/heater permission은 `E-stop → lid → service guard → independent thermal cutoff → safety contactor`의 hardwired normally-safe chain이다. Mega는 feedback만 읽으며 chain을 우회하지 않는다. Protective earth는 frame과 metal hot shield에 전용 bond한다.

== 통전 전 gate

- exact PSU/driver/MOSFET/fuse/connector 정격과 DC 차단능력 확인
- 각 conductor ampacity·온도·길이·전압강하를 현지 규정과 donor stall current로 재계산
- PE continuity, insulation, polarity, branch isolation, forced-open interlock 시험 기록
- logic-only → motor → heater 순으로 별도 사용자 승인; power restore 자동 재기동 금지

== `board_config.h` exact pin map

- `SHREDDER_RPM_PIN` → `2`
- `PULLER_TACH_PIN` → `3`
- `ENCODER_A_PIN` → `18`
- `ENCODER_B_PIN` → `19`
- `ESTOP_PIN` → `20`
- `LID_PIN` → `21`
- `SERVICE_GUARD_PIN` → `22`
- `THERMAL_CHAIN_PIN` → `23`
- `HEATER_PERMISSION_FEEDBACK_PIN` → `24`
- `START_PIN` → `25`
- `PAUSE_PIN` → `26`
- `BACK_PIN` → `27`
- `CONFIRM_PIN` → `28`
- `ENCODER_BUTTON_PIN` → `29`
- `SHREDDER_DIR_PIN` → `30`
- `SHREDDER_REVERSE_PIN` → `31`
- `SHREDDER_ENABLE_PIN` → `32`
- `SCREW_DIR_PIN` → `33`
- `SCREW_ENABLE_PIN` → `34`
- `PULLER_DIR_PIN` → `35`
- `PULLER_ENABLE_PIN` → `36`
- `SPOOLER_DIR_PIN` → `37`
- `SPOOLER_ENABLE_PIN` → `38`
- `TRAVERSE_STEP_PIN` → `39`
- `TRAVERSE_DIR_PIN` → `40`
- `TRAVERSE_ENABLE_PIN` → `41`
- `LOCKOUT_CONFIRM_PIN` → `43`
- `FAN_TACH_MUX_SELECT_PIN` → `49`
- `FEEDER_ENABLE_PIN` → `42`
- `SHREDDER_PWM_PIN` → `5`
- `SCREW_PWM_PIN` → `6`
- `PULLER_PWM_PIN` → `7`
- `SPOOLER_PWM_PIN` → `8`
- `COOLING_PWM_PIN` → `9`
- `HOPPER_PTC_PIN` → `4`
- `THERMOCOUPLE_SO_PIN` → `50`
- `THERMOCOUPLE_SCK_PIN` → `52`
- `CURRENT_PIN` → `A0`
- `DANCER_PIN` → `A1`
- `GAUGE_X_PIN` → `A2`
- `GAUGE_Y_PIN` → `A3`
- `SHREDDER_FAULT_PIN` → `A8`
- `SCREW_FAULT_PIN` → `A9`
- `PULLER_FAULT_PIN` → `A10`
- `SPOOLER_FAULT_PIN` → `A11`
- `GAUGE_VALID_PIN` → `A12`
- `COOLING_CURRENT_PIN` → `A4`
- `TRAVERSE_LEFT_LIMIT_PIN` → `A5`
- `TRAVERSE_RIGHT_LIMIT_PIN` → `A6`
- `SCREW_TACH_PIN` → `A13`
- `FAN_TACH_MUX_PIN` → `A14`
- `SPOOLER_TACH_PIN` → `A15`

Array pin groups와 analog pins는 source header가 최종 기준이다. Adapter가 미승인인 feeder 추가 I/O는 배정하지 않는다.
