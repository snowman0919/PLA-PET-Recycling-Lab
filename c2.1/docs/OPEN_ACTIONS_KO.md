# C2.1 미해결 사용자·물리 작업

디지털 P0~P6 패키지에서 숫자로 대체할 수 없는 항목만 유지한다. 아래가 해제되기 전 구매·가공·통전·제작 승인은 HOLD다.

| 우선 | 필요한 실제 입력/행동 | 해제 증거 |
|---|---|---|
| 1 | 보유 donor와 후보 M1/M2, PSU, driver, screw, sprocket/gear, bearing, sensor의 라벨·도면·실측 | MPN, 전압/연속전류/토크-속도, 축경·길이, mount, terminal, 정격 원자료 |
| 2 | M1+driver+감속·분기, M2, 금속가공, 안전부품, 전장, heater/cooling, 배송·세금을 포함한 견적 | 수량 1 기준 landed quote와 유효일; 현재 124/135 BOM 행 원가 미상 해소 |
| 3 | bearing/shaft/pin/plate/fastener와 guard의 하중·수명·공차 설계 | 재질·열처리·fit·GD&T·TIR·preload·L10·접촉/피로 계산 및 제조사 도면 |
| 4 | safety relay, contactor, fuse, conductor, overtemp, thermal fuse, driver, clamp/suppression 선정 | MPN별 datasheet, 실제 terminal 번호, 차단용량·온도·전류·배선 규격 검토 |
| 5 | 사용자 승인 하의 물리 조립·잠금·단계 시험 | `ASSEMBLY_SERVICE_KO.md` 절차의 서명된 원자료; FAIL과 DID_NOT_RUN을 분리 |
| 6 | PLA/PET/TPU별 보정 시험 | 건조/grade/질량/입도/throughput/torque/current/rpm/jam/temperature 원자료와 calibration update |

현재 확인된 국내 200W 모터 단품 최저 floor 110,200원은 전체 잔여기계 soft budget 100,000원을 이미 넘는다. 예산 변경 또는 설계 재범위 결정이 필요하며 자동 선정하지 않는다.
