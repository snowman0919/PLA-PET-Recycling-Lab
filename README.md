# Coupled Digital Validation PLA/PET Recycler v0.5

Active revision은 `coupled-digital-validation-v0.5`, release state는 `DIGITAL_FABRICATION_BASELINE`이다. `compact-single-path-v0.3`의 단일 기계 경로와 `470 × 700 × 930 mm` 외형을 유지한다. 물리 상태는 `PHYSICAL_VALIDATION_PENDING`(`PHYSICAL_NOT_RUN`)이며 성능 또는 안전 인증이 아니다.

```text
수동 검사/세척/재질 확인 → 공용 hopper → 공용 dual-shaft cycloidal-inspired hook cutter
→ removable 5 mm screen/flake bin → 외부 pre-dry → sealed feed hopper
→ 공용 16 mm × 16 L/D single screw → metal die → compact air cooling
→ X/Y shadow gauge → puller → solid guide → dancer/traverse/1 kg spool
```

## 분쇄기 drive

`CUT-01`은 각 pitch의 76%에 cycloidal radial-rise capture flank, 24%에 빠른 hook relief를 둔 비대칭 7-hook cutter다. 특정 MY1016Z, coupling, phase-gear MPN 대신 `DRV-01 universal plate + DRV-Axx adapter + DRV-F01 replaceable shear fuse + #35 12T:30T chain + DRV-02 hub + generic/laminated M3 Z16 phase pair`를 사용한다.

Project-lab 우선 후보는 24 V wheelchair/conveyor geared brushed-DC, 그다음 검증된 scooter/e-bike geared motor다. 합격조건은 cutter 환산 20–40 rpm, 연속 14 N·m, 3초 peak 24 N·m, 30분 case ≤80 °C다. 정확한 디지털 기준모터 `GMP60-60127-2460 ratio 47`은 공개 정격 70 rpm/9.80665 N·m이며 12:30, η=0.85에서 cutter 28 rpm/20.84 N·m다. `GMP42-775PM ratio 51`은 동일 조건 5.42 N·m라 연속토크 기준에 불합격한다. 둘 다 donor 실물이나 구매 승인품을 뜻하지 않는다.

보호 순서 `14 < 18 < 22 < 34 < 48 N·m`는 cutter-shaft equivalent다. Firmware는 donor의 no-load current, torque/A, ratio, efficiency와 encoder RPM을 교정한 `verified=true` record 없이는 시작하지 않는다. E-stop, lid/service hard-cut, branch fuse, DRV-F01과 independent thermal fuse는 유지한다.

## 디지털 검증 결과

- 설계 외형: `470 × 700 × 930 mm`; hard `500 × 750 × 1000 mm`, target `480 × 720 × 950 mm` 이내.
- 출력품: 12종, 계획 질량 `904.20 g` (실패 12% reserve 포함 `1,012.70 g`) 이하 기준선; 개별 축 210 mm 이하. 실제 slicer 결과는 재검증 산출물을 따른다.
- OpenModelica 1.27.0 / MSL 4.0.0: DC electrical motor, 47:1 gearbox, compliant #35 chain/backlash, one-shot shear fuse, phase mesh, cutter load, 4-node thermal-flow, dynamic spool을 연결한 32 scenario PASS.
- Coupled peak envelope: cutter 21.994 N·m, phase 16.216 N·m, bearing 1.797 kN, chain 0.603 kN. 모두 실물 Gate-1 전 surrogate다.
- Process heater: barrel 3×100 W + die 60 W = 360 W, T1–T5와 independent thermal cutoff. Extrusion active peak 490 W < 24 V 600 W; shredder와 heater/screw는 상호배제한다.
- 16 mm screw nominal model: PLA 18 rpm 111.8 g/h, PET 20 rpm 108.4 g/h. 200 g/h는 `ExtruderHighFlow` 디지털 stretch case일 뿐 실제 달성 claim이 아니다.
- 조건부 cash target `170,629 KRW`; 20,000 KRW reserve 포함 `190,629 KRW`; cap 여유 `9,371 KRW`. Supplier quote와 donor evidence가 없어 `VERIFIED_PROCUREMENT_BUDGET=NOT_ESTABLISHED`다.

## 주문 가능한 범위와 잠금

Gate-1 패키지는 `CUT-01` 2장 coupon만 사용하는 완전한 jig source/FCStd/STEP/STL/DXF/BOM/조립 PDF/배선/시험 CSV를 포함한다. PLA wall 1.2/2.0/3.0 mm, PET body/fold seam의 torque-current-RPM, jam/reverse, 3–6 mm chip fraction을 기록한다.

16 mm × 16 L/D RFQ에는 screw SCM440 QT 28–32 HRC + gas nitriding, barrel SCM440 nitrided, radial clearance 0.14–0.16 mm, runout/concentricity/surface-finish/inspection/공정 경로를 명시했다. 그러나 EX-CPN-SCR/EX-CPN-BAR process coupon과 공급사 DFM 전 full screw/barrel 발주는 금지한다.

Gate-1 signed raw CSV와 photo/video hash가 PASS이기 전에는 full cutter stack, full screw/barrel 발주와 `main` fast-forward를 모두 잠근다. 구매·CNC·heater energization은 사용자 승인 전 금지한다.

## 재현

```bash
python3 validation/run_all.py --regenerate-renders
```

세부 생성 명령, 계산과 물리 한계는 `validation/release_checklist.md`, `bom/value_engineering_v0.5.md`, `exports/jigs/gate1`, `exports/cnc/extruder`에 기록한다. 이전 정확 snapshot은 `docs/archive_index.md`의 tag/branch/SHA로 보존한다.
