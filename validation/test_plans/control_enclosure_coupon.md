# 제어함 coupon·패널 시험 계획

## 승인 전 조건

- safety relay, contactor, fuse, heater driver, PSU/buck, terminal과 모든 field interface의 실제 MPN·정격·치수를 확정한다.
- 관할 전기 규정과 책임 있는 전기 기술자의 검토 범위를 확정한다.

## 시험

1. PE continuity/bonding resistance를 door, shell, backplate, partition에서 측정한다.
2. E-stop 두 채널 단선·교차단락·접점 용착 모사를 수행하고 contactor feedback reset 금지를 확인한다.
3. 분기 fuse와 단락 보호, heater-driver welded-on fault, 독립 thermal fuse 차단을 저에너지 fixture부터 검증한다.
4. 최대 480 W 운전에서 30분 이상 열상승을 측정하고 enclosure 내부 최고온도·derating을 기록한다.
5. Pi brownout, Mega reset, heartbeat 상실, 센서선 단선/단락에서 heater와 motion이 기본 OFF인지 확인한다.
6. 전원/히터 배선과 logic/sensor 배선의 duct·gland 분리, shield/ground 종단과 wire bend radius를 검사한다.

## 보류 기준

- 단일 고장으로 heater/contactors가 유지되거나, reset 없이 자동 재기동하거나, PE/절연/열상승 기준을 충족하지 못하면 보류한다.
- CAD keep-out 결과만으로 mains energization을 허용하지 않는다.
