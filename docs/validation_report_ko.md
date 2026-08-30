# 자동검증 보고 — virtual-physics-closure-v0.5.1

- release: `DIGITAL_FABRICATION_BASELINE`
- virtual physics: `VIRTUAL_PHYSICS_VALIDATED`
- empirical: `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- architecture: `compact-single-path-v0.3` 유지

|Gate|현재 디지털 결과|근거|
|---|---|---|
|Envelope|470 × 700 × 930 mm|`cad/generation/assembly_metadata.json`|
|Pairwise collision|13,203 pair, allowed interface 12, unexpected 0|`validation/results/assembly_pairwise_collisions.json`|
|Print|12 family, planning mass ≤1.5 kg|`validation/results/slicer_results.json`|
|OpenModelica|mandatory coupled 55 scenario PASS|`simulation/openmodelica/results/summary.json`|
|Dynamic load|cutter 21.994 N·m, phase 16.220 N·m, bearing 1.293 kN, chain 0.603 kN|`simulation/openmodelica/results/dynamic_load_envelope.json`|
|Throughput/forming|PLA 16 rpm 99.4, PET 18 rpm 97.5 g/h virtual default; 200 g/h stretch|`simulation/engineering_summary.json`|
|Power/thermal|normal phase peak max 490 W ≤500 W, minimum PSU reserve 110 W|`simulation/engineering_summary.json`|
|Structure|10 closed-form + 2 CalculiX; local 2040 frame; thermocouple blind6 SF 2.00|`analysis/structural/results/structural_screening.json`|
|Budget|173,729 target; 193,729 reserve 포함; 계획 여유 6,271|`bom/cash_budget.csv`|
|Gate-1 package|25 torque rows, 6 jam trials, 2 chip batches; `OPTIONAL_NOT_RUN`|`validation/results/gate1_readiness.json`|

55 scenario PASS는 선택한 reduced-order 방정식과 가정 안의 가상 검증이다. 실제 PLA/PET 절단토크, chip size, melt flow와 filament tolerance를 측정했다는 뜻이 아니다. Optional Gate-1 미수행은 `main`을 차단하지 않지만 full cutter/screw-barrel 발주와 commissioning은 사용자 승인 전 잠겨 있다.
