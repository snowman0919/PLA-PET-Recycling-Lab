# 건조기·정량공급기 coupon 시험계획

## 안전 전제

금속 hot path와 guard, 보호접지, branch fuse, 독립 thermal trip/fuse, latching E-stop, blower proof, 3개 온도센서, 외부 dew-point port가 없으면 heater를 인가하지 않는다. 최초 시험은 비가연성 구역에서 원격 감시하며 PET/PLA를 넣지 않은 cold-air 시험부터 시작한다. PET와 PLA heater branch의 동시 energize가 물리적으로 불가능함을 먼저 fault-injection으로 확인한다.

## 1. 기계·계량 coupon

- 빈 호퍼, 0.3/0.6/0.9/1.2 kg 표준추로 3점 load-cell을 각 5회 올림·내림 교정
- hose와 cable을 연결한 상태에서 tare drift, corner-load error, 1 h creep 측정
- auger 2/3.5/6 rpm에서 PLA와 세척·건조 PET flake를 각 30 min 공급하고 1 min 단위 질량 기록
- gate 10,000 cycle 무부하 및 1,000 cycle flake 부하 시험; leakage, jam, actuator current 기록
- agitator 20 rpm에서 1.2 kg load로 6 h 운전, shaft runout, paddle-wall contact, motor current 기록

기계 합격 기준: 0–1.2 kg 계량 오차 ±1% FS, 1 h drift ±0.5% FS, 200 g/h 명령에서 평균 ±5% 및 1 min CV≤10%, stall/접촉 0회, auger housing 분해·세척·복구 15 min 이내. Gate 차압·누설 기준을 만족하지 못하면 PET mode를 금지하고 rotary airlock을 사용한다.

## 2. 무부하 열·fault 시험

- ambient에서 PLA 45 °C와 PET 140→160 °C profile을 각각 실행
- hopper inlet/mid/outlet, heater sheath, shield 손접촉 표면, insulation bridge, cable gland를 교정 thermocouple로 기록
- control sensor open/short, blower 정지, relay welded-on 모사, fan duct block, controller hang을 한 번씩 주입
- thermal trip와 one-shot fuse는 해당 branch 전원을 하드웨어로 차단하며 경보만으로 끝나지 않는지 확인

합격 기준: 정상상태 control 편차 ±3 °C, 국부 금속 온도 공급품 정격 이하, 접근 가능한 shield 표면 50 °C 이하 목표, PLA trip 60 °C 이전, PET trip 170 °C 이전, fuse 정격 초과 전 branch de-energize. 단일 fault 뒤 heater 재인가에는 수동 reset과 원인 확인이 필요하다.

## 3. PLA 건조 coupon

- 동일 lot의 세척 flake를 무건조 control과 45 °C×6 h 군으로 각 3 batch
- 투입/배출 질량, dew point, hopper 상·중·하 온도, 전력량, bulk bridging 기록
- 압출 가능 상태가 되면 동일 압출 조건으로 bubble, filament diameter 변동, 인장 coupon 비교

합격 기준: 6 h 동안 모든 material sensor 42–48 °C, 응축·변색·고착 없음, 200 g/h 공급 유지. 재료 수분 기준은 공급원/시험법 확정 전까지 정량 승인하지 않는다.

## 4. bottle PET 고온 coupon

- 깨끗한 단일재질 PET flake만 사용하고 PVC, PETG, cap/label/adhesive를 사전 제거
- wet load는 140 °C 2 h 후 160 °C 4 h, 공정 공기 dew point와 inlet/outlet moisture를 시간별 기록
- 0.3/0.6/1.2 kg batch에서 agglomeration, wall adhesion, gate bridge, auger torque와 색변화를 확인

PET 합격 기준: 공정 dew point ≤−40 °C, outlet moisture ≤50 ppm, 모든 batch에서 용융·응집·bridge 0회, 200 g/h 안정공급, 황변·탄화 없음. 외부 교정 계측으로 둘 중 하나라도 입증하지 못하면 PET 압출은 금지한다.

## 5. endurance와 결과 상태

PLA profile 3회, PET profile 3회, 200 g/h 연속 8 h를 완료하고 체결부 paint mark, insulation 침하, 접지 연속성, load-cell drift와 hot wiring을 재검사한다. 결과는 batch ID, 원료 사진, 센서 교정번호, CSV log와 열화상 원본을 함께 보존한다.

현재 결과: 미실시 — 제작된 금속 rig, 선정된 heater/센서/fuse, 교정 dew-point 및 moisture 계측기가 필요하다.
