# FRP1 Mega–Pi 직렬 프로토콜

## 전송 계층

기본 연결은 Arduino Mega의 USB device serial, `115200 8N1`이다. D14/D15는 shredder tach와 hopper gate에 배정했으므로 Pi GPIO UART 대체경로는 제공하지 않는다. Ground만 공유하고 24 V를 logic connector에 연결하지 않는다.

한 frame은 ASCII 한 줄이며 최대 159 byte다.

```text
FRP1|TYPE|SEQUENCE|PAYLOAD|CRC16\n
```

CRC는 마지막 `|CRC16`을 제외한 전 byte에 CRC-16/CCITT-FALSE(poly `0x1021`, init `0xFFFF`)를 적용한 4자리 대문자 hex다. Sequence는 unsigned 32-bit이고 modulo wrap을 허용하되 중복·역행 frame은 거부한다. Payload에는 `|`, CR, LF를 넣지 않는다.

## Pi→Mega 명령

| TYPE | PAYLOAD | 조건/효과 |
|---|---|---|
| `HB` | `uptime_ms=<n>` | 250 ms 주기; 750 ms 초과 시 Mega latched safe fault |
| `PROFILE` | `PLA` 또는 `PET` | fixed local recipe 선택; 임의 고온 setpoint 전송 금지 |
| `DRY_STAGE` | `PLA_45`, `PET_140`, `PET_160` | 선택된 material과 일치하는 고정 dryer stage만 허용 |
| `RESET` | 빈 문자열 | local BACK/ABORT 유지와 동시에만 self-test 시작 |
| `RUN` | phase 이름 | local START 유지, self-test 통과와 interlock 일치 시만 시작 |
| `PAUSE` | 빈 문자열 | heater·위험 motor safe off, 조건부 cooldown fan만 허용 |

Phase는 `SORT_SHRED`, `DRY_PREHEAT`, `EXTRUDE_SPOOL`, `COOLDOWN_CLEAN` 중 하나다. Pi 명령만으로 contactor를 붙일 수 없고, Mega의 local 안전조건과 물리 사용자 입력이 동시에 필요하다.

## Mega→Pi telemetry

`TEL` payload는 comma-separated key/value다. 최소 필드는 `state`, `phase`, `fault`, `p`, `t0`, `load`, `jam`, `retry`이며 firmware revision에서 필드를 뒤에 추가할 수 있다. `load`는 current RMS/peak/derivative, tach speed ratio와 vibration peak의 정규화 score다. Pi는 알 수 없는 필드를 무시하고 원문 frame과 수신 monotonic time을 함께 저장한다.

## Fault injection 합격 기준

- 한 bit 변조, 잘못된 CRC, field 4개 초과, 160 byte 이상, sequence replay는 actuator command에 반영되지 않는다.
- 연속 malformed 3회는 `FAULT_PROTOCOL`을 latch한다.
- heartbeat cable removal 후 750 ms 이내 heater·motor command와 contactor request가 모두 0이 된다.
- reconnect만으로 복귀하지 않으며 원인 확인 후 Pi `RESET`과 local BACK/ABORT가 동시에 필요하다.
