# 자동검증 보고 — coupled-digital-validation-v0.5

- release: `DIGITAL_GEOMETRY_AND_SURROGATE_BASELINE`
- physical: `PHYSICAL_NOT_RUN`
- architecture: `compact-single-path-v0.3` 유지

|Gate|현재 디지털 결과|근거|
|---|---|---|
|Envelope|470 × 700 × 930 mm|`cad/generation/assembly_metadata.json`|
|Pairwise collision|13,041 pair, unexpected 0|`validation/results/assembly_pairwise_collisions.json`|
|Print|12 family, planning mass ≤1.5 kg|`validation/results/slicer_results.json`|
|OpenModelica|coupled 32 scenario PASS|`simulation/openmodelica/results/summary.json`|
|Dynamic load|cutter 21.994 N·m, phase 16.216 N·m, bearing 1.797 kN, chain 0.603 kN|`simulation/openmodelica/results/dynamic_load_envelope.json`|
|Throughput|PLA 18 rpm 111.8, PET 20 rpm 108.4 g/h nominal; 200 g/h stretch|`simulation/engineering_summary.json`|
|Power/thermal|360 W heater, extrusion active peak 490 W < 600 W|`simulation/engineering_summary.json`|
|Budget|170,629 target; 190,629 reserve 포함; 계획 여유 9,371|`bom/cash_budget.csv`|
|Gate-1 package|25 torque rows, 6 jam trials, 2 chip batches; physical NOT_RUN|`validation/results/gate1_readiness.json`|

32 scenario PASS는 사용한 방정식과 가정의 일관성만 뜻한다. 실제 PLA/PET 절단토크, jam recovery, chip size, melt flow, thermal safety와 filament 품질은 증명하지 않는다. Gate-1 signed raw evidence 전 full CUT-01 stack과 full screw/barrel 발주, `main` 승격은 잠겨 있다.
