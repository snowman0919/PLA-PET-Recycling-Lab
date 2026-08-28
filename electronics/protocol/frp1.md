# FRP1 선택형 Service Serial 프로토콜

Arduino Mega는 외부 컴퓨터 없이 운전한다. USB serial `115200 8N1`은 firmware upload, commissioning, CSV log와 fault injection을 위한 선택형 서비스 인터페이스다. 연결 상실은 기록하되 E-stop이나 안전정지 신호로 사용하지 않는다.

한 frame은 최대 159 byte의 ASCII 한 줄이다.

```text
FRP1|TYPE|SEQUENCE|PAYLOAD|CRC16\n
```

CRC는 `|CRC16` 앞까지 CRC-16/CCITT-FALSE(poly `0x1021`, init `0xFFFF`)를 적용한 4자리 대문자 hex다. Sequence는 unsigned 32-bit이고 modulo wrap을 허용하되 중복·역행 frame은 거부한다. Payload에는 `|`, CR, LF를 넣지 않는다.

## Service 명령

| TYPE | PAYLOAD | 조건/효과 |
|---|---|---|
| `HB` | `uptime_ms=<n>` | 연결 상태 기록만 수행; 운전 필수조건 아님 |
| `PROFILE` | `PLA` 또는 `PET` | local UI에서 선택된 recipe와 일치할 때만 반영 |
| `DRY_STAGE` | `PLA_45`, `PET_140`, `PET_160` | commissioning용 고정 dryer stage 요청 |
| `RESET` | 빈 문자열 | local BACK/ABORT 동시 입력과 안전조건이 있어야 self-test 시작 |
| `RUN` | phase | local START와 안전조건이 있어야 시작 |
| `PAUSE` | 빈 문자열 | 정상 pause 요청 |
| `PURGE_ACK` | 빈 문자열 | 정지상태와 local BACK/ABORT 동시 확인 필요 |
| `UI_BATCH` | `selected=2|3,color=0..7,batch=0..999,purge=0|1` | 수동 PLA/PET·색상·batch service snapshot |
| `UI_PROD` | 정수 key/value | 직경 X/Y, 길이, 중량, ETA와 gauge qualification snapshot |
| `UI_STOCK` | `hopper=0..100` | hopper 표시 snapshot |

Phase는 `SHRED`, `DRY_PREHEAT`, `EXTRUDE_SPOOL`, `COOLDOWN_CLEAN`이다. Serial 명령만으로 KACT를 붙일 수 없고 물리 입력과 local safety condition이 우선한다. `UI_*`는 표시 정보이며 센서·thermal chain·E-stop을 대체하지 않는다.

## Telemetry

`TEL` payload의 최소 필드는 `state`, `phase`, `fault`, `p`, `t0`, `load`, `jam`, `retry`다. `load`는 current, tach와 vibration에서 계산한 제한값이며 `retry`는 bounded jam-reverse 횟수다. Batch log는 recipe, 온도, 직경 평균과 fault를 CSV로 저장한다.

## Fault injection 기준

- 한 bit 변조, 잘못된 CRC, field 과다, 160 byte 이상, sequence replay는 actuator command에 반영하지 않는다.
- 연속 malformed 3회는 `FAULT_PROTOCOL`을 latch한다.
- USB 분리 후에도 local UI와 센서 감시는 계속 동작하고 위험 출력은 기존 local 상태와 fault 조건만 따른다.
- reconnect만으로 fault나 purge latch를 해제하지 않는다.
