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
- `renders/cnc/extruder_die_exploded.png`
- `renders/review/compact_section.png`
- `renders/review/forming_spool_motion.png`
- `exports/print/slicing_previews/plate-08-PPR-C08-first-layer.svg`
- `exports/print/slicing_previews/plate-10-PPR-C10-first-layer.svg`
- `exports/print/slicing_previews/coupon-PPR-TC01-first-layer.svg`
- `docs/build_manual_ko.pdf` 7쪽 contact sheet
- `docs/design_report_ko.pdf` 8쪽 contact sheet
- `exports/cnc/extruder/rfq_drawing_ko.pdf` 3쪽 contact sheet
- `exports/jigs/gate1/gate1_assembly_ko.pdf` 3쪽 contact sheet

## 판정

1. CUT-01은 원형 saw tooth가 아니다. 각 7개 hook는 긴 capture flank와 짧고 급한 relief를 가지며, 단독 profile과 Gate-1 두-disc engagement render에서 비대칭 형상이 확인된다.
2. Gate-1은 축당 CUT-01 한 장, 250 mm torque arm, 5 mm screen, metal upright/plate/table load path와 full polycarbonate guard를 보여 준다. Torque arm이 guard 밖 계측점으로 나오며 rotor detail에서 두 coupon과 screen 간 위치가 구분된다.
3. Full assembly는 하나의 470×700×930 mm frame 안에 hopper/shredder/extruder/forming/spool path를 유지한다. 두 번째 tower나 외부 forming rail은 없다.
4. 최초 screw/barrel 검토 render는 4 mm 시각화 loft가 null shape로 붕괴해 barrel만 표시되는 결함이 있었다. 이를 valid single-solid인 2 mm 시각화 형상으로 교체하고 screw와 barrel을 평행 분해 배치해 flight, journal, barrel 외형이 함께 보이도록 수정했다. Bore/clearance/finish/GD&T는 raster에서 판정할 수 없으므로 controlling SVG/PDF/inspection template과 1 mm source STEP/topology audit를 사용한다.
5. Guard-removed 조립 render에서는 exact reference motor LOD가 chain 일부를 가려 인터페이스 판독성이 충분하지 않았다. 따라서 active PDF에는 motor-side DRV-F01, input/output sprocket, #35 chain run, cutter-side DRV-02와 M3 Z16 pair를 분리해 보이는 `interchangeable_drive_interface.png`를 사용한다. 이 schematic LOD는 주문 형상이 아니며 actual donor 실측 전 DRV-Axx adapter는 HOLD다.
6. 모든 갱신 render는 opaque B-Rep face 또는 hidden-edge tessellation으로 생성됐다. 이전의 투명 삼각 surface 인상은 제거됐고, cutter/gate jig/print part는 positive-volume source와 독립 topology/mesh gate로 교차 확인한다.
7. PPR-C08/C10과 PPR-TC01 first-layer preview에서 perimeter, infill, bore와 support contact가 220×220 mm bed 안에 분리되어 보인다. PDF contact sheet에서는 페이지 잘림, 빈 페이지, figure 겹침 또는 RFQ 표의 경계 이탈이 보이지 않았다.
8. 재감사에서 기존 `DownDie` cylinder가 barrel과 접선만 이루고 내부 melt turn이 없으며 upper PPR-C05가 barrel/hot shield를 각각 2,446/10,128 mm³ 관통하는 결함을 확인했다. EX-DIE-01…05 실제 Ø8 교차유로와 gasket 접속으로 교체하고 forming 중심선을 X=74.5 mm로 정렬했다. 새 section/front render와 exact die tessellation을 직접 열어 body/breaker/insert/retainer/gasket의 존재, 두 100 mm duct, 직렬 X/Y gauge와 puller 순서를 확인했다. 자동검사는 upper duct–shield 10.0 mm, upper duct–die 약 29.0 mm, 해당 관통 0을 보고한다.
9. EX-DIE-01의 유효 intersecting-bore seam은 OCC wire discretizer를 crash시켰다. Cabinet view에서만 body의 exact bounding solid를 render LOD로 쓰고, 모든 hole/channel을 유지한 별도 exact tessellation exploded view를 추가했다. 제조 판단은 STEP/FCStd/topology 검사와 EX-DIE SVG/PDF가 지배하며 render LOD는 주문 형상이 아니다.
10. 최초 EX-DIE-04는 5052-H32 t2와 5×5 mm web을 사용하고 insert 전체 투영면적을 반영하지 않아 PET 온도 relief 근거로 부적합했다. 이를 304 stainless t1.5, 두 10×2.5 mm web으로 교체했다. 265 °C 보수 항복강도 150 MPa와 insert–orifice 환형 투영면적을 사용한 digital screening은 4.32 MPa다. 새 exploded render에서 retainer가 독립 교환부품임을 확인했지만, 동일 lot 고온 coupon 3개의 최초 영구변형·우회 개방·비산 없음 시험 전에는 PASS나 release 값으로 사용하지 않는다.
11. 07:38–07:39 재생성본에서 puller guard, 두 금속 plate/roller, Ø8 spindle, guide/dancer/traverse, spool bearing plate와 motor mount가 보이는지 다시 확인했다. Guard를 높여 crossrail을 피하던 첫 수정은 gauge/roller와 실제로 겹쳤으므로 폐기하고, guard는 z=0에 유지한 채 인접 crossrail을 y=275/405 mm로 옮겨 각각 5 mm gap을 만들었다. 전체 138 object, 9,453 pair B-Rep 감사에서 정책 밖 체적간섭은 0건이다. 특정 허용은 socket weld 2쌍, chain-sprocket 보수 LOD 2쌍, generic spool/core/cone 기준 LOD 7쌍뿐이며 frame-frame 자동 예외는 제거했다.
12. 최신 isometric/front render에서 frame 내부 경로와 support가 보이지만, yellow spool/core는 구매품 실측 전 보수적인 solid reference라 cone 삽입부가 시각적으로 겹친다. 이를 실제 끼워맞춤 완료로 판정하지 않으며 PPR-C09 삽입 깊이, 6001 bearing fit, spindle runout은 Gate-5에서 받은 spool bore에 맞춰 고정한다.

## 남은 물리·시각 blocker

- Transparent guard가 실제 optical clarity/impact containment을 의미하지 않는다.
- Chain slack, sprocket tooth engagement와 22 N·m replaceable fuse groove는 donor 및 Gate-1 calibration 뒤 최종 상세화한다.
- Hopper reach, screen removal, screw withdrawal와 bolt-tool clearance는 digital keep-out/section에서만 확인됐으며 실물 mock-up이 필요하다.
- Center of mass와 anchor load는 digital model 기준이다. Four-point M8 table anchor를 실제 설치하지 않고 운전하지 않는다.
- Cutter chip clearance와 actual PET folded seam capture는 Gate-1 전 PASS로 표시하지 않는다.

Digital visual review는 위 조건으로 PASS다. `main` 승격과 physical release는 Gate-1 부재로 계속 LOCKED다.
