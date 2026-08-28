# 아키텍처 계약 — compact-single-path-v0.3

## 잠긴 결정

1. Material은 `PLA` 또는 `PET`이며 RUN 진입 때 잠긴다.
2. 두 재질은 동일 hopper, cutter, screen, bin, sealed feed hopper, feeder, screw, barrel, breaker, die, cooling, gauge, puller, dancer, traverse와 spool을 통과한다.
3. 외부 pre-dry를 채택한다. 장치 내 hopper heater는 재흡수 방지용이며 원료 건조 완료를 대신하지 않는다.
4. 선택 layout은 470 x 700 x 930 mm vertical forming cabinet이다.
5. 90 degree 방향 전환은 metal die 내부에서 끝난다. Die 출구부터 puller까지 filament 중심선은 수직 직선이고, 첫 guide bend는 puller 아래의 solid strand에만 적용한다.
6. Cutter는 Candidate A다. 단일 dual-shaft 반복 hook disc와 removable screen을 사용하고 oversize는 전원을 격리한 뒤 수동 재투입한다.
7. Cutter actuator는 `MY1016Z-24V-250W-75RPM` geared brushed-DC motor 1개를 right shaft에 direct keyed coupling하고, hardened M3 Z16 counter-rotation gear pair를 쓴다. PLA/PET별 motor나 shaft를 복제하지 않는다.
8. Raspberry Pi, 자동 재질/색상 분류와 network dashboard는 active scope가 아니다.

## Material profile로만 달라지는 값

Shredder speed/load/retry, pre-dry confirmation, maintenance temperature, feeder speed, screw RPM, barrel/die temperature, cooling fan, puller feed-forward, diameter PI gain, purge recipe가 달라질 수 있다. 기계 path와 guard topology는 달라지지 않는다.

## 안전 불변조건

- E-stop과 lid/service switch는 Mega 명령과 독립적으로 shredder, feeder, screw, heater branch enable을 끊는다.
- 각 heater branch에는 정격을 확인한 fuse와 one-shot thermal fuse가 있다.
- Cutter와 screw의 힘 경로는 metal shaft -> bearing/thrust plate -> metal plate -> profile -> table이다.
- Jam retry는 최대 3회 뒤 latched fault다. Clear는 물리 lockout와 원인 제거 뒤에만 가능하다.
- Melt pressure sensor가 없어도 open die, removable screen, calibrated motor torque trip, sacrificial threaded die retainer/guarded catch가 중복 방호를 제공해야 한다.

## Claim 경계

CAD와 계산은 조립성·간섭·nominal load screening만 보인다. 실제 flake 입도, melt flow, 200 g/h, 1.75 mm 품질, 안전 인증은 물리 gate 전 미검증이다.
