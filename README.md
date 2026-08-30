# Implementation + Cross-solver PLA/PET Recycler v0.6

Active revision은 `implementation-crosssolver-v0.6`이다. 상태는 `IMPLEMENTATION_BASELINE`, `virtual_physics_state=VIRTUAL_PHYSICS_VALIDATED`, `cross_solver_state=CROSS_SOLVER_VALIDATION_PENDING`, `empirical_state=EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`이다. Arduino Mega 구현과 외부 Fusion 전달 패키지를 포함하지만, 실제 Fusion solve·안전 인증·물리 filament 측정 합격을 뜻하지 않는다.

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
- Arduino Mega 2560: T1–T5 MAX6675, motor/stepper/fan/heater I/O, EEPROM calibration CRC, ordered material-change session, bounded heater PID/time-proportion, X/Y gauge PI/safe-pause, Serial text UI backend가 실제 compile 및 host test를 통과했다. 실물 board와 calibration은 미수행이다.
- OpenModelica 1.27.0 / MSL 4.0.0: 좌/우 shaft jam, phase reversal, multi-hook, gauge noise/bias/dropout, puller slip/saturation, feeder/cooling/spool permission loss, relief PLA/PET와 동적 phase power를 포함한 74 scenario PASS.
- Coupled peak envelope: cutter 21.994 N·m, phase 20.000 N·m, bearing 1.857 kN, chain 0.603 kN. 모두 측정값이 아닌 reduced-order virtual load다.
- Process heater: barrel 3×100 W + die 60 W = 360 W, T1–T5와 independent thermal cutoff. 동적 component 합산 peak는 각 phase에서 500 W 이하, PSU reserve 100 W 이상이며 shredder와 heater/screw는 상호배제한다.
- CalculiX: bearing plate medium→fine 전역 변위 차이 1.1644%, cutter shaft 0.3119%로 5% mesh convergence 기준 PASS.
- Fusion neutral package: FreeCAD source에서 생성한 STEP 9개와 LC01–LC10, study 7종, Windows worker, hash-bound result validator가 준비됐다. 실제 Fusion 결과는 `PENDING_EXTERNAL_EXECUTION`이다.
- 16 mm screw default virtual point: PLA 16 rpm 99.4 g/h, PET 18 rpm 97.5 g/h, fan 100%. 200 g/h는 `DIGITAL_STRETCH_TARGET`이며 실제 달성 claim이 아니다.
- Frame은 2020 general frame + local 2040 shredder rails를 사용한다. Profile은 총 14.668 m이고 virtual bearing-center relative displacement는 0.351 mm다.
- 조건부 cash target `173,729 KRW`; 20,000 KRW reserve 포함 `193,729 KRW`; cap 여유 `6,271 KRW`. Supplier quote와 donor evidence가 없어 `VERIFIED_PROCUREMENT_BUDGET=NOT_ESTABLISHED`다.

## 서로 독립인 세 가지 gate

- `IMPLEMENTATION_RELEASE_GATE=PASS`: 코드 compile/host test, 74개 가상 시나리오, CalculiX와 중립 package 완전성을 검증했다.
- `CROSS_SOLVER_GATE=PENDING_EXTERNAL_EXECUTION`: 실제 Autodesk Fusion 결과가 없으므로 PASS가 아니다.
- `PROCUREMENT_APPROVAL_GATE=USER_APPROVAL_REQUIRED`: CNC, cutter, screw/barrel, motor, heater, 안전부품 구매/가공은 승인 전 금지한다.
- `COMMISSIONING_GATE=USER_APPROVAL_REQUIRED`: heater 통전과 최초 powered commissioning은 물리 lockout 및 사용자 확인 전 금지한다.

Gate-1 패키지는 `OPTIONAL_EMPIRICAL_VALIDATION` 절차다. `CUT-01` 2장 coupon jig source/FCStd/STEP/STL/DXF/BOM/조립 PDF/배선/시험 CSV를 유지하지만 `main` promotion의 필수 증거가 아니다.

16 mm × 16 L/D RFQ에는 screw SCM440 QT 28–32 HRC + gas nitriding, barrel SCM440 nitrided, radial clearance 0.14–0.16 mm, runout/concentricity/surface-finish/inspection/공정 경로를 명시했다. 그러나 EX-CPN-SCR/EX-CPN-BAR process coupon과 공급사 DFM 전 full screw/barrel 발주는 금지한다.

Main promotion은 mandatory digital/virtual gate PASS만으로 허용한다. 단, full cutter stack과 screw/barrel 발주, 구매·CNC·heater energization은 별도의 사용자 승인 전 계속 잠긴다.

## 재현

```bash
python3 validation/run_all.py --regenerate-renders
```

Fusion 중립 패키지는 `exports/fusion_validation`, worker 계약은 `fusion_worker`, 상관 matrix는 `analysis/cross_solver`에 있다.

세부 생성 명령, 계산과 물리 한계는 `validation/release_checklist.md`, `bom/value_engineering_v0.5.md`, `exports/jigs/gate1`, `exports/cnc/extruder`에 기록한다. 이전 정확 snapshot은 `docs/archive_index.md`의 tag/branch/SHA로 보존한다.
