# v0.8 PHYSICAL VALIDATION — 현재 실행 기준

이 문서의 controlling 상세는 `validation/physical_v08/PHYSICAL_BUILD_READINESS_KO.md`와 `physical_gate_contract.json`이다. 물리 진입은 release ZIP/GitHub 상태가 아니라 `simulation_prerequisite.py`가 확인하는 23개 기술 gate 전부 PASS를 요구한다. 각 실제 구매·가공·통전 단계는 별도 사용자 승인 전 `NOT_RUN`이다.

## P1–P3: 수령·냉간조립·GGM bench

GGM K9DG60N2+K9G75C(분쇄)와 K9DG60N2+K9G150C(압출)의 실제 축/PCD/편심/길이를 수령 측정한다. BTS7960 두 개는 각각 한 축에 배정한다. current sensor는 motor lead에서 독립 기준으로 교정하며 0–6 A 유효범위의 U95 포함 오차 ≤0.10 A, torque holdout error ≤0.40 N·m를 요구한다.

Gearbox software torque limit은 8.0 N·m이고 mechanical protection coupon은 8.8–9.3 N·m에서 분리되어야 한다. 분쇄 정/역, 압출 정방향 각각 독립 coupon 3개 이상을 사용한다. 압출 reverse는 허용하지 않는다. 과거 18 N·m trip/22 N·m shear 값은 현 GGM 설계의 합격기준이 아니다.

## P4: Shredder coupon

CUT-01은 정확히 2개만 먼저 가공한다. CUT-04 5 mm screen, CUT-05/CUT-05R, 61905 계열 베어링과 현재 GGM 구동계를 사용한다. Manual torque fixture는 기존 Gate-1 형상을 재사용할 수 있지만, legacy `DRV-01/Axx/F01` powered path와 `gate1_powered_assembly.step`은 사용하지 않는다.

실측 torque/current/RPM과 손상 여부를 기록한다. 정상 PLA/PET body 투입에서 반복적인 8.0 N·m gearbox software limit 동작이 없어야 한다. 한 번 이하 재순환 후 3–6 mm ≥70%, >20 mm PET strip ≤2%, fines ≤15%, 회수율 ≥95%를 목표 합격기준으로 사용한다. 실패하면 남은 CUT-01 10개를 제작하지 않는다.

## P5–P6: Screw/barrel coupon과 냉간 압출부

Full screw/barrel 전에 `EX-CPN-SCR` 3-pitch와 `EX-CPN-BAR` 60 mm만 같은 heat/QT/nitride/finish route로 제작한다. Coupon은 pitch/land/ID/OD, 900–1100 HV, effective case 0.30–0.50 mm, screw Ra≤0.8 µm, barrel bore Ra0.4–0.8 µm, matched diametral clearance 0.28–0.32 mm를 확인한다.

Coupon이 통과한 뒤에만 full part를 별도 사용자 승인 대상으로 올린다. 냉간 조립에서는 rub/binding 0, 51102 endplay 0.05–0.15 mm, drive coaxiality ≤0.05 mm, front guide cold axial travel ≥1.50 mm를 확인한다.

## P7–P9: 전기·구동·고온부

Logic-only 단계에서 PE≤0.10 Ω, 24 V rail 22.8–25.2 V, 초기 logic current≤0.5 A, E-stop/lid/service/thermal chain forced-open 시 K0 coil de-energize, 자동재기동 0을 확인한다. 이후 모터는 한 branch씩 dry-run하고 heater는 motor inhibited 상태에서 최초 가열한다.

Die SYS-04는 M4×45 class10.9 stock screw를 42.5±0.1 mm로 절단·디버링하고 dry 1.50 N·m를 사용한다. 가열 전 cold axial travel은 ≥1.50 mm이며 first hot cycle에서 hard-stop 접촉·누설이 없어야 한다. 독립 thermal chain은 강제 개방으로 heater energy removal을 확인하며 장치를 일부러 과열시켜 시험하지 않는다.

## P10–P12: PLA → PET → forming/spool

PLA를 먼저 known dry lot으로 8–10 rpm 부근에서 시작한다. PET는 PLA가 안정된 뒤 동일하게 저속에서 시작하며 18 rpm을 기본 안전값으로 가정하지 않는다. 실제 gearbox torque가 8.0 N·m hard limit에 충분한 여유를 보일 때만 속도를 올린다. 200 g/h를 강제하지 않고 실제 최대 안정 처리량을 기록한다.

직경 검증은 20개 연속 stable sample에서 mean error≤0.05 mm, ovality≤0.05 mm, U95≤0.03 mm target을 사용한다. 최종 forming/spool에서는 puller slip≤1%, traverse 68 mm, dancer stop 0.36 rad 이전, 0.4363 rad hard-stop 비접촉을 확인한다.
