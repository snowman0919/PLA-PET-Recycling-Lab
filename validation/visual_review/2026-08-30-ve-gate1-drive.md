# Parent Codex visual review — VE drive와 Gate-1 jig

검토일: 2026-08-30  
Revision: `coupled-digital-validation-v0.5`  
보존 아키텍처: `compact-single-path-v0.3`

## 검토한 실제 렌더

- `renders/modules/CUT-01_cycloidal_hook_profile.png`: fabrication DXF/STEP과 같은 점열에서 생성한 7-hook 정면. 76% pitch cycloidal radial-rise capture flank, rounded overhung nose, 24% cubic relief, root/OD와 keyway가 식과 함께 식별된다.
- `renders/jigs/gate1_powered_assembly.png`: G1J-12 roof를 포함한 powered jig closed-guard 상태.
- `renders/jigs/gate1_powered_guard_removed.png`: guard를 시각 검토용으로만 제거한 exact DRV-01/A60/F01/#35/DRV-02/DRV-03 상태. 이 상태의 energization은 금지한다.
- `renders/jigs/gate1_powered_exploded.png`: motor face → DRV-A60 → DRV-01 → replaceable fuse/sprocket과 cutter load path의 조립 순서.
- `renders/modules/interchangeable_drive_interface.png`: 특정 motor/coupling/phase-gear 상품에 의존하지 않는 실제 공용 plate, adapter, shear fuse, chain, keyed phase pair solid.

## 발견과 수정

1. 첫 powered 조립에서 DRV-01 plate가 G1J-12 roof를 10 mm 관통했다. Motor axis와 plate/adapter/fuse/chain을 10 mm 낮춰 roof와의 volume intersection을 제거했다.
2. 첫 축방향 stack에서 motor reference front face와 DRV-A60가 겹쳤다. Motor face → A60 → DRV-01 순으로 Y 좌표를 재배치해 접촉면은 맞닿고 volume penetration은 없게 했다.
3. 첫 closed view만으로는 내부 구동경로가 가려졌다. 동일 source assembly에서 closed, guard-removed, exploded 세 상태를 생성해 containment와 조립경로를 분리 검토했다.
4. CUT-01 기존 일반 hook silhouette의 근거가 약했다. 실제 controlling point set과 `s(u)=u-sin(2πu)/(2π)`를 함께 그린 annotated render를 추가했다.

`validation/manufacturing_checks.py`는 두 controlling assembly envelope, roof/chute opening, DRV-01 Ø65 pass-through, DRV-03 6.2×6 keyway, motor/adapter/plate 접촉과 roof 무관통을 검사한다. 최종 digital 판정은 `MANUFACTURING_GEOMETRY_RFQ_OK`, 예상하지 않은 assembly collision은 0이다.

## 남은 물리 판정

- Polycarbonate 실제 투명도·균열·fastener preload, reach probe, fragment containment와 wrench clearance는 Gate-1 preflight 대상이다.
- Reference GMP60 solid는 치수/정격 비교용이며 구매품 또는 donor 확정이 아니다. 수령 label, shaft, no-load current/RPM, 30분 온도 기록 전 powered 시험을 허용하지 않는다.
- 실제 PLA/PET torque, jam recovery와 chip-size는 `NOT_RUN`이다. 이 기록은 full cutter stack, screw/barrel 또는 `main` release 근거가 아니다.

## 판정

VE drive와 Gate-1 jig는 digital fabrication/RFQ 검토용으로 PASS다. 물리 Gate-1은 `READY_NOT_RUN`이며, 구매·가공은 사용자 승인 후 최소 coupon 수량으로만 진행한다.
