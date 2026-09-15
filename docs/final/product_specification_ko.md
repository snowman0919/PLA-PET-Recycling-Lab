# PPR 제품 스펙시트 - v1.0.0-rc1

아래 값은 설계·소프트웨어 계약 또는 패키지 파일에서 읽은 값이다. 별도 표시가 없는 한 실측 보증 성능이 아니다. 전체 구조는 공용 분쇄기, 외부 사전 건조, 공용 screw/barrel, 냉각·측경·puller·권취 경로다.

| 항목 | 현재 기준 | 근거 / 판정 범위 |
|---|---|---|
| 최종 GGM 통합 외형 | 470 x 729 x 930 mm | `exports/final/drive_ggm_v08/manifest.json`; STEP 재수입 기준 |
| 기본 프레임 평면 | 470 x 700 mm | `physical_gate_contract.json` P2; 전체 장착품 외형과 구분 |
| hard 외형 제한 | 500 x 750 x 1000 mm | 통합 모델은 이 범위 안 |
| 선호 외형 목표 | 480 x 720 x 950 mm | GGM 통합 Y는 9 mm 초과. 목표 달성으로 표시하지 않음 |
| 압출 형상 | nominal 16 mm, L/D 16 single screw | EX-SCR-01/EX-BAR-01 RFQ; 최종 bore/flight 공차가 명목값보다 우선 |
| Screw/barrel 냉간 직경 유격 | 0.28-0.32 mm | P5/P6; 측정 불확도 포함 판정 |
| Screw/barrel 재료·처리 | SCM440, Q&T, gas nitriding, 최종 연삭/호닝 | P5 공정 증명·경도·질화층·조도 검사 필요 |
| 분쇄기 주 구동 | GGM K9DG60N2 + K9G75C, 12T:30T #35 chain | `control/ggm_drive_contract.json`; 수령/키/축방향 유지 검사 필요 |
| 압출기 주 구동 | GGM K9DG60N2 + K9G150C | 같은 계약; 역회전 금지 |
| 보호 설정 | gearbox-side software 8.0 N.m, mechanical coupon 목표 8.8-9.3 N.m | 실제 current-to-torque 및 전단핀 lot 교정 전 운전값으로 보증하지 않음 |
| Screw 시운전 | 약 8-10 rpm 시작, hard limit 20 rpm | P8/P10/P11; 상태·토크 조건 충족 시에만 진행 |
| Process heater | barrel 3 x 100 W + die 60 W = 360 W, 24 V | 최종 thermal channel 및 fuse schedule; hopper PTC는 활성 설계에서 제거 |
| 온도 profile | PLA barrel 180/195/205 C, die 200 C; PET 245/260/270 C, die 265 C | P9 및 generated firmware profile; 달성 실측 NOT_RUN |
| 열전대 | T1-T5, 비접지 K형 MI sheath, Tempco MTA1 맞춤 기준 | 정확 MPN/stop collar/승인도면·수령 시험 HOLD |
| 독립 열차단 | TF-BARREL + TF-DIE 직렬 K0 coil chain; 동일 spare 1개 | TH-FUSE-01 총3개; heater F-H1..H4 과전류 퓨즈와 역할 구분 |
| 열 관련 테이프 | PI 계열, 사용자 보유 25 mm x 30 m | 판매자 자료만 있음. 접착제/lot/정식 연속 정격 미확정; 220 C는 잠정 보수 설계값이지 인증 정격 아님 |
| 테이프 사용 범위 | 금속 shield 외측 보조재; 접착면 peak+U95 <=190 C, S4 필요 | 직접 heater/barrel/die 감싸기 금지; 얇은 PI의 내열성을 충분한 단열 효과로 간주하지 않음 |
| 제어기 / 구동회로 | Arduino Mega 2560 / GGM-BTS7960 variant | base sketch 대신 released GGM source와 HEX 사용 |
| 배포 HEX SHA-256 | 해당 패키지의 `exports/final/firmware/build_manifest.json` 안 `binary_sha256` | HEX 및 clean rebuild 로그와 대조; 구형 고정 해시를 최신으로 재사용하지 않음 |
| 치수 품질 목표 | 평균 오차 <=0.05 mm, ovality <=0.05 mm, U95 <=0.03 mm | P10/P11/P12 실제 안정 표본 필요 |
| 생산량 / 연속성 | 현재 feed 제어 명목100 g/h; 최대 안정 생산량 미확정; 200 g/h는 stretch target | `analysis/process_feed/feed_parameters.json`; 실측 달성·장시간 운전·내구 보증 없음 |
| 가격 / 조달 | 확정 견적 없음 | 미확정 재고와 제조사 회신은 구매 승인품으로 취급하지 않음 |
| 최종 상태 | FABRICATION_CANDIDATE / physical NOT_RUN / safety NOT_CERTIFIED | 공개 prerelease 게시 승인만 있음 |

부품별 세부 치수·datum·재료·표면처리·검사법은 RFQ PDF/STEP, `interface_catalog.csv`, `fastener_schedule.csv`, R2 GGM 도면과 P-stage 계약을 함께 사용한다. 이 스펙시트가 상세 도면의 공차나 미해결 수령 조건을 대체하지 않는다.
