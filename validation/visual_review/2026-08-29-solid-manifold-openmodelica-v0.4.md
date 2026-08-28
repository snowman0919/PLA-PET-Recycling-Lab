# Parent visual review — solid-manifold-openmodelica-v0.4

검토자: parent Codex
상태: `DIGITAL_FABRICATION_BASELINE`, `PHYSICAL_NOT_RUN`

## 직접 연 이미지

- `renders/assembly/compact_full_assembly_isometric.png`
- `renders/assembly/compact_full_assembly_front.png`
- `renders/modules/CUT-01_cycloidal_hook_profile.png`
- `renders/modules/shredder_drive_guard_removed.png`
- `renders/modules/interchangeable_drive_interface.png`
- `renders/jigs/gate1_assembly.png`
- `renders/jigs/gate1_exploded.png`
- `renders/jigs/gate1_rotor_detail.png`
- `renders/cnc/extruder_screw_barrel.png`

## 판정

1. CUT-01은 원형 saw tooth가 아니다. 각 7개 hook는 긴 capture flank와 짧고 급한 relief를 가지며, 단독 profile과 Gate-1 두-disc engagement render에서 비대칭 형상이 확인된다.
2. Gate-1은 축당 CUT-01 한 장, 250 mm torque arm, 5 mm screen, metal upright/plate/table load path와 full polycarbonate guard를 보여 준다. Torque arm이 guard 밖 계측점으로 나오며 rotor detail에서 두 coupon과 screen 간 위치가 구분된다.
3. Full assembly는 하나의 470×700×930 mm frame 안에 hopper/shredder/extruder/forming/spool path를 유지한다. 두 번째 tower나 외부 forming rail은 없다.
4. Screw/barrel render는 full RFQ geometry를 보여 주지만 bore/clearance/finish는 raster에서 판정할 수 없다. Controlling SVG/PDF/inspection template과 topology audit를 사용해야 한다.
5. 기존 interchangeable-drive 개별 render는 DRV-01/02/03만 띄워 motor/chain 관계가 불명확했다. v0.4에서 donor reference LOD, input/output sprocket, #35 chain run, 22 N·m input fuse와 M3 Z16 pair를 한 schematic LOD에 표시하도록 수정했다. 이 LOD는 주문 형상이 아니며 actual donor 치수 전 adapter bracket은 HOLD다.

## 남은 물리·시각 blocker

- Transparent guard가 실제 optical clarity/impact containment을 의미하지 않는다.
- Chain slack, sprocket tooth engagement와 22 N·m replaceable fuse groove는 donor 및 Gate-1 calibration 뒤 최종 상세화한다.
- Hopper reach, screen removal, screw withdrawal와 bolt-tool clearance는 digital keep-out/section에서만 확인됐으며 실물 mock-up이 필요하다.
- Center of mass와 anchor load는 digital model 기준이다. Four-point M8 table anchor를 실제 설치하지 않고 운전하지 않는다.
- Cutter chip clearance와 actual PET folded seam capture는 Gate-1 전 PASS로 표시하지 않는다.

Digital visual review는 위 조건으로 PASS다. `main` 승격과 physical release는 Gate-1 부재로 계속 LOCKED다.
