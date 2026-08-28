# ADR-002: 학부 MVP의 단일 E-stop 차단과 Mega 전력 중재

- 상태: Accepted for baseline
- 날짜: 2026-08-28

## 결정

Arduino Mega가 sensor 감시, heater/motor command, UI, watchdog와 power arbiter를 담당한다. Raspberry Pi, vision 분류와 원격 자동화는 MVP에서 제거한다.

사용자가 누르는 래칭 mushroom E-stop의 NC 접점은 Arduino 입력만으로 끝나지 않고 공통 24 V 액추에이터 contactor coil과 직렬 연결한다. 버튼을 누르거나 선이 끊기면 1차/2차 파쇄기, 압출 drive, puller/spooler와 heater branch의 위험 전력이 함께 제거된다. Arduino는 contactor 보조접점을 읽어 상태만 진단하며, 별도 safety relay와 tower별 이중 contactor는 사용하지 않는다.

운전 phase는 `SHRED`, `DRY_PREHEAT`, `EXTRUDE_SPOOL`, `COOLDOWN_CLEAN`으로 상호 배타 관리한다. 실제 branch 정격은 donor label과 부품 선정 후 확정하며, total requested power가 derated PSU budget을 넘으면 heater duty를 우선 제한하고 위험 motor를 예고 없이 재시작하지 않는다.

## 독립 보호 계층

- latching E-stop NC 접점 + 공통 contactor/high-current cutoff
- 고정 anti-reach hopper + 공구식 service cover + 물리 lockout
- branch fuse와 main fuse
- heater별 thermal fuse
- Mega thermal runaway·sensor plausibility
- Mega watchdog와 default-OFF driver

## 결과

구성이 단순해지고 원격 컴퓨터 장애 경로가 사라진다. Mega firmware는 여전히 단일 실패점이 될 수 있으므로 E-stop contactor와 thermal fuse는 firmware 밖에서 동작해야 한다. 이 구조는 최소 prototype 경계이며 기계 인증을 의미하지 않는다.
