# 초기 비용 분석

## 현재 결론

현재 BOM은 구조를 잠그기 위한 **수량·가격 미확정 초기본**이다. 확인되지 않은 구매/CNC 가격을 0원으로 간주하지 않았으므로 Target Budget 달성 여부를 아직 판정할 수 없다.

## 가장 큰 비용 위험

1. Stage 1 금속 cutter, shaft와 bearing plate
2. extruder screw, barrel, die와 thrust support
3. 충분한 torque의 24 V geared drive
4. E-stop cutoff, fuse distribution, heater와 thermal fuse
5. optical gauge용 camera/optics가 보유품으로 충당되지 않는 경우

## Target Budget 전략

- donor motor는 label/bench test 후 feeder, traverse, vibratory drive부터 배정한다.
- high-torque shredder/extruder drive는 NEMA17 재사용을 강제하지 않고 reducer와 저가 gearmotor의 전체비용을 비교한다.
- cutter disc 수와 비표준 plate 수를 최소화하고 project-lab stock/표준 bearing을 우선한다.
- PCB는 wiring complexity와 안전성을 실제로 낮출 때만 제작한다.
- 공급처 가격은 part number와 specification이 잠긴 뒤 조회 날짜·shipping을 포함해 채운다.

`bom` 스킬 지침에 따라 향후 electronics schematic이 생성되면 MPN과 제조사를 KiCad symbol property의 source of truth로 유지하고 `bom.csv`로 동기화한다. 현재 system-level 기계 BOM은 schematic이 없으므로 CSV가 임시 source다.
