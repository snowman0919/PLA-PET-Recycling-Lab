# ADR-009: 18 mm, 24 L/D single-screw extruder proof

- 상태: Accepted for CAD proof; fabrication and hot operation prohibited
- 날짜: 2026-08-28

## 맥락

PLA 폐출력물과 세척·건조 bottle PET를 한 번에 한 재질씩 200 g/h 이상 압출해야 한다. 12–18 mm 직경을 비교해야 하며, motor bearing이나 출력 housing으로 screw thrust를 받으면 안 된다. 기존 18 mm 구상을 근거 없이 채택하지 않고 압력 역류와 모델 불확실성을 포함한 선택 규칙이 필요하다.

## 결정

Target proof는 Ø18 mm, 24 L/D, pitch 18 mm, 2.5:1 compression, 8D/8D/8D zone, 20–45 rpm으로 한다. 12/14/16/18 mm를 같은 Couette-minus-pressure-flow 모델로 비교하고, 8 MPa·300 Pa·s·45 rpm·melt density 1100 kg/m³에서 `>=250 g/h`를 요구했다. 18 mm만 296 g/h로 1.25× margin을 통과했다.

Hot path는 screw, ID18.2/OD38 barrel, cooled metal feed throat, 7-hole breaker plate, replaceable screen pack, Ø3×12 mm die와 purge catch로 구성한다. 모든 heater 접촉면·die·pressure port는 금속이다. 3 barrel zone + die에 80/80/80/60 W를 배정하고 PLA 180/190/200/190 °C, PET 250/270/280/275 °C를 첫 coupon profile로 둔다.

각 zone은 제어 sensor, keyed profile별 독립 high-limit(PLA 230 °C/PET 295 °C), branch fuse와 300 °C one-shot thermal fuse 후보를 갖는다. 공통 contactor는 독립 high-limit, E-stop 또는 pressure trip에서 열리고 software reset만으로 복귀하지 않는다. Thermal fuse 정격·공차와 310 °C hot-zone 설계한계의 관계는 공급품 선정 시 다시 검증한다.

압력 상태는 clean target ≤3 MPa, warning 5 MPa, feed/speed reduction 6.5 MPa, latched trip 8 MPa다. Structure proof는 20 MPa다. Pressure transducer와 proof보다 낮게 개방하는 qualified mechanical rupture element가 모두 없으면 polymer를 넣고 운전하지 않는다.

Screw thrust는 `screw -> 51102 thrust bearing -> 12 mm metal plate -> 4040/profile crossmember -> table`로 전달한다. Radial alignment bearing과 flexible coupling을 별도로 두고 motor bearing은 axial load path에서 제외한다. 51102 주변은 heat break와 강제냉각으로 70 °C 이하를 목표로 한다.

Drive 후보의 합격점은 output 20 N·m continuous at 45 rpm, 30 N·m current/torque trip, 약 126 W 이하 nominal electrical input이다. Donor+reducer를 우선 dyno하되, 실패하면 24 V geared DC motor와 metal chain reduction을 Engineering Recommended 대안으로 사용한다. Printed cycloidal reducer는 metal pin/bearing과 guard가 있어도 독립 endurance 시험 전 채택하지 않는다.

## 결과와 제한

- 18 mm×432 mm barrel은 12–16 mm보다 길고 비싸지만 16 mm의 4% 계산 여유를 피한다.
- 4.97–8.52 min residence 때문에 재질 전환 purge가 34.8–59.7 min으로 길다. 자동 PLA↔PET 연속 전환은 지원하지 않는다.
- 18 mm screw와 barrel은 210 mm print volume 대상이 아니라 CNC metal 부품이다. Guard와 sensor bracket만 분할 출력한다.
- 계산 점도는 실제 폐재료 rheology가 아니다. Die pressure, mass flow, melt temperature, torque와 residence tracer를 coupon에서 측정해 screw RPM map을 교체한다.
- PET는 dryer dew point·moisture gate와 별도로 extrusion fume/IV/색변화 검증을 통과해야 한다.

## 미채택 대안

- 12/14 mm: 45 rpm worst-normal model에서 88/139 g/h라 처리량 미달
- 16 mm: 208 g/h로 raw 목표는 넘지만 누락 손실에 대한 1.25× 여유 미달
- NEMA17 직결: 속도·토크·thermal duty 미달 가능성이 높고 검증 자료 없음
- motor bearing thrust support: axial load path와 열 격리 요구 위반
- 1.75 mm die: puller drawdown 제어와 압력 여유를 악화
- software pressure trip만 사용: sensor/controller single fault에서 구조 보호 불가
