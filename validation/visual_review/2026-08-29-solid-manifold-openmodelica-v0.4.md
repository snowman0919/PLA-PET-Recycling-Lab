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
4. 최초 screw/barrel 검토 render는 4 mm 시각화 loft가 null shape로 붕괴해 barrel만 표시되는 결함이 있었다. 이를 valid single-solid인 2 mm 시각화 형상으로 교체하고 screw와 barrel을 평행 분해 배치해 flight, journal, barrel 외형이 함께 보이도록 수정했다. Bore/clearance/finish/GD&T는 raster에서 판정할 수 없으므로 controlling SVG/PDF/inspection template과 1 mm source STEP/topology audit를 사용한다.
5. Guard-removed 조립 render에서는 exact reference motor LOD가 chain 일부를 가려 인터페이스 판독성이 충분하지 않았다. 따라서 active PDF에는 motor-side DRV-F01, input/output sprocket, #35 chain run, cutter-side DRV-02와 M3 Z16 pair를 분리해 보이는 `interchangeable_drive_interface.png`를 사용한다. 이 schematic LOD는 주문 형상이 아니며 actual donor 실측 전 DRV-Axx adapter는 HOLD다.
6. 모든 갱신 render는 opaque B-Rep face 또는 hidden-edge tessellation으로 생성됐다. 이전의 투명 삼각 surface 인상은 제거됐고, cutter/gate jig/print part는 positive-volume source와 독립 topology/mesh gate로 교차 확인한다.

## 남은 물리·시각 blocker

- Transparent guard가 실제 optical clarity/impact containment을 의미하지 않는다.
- Chain slack, sprocket tooth engagement와 22 N·m replaceable fuse groove는 donor 및 Gate-1 calibration 뒤 최종 상세화한다.
- Hopper reach, screen removal, screw withdrawal와 bolt-tool clearance는 digital keep-out/section에서만 확인됐으며 실물 mock-up이 필요하다.
- Center of mass와 anchor load는 digital model 기준이다. Four-point M8 table anchor를 실제 설치하지 않고 운전하지 않는다.
- Cutter chip clearance와 actual PET folded seam capture는 Gate-1 전 PASS로 표시하지 않는다.

Digital visual review는 위 조건으로 PASS다. `main` 승격과 physical release는 Gate-1 부재로 계속 LOCKED다.
