# 모터 선정 전 시퀀스 부하 산정

이 자료는 원료 실측이 없는 상태의 조건부 설계 산정이다. Modelica가 실행됐다는 사실과 실제 폐출력물의 최소 필요 토크가 입증됐다는 것은 다르다. 물리 시험과 기계 제작 승인은 NOT_RUN/HOLD다.

## 기존 계산을 그대로 구매 기준으로 쓰지 않은 이유
`HookMaterialLoad.mo`는 PLA/PET 부하의 capture/buckle/fracture 계수를 지정한다. `ThermalExtruderSystem.mo`는 압력을 유량의 함수로 가정하고 `polymerTorque=1.5+2.5*meltPressureMPa`로 토크를 정한다. 둘 다 해당 폐기물의 실측 재료시험을 역산한 모델은 아니다. 기존 14/15 N.m는 유일한 물리 최소값이 아니다.

## 입력과 범위
- 기존 형상: cutter 반경29 mm,7 hook; screw D16 mm,pitch16 mm,metering depth0.96 mm,tip gap0.15 mm. 계산 bore16.22 mm.
- 분쇄의 동시 절단 단면적은 양축 전체 합으로4/8/12 mm2를 사용한다. 6 mm 폭에서 등가 두께0.67/1.33/2 mm에 해당하지만, 여러 날이 동시에 물리면 그 합이므로 두꺼운 통짜 출력물 투입을 보장하지 않는다.
- 유효 절단응력은 PLA35/PET40 MPa,형상계수1.2,공회전저항0.6 N.m의 설계 가정이다. 실제 로트 전단시험값이 아니며50 MPa도 별도 민감도로 계산한다. 얇은 PET도 접혀 겹치면 요구 단면적이 커진다.
- 50/100/150 g/h는 최소 제한운전/현재 nominal/확장 검토 대역이다. 실제 처리량 또는 새로운 제품 요구의 확정이 아니다. rpm당 유량은 기존 bulk-density/fill 가정의 PLA6.209/PET5.418 g/h를 상속한다.
- 점도는 PLA600/1200/2000,PET800/1600/2600 Pa.s의 명시적 시나리오다. 실측 점도 곡선이 아니며 기준점의0.5/1.5배를 독립 민감도로 검토한다.
- 압력1.5/3/4 MPa와 압력 일 전달효율0.4는 설계 경계다. 효율0.3도 별도로 검토한다. 이것은 die의 실제 정상압력을 예측하거나6 MPa를 모터전류에서 보증하는 모델이 아니다.

## 사용한 관계
분쇄 peak: T = 0.6 + tau_eff * A_concurrent * r * geometry_factor. 주기 부하는 반파 sin^4를 사용한다. 평균제곱 적분의 닫힌형 해로 RMS를 독립 대조한다.
압출 torque: channel/flight-tip Couette 점성항 + P*A*lead/(2*pi*eta_work) 압력 일 screening + 고체공급/기계 저항. 두번째 항은 가정한 유효 나사 일 전달 모델이며 실제 연속체 압출 해석은 아니다. Newtonian die 압력/유동동력 항은 진단용으로 따로 계산하고 중복 가산하지 않는다.
기계출력 P=T*2*pi*n/60. 감속 시 n_out=n_in/i,T_out=T_in*i*eta; 큰 PSU나 추가 감속만으로 모터 축출력이 늘지는 않는다.

## 실제 실행 범위
SequenceDemand.mo와 run_study.py는 분쇄,예열,30초 soak,압출,purge,냉각 및 지정된 jam-stop/die-stop/공급감소 조건을 실행한다. 정지는 시나리오에서 부여한 명령이며 실제 검출기·PID·감속기 충격·모터열·중단거리 검증이 아니다. 예열은 단일500 J/K 열용량과0.75 W/K 손실의 lumped 근사다.
20개 최종 케이스 +2개 적분 최대시간간격 절반 재실행을 사용한다. 모든 극단을 동시에 더하지 않는다. 출력량 숫자는 주어진 feed map의 결과이며 screened flake 크기,수분,기포,직경품질과 평균 batch 처리량은 별도다.
