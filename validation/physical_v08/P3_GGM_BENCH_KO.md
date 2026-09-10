# P3 GGM 구동계 벤치 검증 절차

P3는 cutter, screw, heater를 장착하지 않은 상태에서 두 GGM 구동축의 **실제 속도·전류·토크 대응과 기계식 보호핀**을 교정하는 단계다. 실행에는 P0 PASS, GGM 수령 PASS, 배선 점검, 독립 기준계측 준비와 별도 사용자 통전 승인이 필요하다.

## 치구

가능하면 프로젝트실의 traceable rotary torque transducer를 우선 사용한다. 없으면 `GGM_SH_Jackshaft`와 2×6201을 두 축에서 순차 재사용하고, 12 mm keyed test arbor에 Ø60×25 mm steel brake drum을 장착한 250.0±0.5 mm reaction-arm Prony brake를 쓴다. Brake reaction arm 끝의 0–200 N force gauge/load cell이 토크 기준이다. 8.0 N·m=32.0 N, 8.8–9.3 N·m=35.2–37.2 N이다. Drum/arm은 금속이며 출력물은 guard/센서 지지 외 구조 하중경로에 쓰지 않는다.

## P3-A: 전류센서 전기 교정

모터와 분리된 저전압 DC current loop에서 각 Hall sensor를 독립 DMM/shunt 기준과 비교한다. 최소 5개 점, 0 A 부근부터 4.6 A 이상까지 포함하고 useful range는 6 A를 넘기지 않는다. `reference_current_a`, ADC count, U95를 기록한다. 선형 fit 후 모든 점의 residual+U95가 0.10 A 이하여야 한다.

## P3-B: 무부하 축 확인

각 축을 별도로 guard 안에서 구동한다. SH는 K9G75C, EX는 K9G150C를 확인하고 3회 이상 no-load current와 output rpm을 기록한다. EX reverse command는 시험하지 않는다. 이상음·축 흔들림·coupling rub가 있으면 즉시 중단하고 P2/P3를 HOLD한다.

## P3-C: 동적 torque-current map

기계식 보호핀은 intact 상태로 두고 brake를 천천히 조여 실측 토크를 올린다. 권장 fit target은 1.5/3.0/4.5/6.0/7.8 N·m, independent holdout은 2.25/5.25/7.2 N·m이다. 실제 토크는 target이 아니라 force×실측 arm으로 계산한다. 각 loaded point는 안정값을 짧게 취득하고 brake/drum 온도 상승을 기록한다. SH holdout에는 F/R 둘 다 포함하고 EX는 F만 허용한다. holdout torque error bound는 0.40 N·m 이하다.

## P3-D: 보호핀 release coupon

이 시험은 **모터 OFF/lockout** 상태의 quasi-static 시험으로 한다. SH-F 3개, SH-R 3개, EX-F 3개를 서로 다른 coupon ID로 시험한다. 250 mm arm에서 release force U95까지 포함한 토크 구간이 8.8–9.3 N·m 안에 들어와야 한다. 파단 뒤 input/output pilot이 자유롭게 상대회전하고 hub/key에 영구손상이 없어야 한다. 목경 2.416–2.483 mm는 시작 가공 참고값일 뿐 합격값이 아니다.

## P3 판정

`analyze_p3_records.py`는 숫자 정합만 판정하며 하드웨어를 승인하거나 구동하지 않는다. 실제 P3 PASS는 기존 `analysis/drive_acceptance_v08/manufacturing/inspection.py`에 raw evidence hash·작업자·계측기 교정정보와 별도 physical authorization이 함께 들어간 뒤에만 승격한다.
