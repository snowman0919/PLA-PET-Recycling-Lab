# 자동검증 보고 — solid-manifold-openmodelica-v0.4

## Release 경계

- release: `DIGITAL_FABRICATION_BASELINE`
- physical: `PHYSICAL_NOT_RUN` / `PHYSICAL_VALIDATION_PENDING`
- 구매·CNC: `BLOCKED_PENDING_USER_APPROVAL_AND_PHYSICAL_GATES`
- main 승격: Gate-1 결과가 없어 `LOCKED`

## Digital evidence

|항목|결과|증거|
|---|---:|---|
|Envelope|470×700×930 mm PASS|`cad/generation/assembly_metadata.json`|
|B-Rep topology|active 181, failure 0|`validation/results/solid_topology.json`|
|Print mesh|12 watertight manifold, failure 0|`validation/results/mesh_manifold.json`|
|Slicing|support 포함 904.60 g, 81.7 h; reserve 포함 1,013.15 g|`validation/results/slicer_results.json`|
|Throughput|PLA 18 rpm 111.8, PET 20 rpm 108.4 g/h nominal|`simulation/engineering_summary.json`|
|OpenModelica|18 scenario + 6 sensitivity sweep PASS|`simulation/openmodelica/results/summary.json`|
|Dynamic load|22 N·m fuse, 1.255 kN bearing, 0.603 kN chain, 0.485 kN anchor tension|`dynamic_load_envelope.json`|
|Structure|9 screening + 2 CalculiX PASS|`analysis/structural/results/structural_screening.json`|
|Firmware|baseline hash sync, unverified calibration start reject|host tests/generated header|
|Budget|178,137 target; 198,137 reserve 포함; 계획 여유 1,863|`bom/cash_budget.csv`|
|Artifact 재현성|전체 manifest normalized hash PASS|`validation/results/artifact_reproducibility.json`|

OpenModelica cutter load는 Gate-1 이전 surrogate다. CalculiX는 linear-elastic global screening이며 실제 impact/notch/fatigue/safety certification을 대체하지 않는다. 200 g/h는 stretch target이고 diameter accuracy도 physical calibration 전 claim하지 않는다.

## Physical lock

`validation/physical_gate_status.json`은 Gate-1, screw coupon, barrel coupon을 모두 `NOT_RUN`으로 유지한다. CUT-01 2장 coupon 외 full cutter stack, full EX-SCR-01/EX-BAR-01과 main fast-forward는 허용되지 않는다.
