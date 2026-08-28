# Solid Manifold OpenModelica PLA/PET Recycler v0.4

Active revision은 `solid-manifold-openmodelica-v0.4`이며 release state는 `DIGITAL_FABRICATION_BASELINE`이다. PLA와 PET는 hopper부터 spooler까지 동일한 compact mechanical path를 사용한다. 물리 상태는 `PHYSICAL_VALIDATION_PENDING`/`PHYSICAL_NOT_RUN`이며, 성능·안전 인증을 뜻하지 않는다.

```text
수동 검사/세척/재질 확인 -> 공용 hopper -> 공용 dual-shaft cycloidal-inspired hook cutter
-> removable 5 mm screen/flake bin -> 외부 pre-dry -> sealed feed hopper
-> 공용 16 mm x 16 L/D single screw -> metal down-die -> vertical air cooling
-> X/Y shadow gauge -> puller -> solid guide -> dancer/traverse/1 kg spool
```

설계 envelope는 `470 x 700 x 930 mm`이며 hard limit `500 x 750 x 1000 mm` 안에 정상운전 부품과 full-motion 범위를 포함한다. Manufacturing assembly에는 제작품/stock/reference LOD만 포함하고, chain motion·dancer/traverse sweep·screw withdrawal keep-out은 `cad/review_keepouts`로 격리했다.

## Drive와 torque hierarchy

Cutter profile은 76% cycloidal radial-rise capture flank와 24% fast hook relief다. Shredder는 특정 MY1016Z, coupling 또는 phase gear MPN에 종속하지 않는다. `DRV-01 universal plate + DRV-Axx donor adapter + motor-side DRV-F01 + #35 chain + cutter-side DRV-02 + generic/laminated M3 Z16 phase pair` interface를 사용한다.

Donor는 18–30 V reversible geared brushed-DC, cutter 14 N·m continuous, 20–40 rpm 조건을 Gate-1에서 입증해야 한다. Firmware는 고정 current threshold를 torque로 오인하지 않으며 donor calibration이 `verified=true`가 아니면 시작하지 않는다. 보호 순서 `14 < 18 < 22 < 34 < 48 N·m`는 cutter-shaft equivalent이며, DRV-F01의 물리 setting은 chain ratio에 따라 17.25/12.94/10.35 N·m다.

## 현재 디지털 결과

- CAD active object 135개: 유효 B-Rep/solid topology PASS. Print part 12종은 각 1 solid다.
- STL 12종: watertight/manifold, zero-area/non-manifold edge 0, component 1.
- PrusaSlicer 2.9.6: support 설정을 포함한 nominal 994.61 g, 12% reserve 포함 1,113.96 g, 87.9 h.
- OpenModelica 1.27.0 / Modelica Standard Library 4.0.0: 18 scenario + 6 sensitivity sweep PASS.
- Digital load envelope: cutter-equivalent relief 22 N·m, bearing 1.255 kN, chain 0.603 kN, table anchor tension 0.485 kN이다.
- CalculiX screening: bearing plate 45.36 MPa/0.1840 mm, cutter shaft 48.63 MPa/0.0136 mm. Gate-1 load로 재검증해야 한다.
- 16 mm screw nominal throughput: PLA 18 rpm 111.8 g/h, PET 20 rpm 108.4 g/h. 200 g/h는 stretch target이며 현재 nominal claim이 아니다.
- Barrel front interface는 4×M4-6H/PCD26으로 정정해 nominal outer/bore-side thread ligament 2.0/2.9 mm를 확보했으며 feed assembly는 rear Datum B+12…30 mm port에 정렬된다.
- Conditional target cash 179,951 KRW; 20,000 KRW contingency 포함 199,951 KRW. 남은 계획 여유는 49 KRW뿐이고 donor/RFQ 미확정이므로 구매 release는 BLOCKED다.
- `CLEAN_CLONE_REPRODUCIBILITY`는 전체 재생성 뒤 manifest의 모든 decision-relevant artifact를 다시 해시한다. STEP exporter counter, FCStd history map, ZIP timestamp만 정규화하며 B-Rep, 문서와 3MF member content는 해시 범위에 남긴다.

## 재현

```bash
nix develop --command bash -lc 'FreeCADCmd -c "import runpy; runpy.run_path(\"cad/generation/generate_all.py\", run_name=\"__main__\")"'
python3 validation/solid_topology.py
python3 validation/mesh_checks.py
python3 validation/slice_prints.py
nix develop --command omc simulation/openmodelica/scripts/checkModel.mos
nix develop --command omc simulation/openmodelica/scripts/run_all.mos
python3 simulation/openmodelica/postprocess/summarize_results.py
nix develop --command python3 analysis/structural/run_load_checks.py
python3 firmware/arduino_mega/generate_config.py
make -C firmware/arduino_mega test
python3 validation/run_all.py
```

PrusaSlicer는 경로 순서 재현성을 위해 1 thread로 고정된다. `validation/artifact_reproducibility.py --bootstrap`은 기준선 작성자가 최초 manifest를 만들 때만 사용하며 일반 검증과 clean clone에서는 허용하지 않는다.

구매·CNC 주문·heater energization은 사용자 승인 전 금지한다. Gate-1에서는 CUT-01 정확히 2장과 최소 jig만 허용하며, signed raw 결과가 PASS이기 전 full cutter stack과 full screw/barrel 발주 및 `main` fast-forward는 잠겨 있다.

이전 snapshot의 tag/branch/SHA는 `docs/archive_index.md`에 기록한다.
