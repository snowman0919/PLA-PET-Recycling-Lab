# P0-G shredder 재순환 virtual closure 보고서

## 선택

`PASSIVE_ROTOR_SWEPT_RETURN`을 선택했다. 단순 wedge만으로는 ribbon bypass와 axial migration이 남고, active paddle은 성능상 통과하지만 actuator, jam/tach/drive fault와 세척 부담을 추가한다. 선택안은 52° return wedge, rotor-swept shelf, 교체식 anti-ribbon comb, split labyrinth barrier, 55° dead-pocket drain, 탈착식 5 mm screen tray 및 하향 service guard를 하나의 passive 경로로 조합한다.

## 가상 검증 결과

8개 PLA/PET 형상에 width, aspect ratio, wall friction, screen fill, orientation의 3-level 전조합 1,944 case를 평가했다.

- active cutter region 최소 귀환 확률: 94.22% (기준 ≥90%)
- PET ribbon 최대 bypass 확률: 0.7875% (기준 ≤1%)
- 최대 dead-pocket retention: 1.1107% (기준 ≤2%)
- 최대 axial migration: 0.7073% (기준 ≤1%)
- 최대 평균 residence: 2.132 cycle (기준 ≤4)
- guard를 통한 작업자 방향 fragment ejection: 허용하지 않음

`concept_trade.csv`, `transport_sweep.csv`, `recirculation_validation.json`이 machine-readable 증적이다. screen은 captive M5 4개를 service side에서 풀어 인출하며, rotor lockout 전에는 jam clearing을 금지한다.

## CAD 및 한계

FreeCAD Python과 `process_v0621.json`에서 5개 shredder 부품 solid, 개별 STEP, printable labyrinth/guard STL, 조립 FCStd/STEP 및 치수 SVG를 생성했다. 모든 solid가 valid이고 각 축 bounding box는 210 mm 이하다.

이 판정은 fracture-calibrated DEM이나 실제 containment 시험이 아니다. cutter phase, 마모, 수분, 정전기, 동적 변형은 아직 검증하지 않았다. 실제 chip 회수율, ribbon 포획, 파편 containment, screen 탈착·세척 시험이 필요하다. 기존 cutter shaft/bearing/frame와 22 N·m jam load를 바꾸지 않으므로 기존 Fusion LC01–LC10은 이 국부 유로 변경 때문에 재실행하지 않는다고 분류했다.
