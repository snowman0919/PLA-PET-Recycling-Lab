# 18 mm 압출기 coupon 시험계획

## 안전 전제와 계측

금속 pressure boundary, 완전한 coupling/shaft guard, 보호접지, branch fuse, 독립 heater high-limit/fuse, pressure transducer, 독립 mechanical relief, guarded discharge catch, feed-throat cooling proof와 latching E-stop이 없으면 heater·motor를 인가하지 않는다. Pressure sensor, torque/current, 4개 control 온도와 독립 high-limit 온도는 교정번호와 함께 기록한다.

고압 proof와 relief calibration은 자격 있는 담당자가 승인한 차폐·원격 절차로 수행한다. 압축성 기체를 이용한 임의 가압은 금지한다. 이 문서는 압력시험 작업절차를 대신하지 않는다.

## 1. 치수·무부하 기계 시험

- screw OD/journal/runout, barrel bore/직진도, die land와 bearing seats를 교정 계측기로 map 작성
- 승인된 assembly tolerance stack과 hot-growth 계산에 대조
- breaker/screen 없이 손 회전 후 5/10/20/45 rpm을 각 10 min 운전
- bearing plate, coupling, guard, barrel과 motor의 진동·온도·전류 기록
- cold shaft lock을 안전하게 모사하여 30 N·m torque trip 및 재시작 금지 확인

합격 기준: 접촉·긁힘 0회, 45 rpm에서 비정상 진동/소음 없음, 모든 guard 고정, trip 후 manual reset 전 자동 재기동 없음. 실제 clearance 또는 runout이 승인 해석 범위를 벗어나면 hot test를 금지한다.

## 2. 압력 경계·relief 시험

- 제작체와 동일 재질·thread·seal의 port coupon으로 leak와 thread pull-out 검증
- 자격 절차에 따라 pressure boundary proof, transducer 교정과 relief 반복성 확인
- 3/5/6.5/8 MPa 신호를 독립 calibrator로 주입하여 정상/경고/감속/latched trip 상태 확인
- relief discharge가 catch 밖으로 향하지 않고 shield/배선/센서를 손상시키지 않는지 확인

합격 기준: 누설·영구변형 0, sensor 오차가 제어 안전여유 내, 6.5 MPa에서 feed/speed가 감소하고 8 MPa 이전 heater/feed/motor가 안전상태로 전환, reset은 압력 제거와 원인 확인 뒤에만 허용. 구조 20 MPa 계산과 10 MPa relief 후보는 실제 인증값으로 대체되기 전 운전 승인 근거가 아니다.

## 3. 무수지 열·fault 시험

- ambient에서 PLA와 PET zone profile을 각각 실행해 ramp, overshoot, steady-state duty 기록
- barrel 각 zone, die, feed throat, thrust plate/bearing, shield, cable gland를 독립 thermocouple/열화상으로 측정
- control sensor open/short, SSR welded-on 모사, coolant flow loss, fan/vent block, controller hang을 하나씩 주입

합격 기준: normal zone 편차 ±3 °C, shield 접근면 ≤50 °C 목표, bearing plate ≤70 °C, 모든 wiring/insulation이 공급자 정격 이하. PLA 230 °C/PET 295 °C independent limit 이전에 heater branch가 하드웨어 차단되고 자동 복귀하지 않아야 한다.

## 4. PLA 재료 시험

- 승인된 건조 단일재질 PLA만 투입하고 40 mesh부터 시작
- 20 rpm에서 purge 후 25.6 rpm 기준으로 30 min 안정 운전, 이후 20/30/45 rpm 각 15 min
- 1 min 단위 mass flow, melt pressure, torque/current, 4 zone 온도, die 출구 온도와 색/기포 기록
- 정지 시 최소 7 barrel-volume purge 기준(예측 34.8–59.7 min)을 실제 배출 질량으로 검증

합격 기준: 기준점 평균 ≥200 g/h, 30 min 동안 feed starvation/plug/pressure trip 없음, clean screen에서 pressure ≤3 MPa 목표, 변색·탄화·금속 접촉 흔적 없음. Die strand diameter는 downstream puller 미연결 상태의 진단값이며 1.75 mm 제품 합격 판정에 사용하지 않는다.

## 5. bottle PET 재료 시험

건조기 coupon에서 dew point ≤−40 °C와 outlet moisture ≤50 ppm이 입증된 깨끗한 bottle PET flake만 사용한다. PLA 잔류물이 없도록 승인 purge를 수행하고, 낮은 feed/20 rpm에서 시작해 250/270/280/275 °C profile을 단계적으로 검증한다. Hydrolysis, acetaldehyde 냄새, 황변, black speck, pressure와 torque drift를 기록한다.

합격 기준: 200 g/h 안정 공급, 8 MPa trip 미도달, 열화·기포·탄화 없음, pressure/temperature가 30 min 동안 안정. 수분 또는 건조공기 기준이 한 번이라도 벗어나면 PET 공급을 즉시 차단하고 batch를 폐기/격리한다.

## 6. 내구·결과 상태

PLA 8 h와 PET 8 h 연속 coupon 후 screw/barrel을 분해하여 wear, scoring, polymer holdup, breaker clog, bearing play, fastener paint mark와 접지 연속성을 재검사한다. CSV log, 원료 batch, screen mesh, purge mass/time, calibration IDs, 열화상과 분해 사진을 보존한다.

현재 결과: 미실시 — 가공된 pressure-rated 금속 rig, 선정·인증된 relief/센서/히터/베어링, 교정 계측기와 자격 압력시험 절차가 필요하다.
