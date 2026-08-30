# 연구 설계 동결 인덱스

- archive commit SHA: `5d83e165466c6a8a1f4c159d198baaa1c2768e59`
- annotated tag: `research-v0.2-two-tower`
- archive branch: `archive/research-v0.2-two-tower`
- 동결일: 2026-08-28

이 snapshot은 이전 대형 연구 설계의 계산·문서·CAD를 재현 가능하게 남기기 위해 동결했다. 현 revision은 단일 소형 장치, 단일 material path, 200,000 KRW cash cap을 요구하므로 이전 구조를 active source와 혼용하면 envelope·BOM·운전 절차가 서로 모순된다.

archive의 문서, CAD, PDF와 artifact는 역사적 연구 기록이며 active revision의 제작 기준이 아니다. Archive ref는 수정하지 않는다.

## Compact v0.3 surface-proof 동결

- archive commit SHA: `d0d7f5cfe866c433bc85ca928d12583a57155c99`
- annotated tag: `compact-v0.3-surface-proof`
- archive branch: `archive/compact-v0.3-surface-proof`
- 동결일: 2026-08-29

이 snapshot은 v0.4에서 closed-solid/manifold CAD, actual slicing, CAD-to-Modelica mass/inertia bridge와 digital mechanics를 추가하기 전 compact architecture를 그대로 보존한다. Current source는 `solid-manifold-openmodelica-v0.4`이며 archive branch/tag를 수정하지 않는다.

## Solid-manifold OpenModelica v0.4 동결

- archive commit SHA: `6c1361b11814f0df72e3b2cfb195b6d56133c26b`
- annotated tag: `solid-manifold-openmodelica-v0.4`
- archive branch: `archive/solid-manifold-openmodelica-v0.4`
- 동결일: 2026-08-29

이 snapshot은 v0.5의 결합 DC motor·cutter·thermal-flow·spool physics와 최종 heater/reference-drive architecture를 적용하기 전 v0.4 제작 기준선을 보존한다. 이 archive branch와 annotated tag는 수정하지 않는다.

## Coupled digital validation v0.5 동결

- archive commit SHA: `9943b0b6c8148db0fa328c6388e00eca2d90619e`
- annotated tag: `coupled-digital-validation-v0.5`
- archive branch: `archive/coupled-digital-validation-v0.5`
- 동결일: 2026-08-30

이 snapshot은 explicit process arbitration, canonical controller contract, real spool-jam length balance, coupled forming, hot extrusion jam과 local 2040 frame reinforcement를 적용하기 전 v0.5 기준선이다. Archive branch/tag는 수정하지 않는다.

## Virtual physics closure v0.5.1 동결

- archive commit SHA: `b4ce4d73f3b7edee010018223083ee804c6e4cfb`
- archive branch: `archive/virtual-physics-closure-v0.5.1`
- 동결일: 2026-08-30

이 snapshot은 Arduino Mega 실제 I/O 구현, material-session lock, 확대된 74 scenario, CalculiX mesh convergence와 Fusion 중립 교차검증 package를 추가하기 전 v0.5.1 기준선이다. Active revision은 `implementation-crosssolver-v0.6`이며 이 archive branch는 수정하지 않는다.
