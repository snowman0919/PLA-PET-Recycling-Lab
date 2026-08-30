# 변경 이력

## coupled-digital-validation-v0.5 — 2026-08-30

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
