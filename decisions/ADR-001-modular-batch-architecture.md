# ADR-001: 모듈형 batch 재질 아키텍처

- 상태: Accepted for baseline
- 날짜: 2026-08-28

## 맥락

PLA와 PET는 건조·압출 온도와 오염 민감도가 다르다. 저예산 장치에서 두 재질을 자동 연속 전환하면 screw/barrel 잔류물, purge waste와 복잡한 valve가 품질·비용·안전을 악화시킨다.

## 결정

장치를 다음 모듈로 분리한다.

1. Input / classification
2. Three-stage shredder
3. Vibratory sorting / storage
4. Dryer / metering feeder
5. Single-screw extruder
6. Cooling / dual-axis gauge / puller
7. Dancer / traverse / spooler
8. Power / control

분류와 저장은 복수 재질을 지원하지만 한 extrusion session은 단일 재질·선택 색상 batch만 처리한다. 재질 전환에는 purge recipe와 waste path를 강제한다.

## 인터페이스 원칙

- 기계: M4/M5, metal nut/insert, alignment pin 또는 tongue-and-groove, profile T-nut
- 하중: metal shaft/part → bearing/plate → 2040/4040 profile
- 전기: keyed connector, branch fuse, connector pin에 전압/신호/정격 표기
- 데이터: Mega가 safety authority, Pi는 supervisory; heartbeat timeout은 safe stop
- 재료 흐름: gate closed/confirmed 후 다음 모듈만 enable
- 정비: hopper, screen, cutter chamber, feeder, die, puller roller를 독립 제거

## 결과

purge와 operator batch 선택이 필요하지만 오염 위험, peak power와 동시 작동 복잡도를 낮춘다. 모듈별 proof test가 가능하며 donor 부품이 확정되지 않아도 interface envelope를 먼저 설계할 수 있다.
