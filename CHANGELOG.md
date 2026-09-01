# 변경 이력

## technical-blocker-closure-v0.6.2.1 — 2026-09-01

- P0-A~K 저속 tach, 4-drive closed loop, spool/traverse, 독립 calibration, recirculation/positive feed, cooling rundown, hardware-adapter E2E와 OpenModelica shadow blocker를 폐쇄했다.
- 사용자 결정으로 Autodesk Fusion 실행과 수치 상관을 post-v0.6.2.1 MacBook stage로 이관했다. 정책은 `DEFERRED`이며 `CROSS_SOLVER_VALIDATED` 또는 `FUSION_VALIDATED`를 주장하지 않는다.
- tri-state Fusion gate(`REQUIRED`/`DEFERRED`/`COMPLETED`)를 추가했다. `DEFERRED`에서도 package hash 검증은 필수이고 실제 결과 파일이 존재하면 malformed/stale binding을 fail-closed로 거부한다.
- LC02/04/05/07/08/08+06/10/11 hash-bound handoff와 `prepare_run.py`를 보존했다. 실제 Fusion 수치나 placeholder PASS는 생성하지 않았다.

## parallel-actuation-hardening-v0.6.2 — 2026-08-31

- puller tach 기반 cascade PI와 실제 포화 dwell, screw 실제 회전수 기반 purge 완료, fan 2개 개별 tach/current 교차검증을 `MachineSupervisor`에 연결했다.
- 히터 요청 duty와 중앙 전력 allocator의 applied duty를 분리하고 back-calculation anti-windup, zone별 deficit·적분기·실제 time-proportion 명령을 노출했다.
- dancer 기반 spooler PI·권취 반경 추정·jam 검출과 spool 회전/피치 기반 traverse 동기화·종단 limit 누락 래치를 구현했다.
- 20 ms tach task, 250 ms fan mux/temperature task, timer·pin budget과 `PPR_DEBUG` deadline 계측을 정의했다. 지름 PI 적분은 이전 cycle의 puller tach-valid/non-saturated 상태에서만 허용한다. 장문 telemetry는 고정 snapshot의 bounded segment를 TX 여유 이하로만 전송한다. Mega 2560 compile 결과 flash 47,206 B(18%), global 3,257 B(39%), local/stack/heap 여유 4,935 B다.
- production-linked runtime 43 scenario/116 trace와 v0.6.2 고위험 mutation 7종을 통과하고, OpenModelica actuation shadow 24/24를 실제 DASSL로 해석했다.
- seeded process-risk screening은 shredder `MITIGATION_REQUIRED`, hopper/feed `MODEL_INSUFFICIENT`, cooling airflow `MITIGATION_REQUIRED`로 판정했다. 이 값은 실물 측정이나 생산 성능 주장이 아니다.
- 외부 Fusion importer에 engineering source/STEP/load manifest/case/unit/evidence hash 결합 검증을 추가했다. 실제 외부 결과가 없어 상태는 `PENDING_EXTERNAL_EXECUTION`이며 상관 판정도 pending이다.
- v0.6.1 Fusion 입력 경로와 hash를 그대로 보존했고 shadow load delta는 0이다. `FUSION_INPUT_DELTA=NONE`; main merge는 외부 Fusion 결과 또는 사용자 승인 전까지 차단한다.
- sensor/control allowance 3,000 KRW를 추가해 조건부 178,729 KRW, reserve 포함 198,729 KRW로 갱신했다. verified procurement 총액은 계속 `NOT_ESTABLISHED`다.

## safety-orchestration-closure-v0.6.1 — 2026-08-31

- pure C++ `MachineSupervisor`로 process/subsystem orchestration을 단일화하고 `.ino`는 물리 I/O·EEPROM·UI adapter로 축소했다.
- 원자적 all-subsystem fault clear와 트랜잭션형 shredder start를 구현했으며, preheat 후 별도 operator arm 없이는 feeder/screw가 시작되지 않는다.
- drive/gauge/current/cooling calibration readiness를 분리하고 EEPROM v2 version/CRC로 stale record를 거부한다. A4 fan-current feedback은 교정 전 fail-closed다.
- 실제 `MAINTENANCE_PURGE`에서 이전 material thermal profile, 별도 feed 승인과 waste-path 확인, 최소 120 s/32 command-derived screw revolutions, fault containment, 순차 청소/최종 확인을 강제한다. purge mass나 revolutions를 실측으로 주장하지 않는다.
- 공통 forming-chain rundown/thermal hold/requalification을 추가했다. gauge·cooling·puller·spooler·dancer·traverse fault reason을 보존하고, 20개 유효 sample·U95/직경/ovality 10 s·transport delay·manual rethread 전에는 production spool을 비활성화한다.
- dancer warning/controlled stop/hard stop을 0.32/0.36/0.4363 rad로 분리하고 hard-stop 접촉은 정상 safe behavior로 판정하지 않는다.
- preheat/purge 시작에 fan-only 1.5 s healthy proof/3.0 s timeout을 두고 입증 전에는 heater·motion을 금지했다. 고온 purge 중단·완료는 60 °C 이하 cooling 완료 전 바로 IDLE로 가지 않는다.
- production-linked runtime harness 43개 시나리오/116개 trace, 고정 seed bounded sequence, 필수 false-PASS mutation 14종과 firmware–Modelica 계약/8개 전력 phase 동등성 검증을 추가했다.
- OpenModelica mandatory 111 scenario에서 purge/rundown/requalification/fan-start/tach/dancer 결함을 검사했고, disturbance 전 spool 자격을 강제해 상시-off 상태로 인한 containment false-PASS를 차단했다.
- fan-current feedback allowance 2,000 KRW를 반영해 조건부/절대 계획을 175,729/195,729 KRW로 갱신했다. 실제 구매·가공·통전은 수행하지 않았다.
- 기계 geometry는 v0.6 exact SHA `60ccd92fe9a7df35b550a2a57649b1263da09d10`에서 변경하지 않았다. Fusion LC01–LC10은 새 engineering-source binding으로 재실행 필요이며 외부 결과는 계속 PENDING이다.

## implementation-crosssolver-v0.6 — 2026-08-30

- Arduino Mega 2560에 실제 MAX6675 T1–T5, H-bridge/DC/stepper/fan/heater I/O, EEPROM CRC calibration, heater protection, X/Y gauge PI와 controlled-pause, text UI backend를 구현하고 compile/host test를 통과했다.
- Process phase와 직교하는 material-session FSM을 추가해 IDLE/feed=0/screw=0에서만 전환을 시작하고 purge→screen→hopper→temperature→explicit final confirmation 순서를 강제했다.
- OpenModelica를 74개 scenario로 확대했다. 좌/우 shaft load 방향, phase reversal, multi-hook, strict rated load, gauge noise/bias/dropout, puller slip/saturation, feeder/cooling/spool permission loss, PLA/PET relief와 component-summed dynamic power를 포함한다.
- 양축 retry jam은 합계 19 N·m로 18 N·m electrical trip과 22 N·m mechanical fuse 사이를 시험하고, mechanical-fuse/multi-hook overload는 별도 보호 시나리오로 분리했다. 74/74 PASS다.
- 새 peak envelope(cutter 21.994 N·m, phase 20.000 N·m, bearing 1.857 kN, chain 0.603 kN)로 구조를 재평가했다. CalculiX bearing plate/shaft 3단계 mesh 수렴은 1.1644%/0.3119%, closed-form 최소 SF는 thermocouple ligament 2.16이다.
- EX-BAR-01 thermocouple bore를 Ø3.20 blind6→blind5.5로 줄여 nominal ligament를 2.9→3.4 mm, trip SF를 2.00→2.15로 높였다. FreeCAD/RFQ/probe 길이/검증을 함께 갱신했다.
- FreeCAD controlling source에서 Fusion STEP 9개, LC01–LC10, 7개 study, Windows worker와 hash-bound result validator를 만들었다. 실제 Autodesk Fusion 결과는 `PENDING_EXTERNAL_EXECUTION`이다.
- Project-lab 실재고와 RFQ는 증거 양식만 준비했으며, 실제 사진·라벨·실측·업체 회신이 없어 `NOT_VERIFIED`/`NOT_RECEIVED`로 유지한다. 구매·발주는 수행하지 않았다.

## virtual-physics-closure-v0.5.1 — 2026-08-30

- v0.4가 표기한 `DIGITAL_FABRICATION_BASELINE`은 근거 검토 결과 `DIGITAL_GEOMETRY_AND_SURROGATE_BASELINE`으로 재분류했고, v0.5는 모든 디지털 gate를 실제 통과한 뒤 승급했다.
- 시간기반 jam/trap legacy surrogate(ShredderSystem, ExtruderSystem, FormingSpoolSystem, FullMechanicalSystem, SafetyController, CutterRotor, ChainReduction, PhaseGearPair, InputTorqueFuse, CutterLoadSurrogate, ScrewDrive, ExtrusionLoadSurrogate, Puller, FilamentSpan, Dancer, FrameMount, VariableRadiusSpool, CalibratedDCDrive)를 제거하고, DC 전기모델 + 감속기 + motor-side one-shot shear fuse + 탄성/backlash #35 chain + phase mesh + hook load가 모두 rotational flange로 연결된 결합모델만 남겼다.
- Jam 판정은 전류 ∧ 속도비 ∧ dwell 센서 조건으로만 하고 상태기를 NORMAL_STOP/E_STOP/JAM_FAULT/SENSOR_FAULT/OVER_TEMP/DRIVE_FAULT로 분리했다. cutter tooth engagement를 rotor angle(mod θ, 2π/7)에 결합하고 PLA/PET surrogate를 분리했다.
- 360 W process heater(3×100 W mica band + 60 W die cartridge), hopper PTC maintenance heating(35×21×5, 24 V), T1–T5 sensor 배치, low-side MOSFET branch wiring, 24 V bus arbitration(490 W peak < 500 W target, SHREDDER/EXTRUSION 상호배제)을 확정했다.
- 32개 coupled scenario(전류/RPM 기반 jam, fuse trip, thermal fault, spool dynamics, cross-system fault propagation)를 모두 PASS시키고 load envelope을 CalculiX screening(9/9 PASS)과 연결했다.
- PPR-C08 guide roller를 Ø5 h6 axle + Ø5.2 reamed printed bore로 재정의하고 32행 interface catalog를 수립했다. mismatch 0.
- GMP60-60127-2460(공개 정격 70 rpm/9.8 N·m, Ø12)을 디지털 기준모터로, GMP42-775PM ratio51을 연속토크 미달로 기각했다. 12T:30T #35 chain으로 cutter 28 rpm/20.8 N·m.
- 조건부 cash target 170,629 KRW(reserve 포함 190,629 KRW, cap 200,000). `VERIFIED_PROCUREMENT_BUDGET=NOT_ESTABLISHED`, 물리 상태 `PHYSICAL_VALIDATION_PENDING`, Gate-1 전 full 발주와 `main` 승격은 잠금 유지.

## compact-single-path-v0.3 — 2026-08-28

- 이전 연구 snapshot을 tag와 archive branch로 동결했다.
- PLA/PET의 기계 경로를 하나의 470 x 700 x 930 mm cabinet으로 재설계했다.
- 외부 pre-dry + sealed maintenance hopper, 16 mm x 16 L/D 공용 screw, vertical forming path를 채택했다.
- 자동 분류, 색상 routing, custom PCB, 대형 enclosure와 별도 forming 구조를 active scope에서 제거했다.
- FreeCAD source, print package, 비용/경제성, firmware profile, 검증과 한국어 PDF를 새 revision으로 교체했다.
# solid-manifold-openmodelica-v0.4 — 2026-08-29

- Active manufacturing CAD를 valid closed solid로 정리하고 motion/service keep-out을 격리했다.
- PrusaSlicer 2.9.6 actual plate/G-code와 913.67 g nominal, 1,023.31 g planning mass를 생성했다.
- CAD mass/inertia를 Modelica package로 생성하고 18 scenario/6 sensitivity sweep를 자동 판정한다.
- 22 N·m cutter-shaft-equivalent DRV-F01 relief 하중 envelope를 9개 구조 screening과 2개 CalculiX deck에 연결했다.
- Firmware profile을 baseline에서 생성하고 donor torque calibration `verified` 전 start를 거부한다.
- Conditional target 178,420 KRW, reserve 포함 absolute 198,420 KRW로 value-engineering했다.
- Release는 `DIGITAL_FABRICATION_BASELINE`; physical result는 `PHYSICAL_NOT_RUN`이며 Gate-1 전 main 승격과 full order는 잠겨 있다.
