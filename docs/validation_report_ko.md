# 자동검증 보고 — implementation-crosssolver-v0.6

- release: `IMPLEMENTATION_BASELINE`
- virtual physics: `VIRTUAL_PHYSICS_VALIDATED`
- empirical: `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- cross solver: `CROSS_SOLVER_VALIDATION_PENDING`
- architecture: `compact-single-path-v0.3` 유지

|Gate|현재 디지털 결과|근거|
|---|---|---|
|Envelope|470 × 700 × 930 mm|`cad/generation/assembly_metadata.json`|
|Pairwise collision|13,203 pair, allowed interface 12, unexpected 0|`validation/results/assembly_pairwise_collisions.json`|
|Print|12 family, planning mass ≤1.5 kg|`validation/results/slicer_results.json`|
|OpenModelica|mandatory coupled 74 scenario PASS|`simulation/openmodelica/results/summary.json`|
|Arduino Mega|Mega 2560 compile + heater/gauge/UI/process/shredder host tests PASS|`validation/results/arduino_mega_compile.json`|
|Dynamic load|cutter 21.994 N·m, phase 20.000 N·m, bearing 1.857 kN, chain 0.603 kN|`simulation/openmodelica/results/dynamic_load_envelope.json`|
|Throughput/forming|PLA 16 rpm 99.4, PET 18 rpm 97.5 g/h virtual default; 200 g/h stretch|`simulation/engineering_summary.json`|
|Power/thermal|normal phase peak max 490 W ≤500 W, minimum PSU reserve 110 W|`simulation/engineering_summary.json`|
|Structure|10 closed-form + 2 CalculiX×3 mesh; displacement convergence 1.1644%/0.3119%; thermocouple blind5.5 ligament 3.4 mm|`analysis/structural/results/structural_screening.json`|
|Fusion handoff|STEP 9, LC01–10, study 7종, hash binding PASS; 실제 solve PENDING|`exports/fusion_validation/run_binding.json`|
|Budget|173,729 target; 193,729 reserve 포함; 계획 여유 6,271|`bom/cash_budget.csv`|
|Gate-1 package|25 torque rows, 6 jam trials, 2 chip batches; `OPTIONAL_NOT_RUN`|`validation/results/gate1_readiness.json`|

74 scenario와 CalculiX PASS는 선택한 가상 방정식·경계조건 안의 결과다. Fusion 결과와 실제 PLA/PET 절단토크, chip size, melt flow, filament tolerance는 측정되지 않았다. Optional Gate-1 미수행은 implementation baseline을 차단하지 않지만 cross-solver gate는 외부 Fusion 결과 전 PENDING이고, full cutter/screw-barrel 발주와 commissioning은 사용자 승인 전 잠겨 있다.
