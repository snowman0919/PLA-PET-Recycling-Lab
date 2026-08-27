# 입력 분류기 coupon 시험 계획

## 승인 전 조건

- 실제 힌지, cam, positive-opening interlock, actuator와 파편 차폐 재료를 선정한다.
- 최대/최소 입력 병, 찌그러진 병, 뚜껑/라벨/오염 조합을 준비한다.
- 원본 객체별 train/validation/test 분리를 고정하고 조명·노출·렌즈 설정을 기록한다.

## 시험

1. 무전원 및 단일 고장 상태에서 두 게이트가 동시에 열리지 않는지 1000 cycle 확인한다.
2. 한 스위치 단선/단락, actuator stall, 이물 끼임에서 투입이 안전 정지되는지 확인한다.
3. 최대 Ø66×210 mm 병의 통과·정지·reject를 100회 반복하고 reach probe가 닫힌 gate를 통과하지 못하는지 확인한다.
4. 재료/색/오염별 confusion matrix와 reject rate를 산출한다. 미정 클래스는 Reject로 보수 처리한다.
5. 7개 bin을 100회 순환해 잘못된 port, hose 탈락, 교차오염을 기록한다.

## 보류 기준

- simultaneous-open 1회, reach-probe 통과 1회, interlock 미검출 1회 또는 미확인 클래스를 자동 승인하면 즉시 보류한다.
- 정확도 목표는 데이터셋과 사용 환경 확정 전 설정하지 않는다.
