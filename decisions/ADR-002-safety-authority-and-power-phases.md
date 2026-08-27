# ADR-002: Mega 안전 권한과 phase 기반 전력 중재

- 상태: Accepted for baseline
- 날짜: 2026-08-28

## 결정

Arduino Mega가 heater, motor enable, interlock, E-stop, watchdog와 power arbiter의 최종 권한을 가진다. Raspberry Pi는 recipe·vision·logging을 제공하지만 위험 actuator를 독립 enable할 수 없다.

운전 phase는 `SORT_SHRED`, `DRY_PREHEAT`, `EXTRUDE_SPOOL`, `COOLDOWN_CLEAN`으로 상호 배타 관리한다. 실제 branch 정격은 donor label과 부품 선정 후 확정하며, total requested power가 derated PSU budget을 넘으면 heater duty를 우선 제한하고 위험 motor를 예고 없이 재시작하지 않는다.

## 독립 보호 계층

- latching E-stop + contactor/high-current cutoff
- lid/service interlock hard enable chain
- branch fuse와 main fuse
- heater별 thermal fuse
- Mega thermal runaway·sensor plausibility
- Pi heartbeat timeout과 Mega watchdog

## 결과

Pi hang 또는 application crash가 heater runaway로 직접 이어지지 않는다. 단, Mega firmware도 단일 실패점이 될 수 있으므로 E-stop, interlock과 thermal fuse는 firmware 밖에서 동작해야 한다.
