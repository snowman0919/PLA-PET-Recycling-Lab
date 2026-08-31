# 자동검증 보고 — parallel-actuation-hardening-v0.6.2

- release: `ACTUATION_HARDENING_COMPLETE`
- implementation: `PASS`
- virtual shadow validation: `PASS`
- Fusion result integration: `PENDING_EXTERNAL_EXECUTION`
- main merge: `BLOCKED_PENDING_FUSION`
- physical validation: `NOT_RUN`

|v0.6.2 Gate|현재 디지털 결과|근거|
|---|---|---|
|Frozen Fusion input|v0.6.1 frozen path diff 0, `FUSION_INPUT_DELTA=NONE`|`validation/results/fusion_delta_classification.json`|
|Firmware actuation|puller/screw/fan/spooler/traverse 실제 feedback path와 히터 applied-duty anti-windup host test PASS|`firmware/arduino_mega/tests`, `validation/results/v062_runtime_audit.json`|
|Mega target|compile PASS; flash 44,774 B(17%), global 2,146 B(26%), local/stack 여유 6,046 B|`validation/results/arduino_mega_compile.json`|
|Runtime|production `MachineSupervisor` 43 scenario/116 trace PASS; actual screw tach purge evidence|`validation/results/runtime_supervisor.json`|
|Mutation|고위험 false-PASS mutation 7/7 검출|`validation/results/v062_mutation_tests.json`|
|OpenModelica shadow|DASSL 24/24 PASS; frozen 구조 envelope 4개 peak delta 0|`simulation/openmodelica/results_v0.6.2/summary.json`, `analysis/fusion_delta_queue/shadow_envelope_comparison.json`|
|Process risk|shredder/airflow `MITIGATION_REQUIRED`; feed `MODEL_INSUFFICIENT`|`analysis/process_risk/process_risk_summary.json`|
|Fusion intake|빈 외부 result manifest는 pending 유지; stale/mismatch/binding rejection unit test PASS|`analysis/cross_solver/fusion_import_review.json`, `analysis/cross_solver/test_import_fusion_results.py`|
|Budget|conditional 178,729; reserve 포함 198,729; verified `NOT_ESTABLISHED`|`bom/verified_budget.csv`|
|CI|CI-LIGHT/CI-FULL PASS; Fusion solve 완료 주장은 명시적으로 false|`validation/results/ci_light_v062.json`, `validation/results/ci_full_v062.json`|

## v0.6.2 해석 경계

- purge 완료 회전수는 screw tach의 누적 실제 회전수로 gate한다. 다만 tach PPR·축 결합은 실물 교정 전이므로 물리 검증 완료가 아니다.
- shredder particle, hopper/feed, airflow 수치는 seeded reduced-order screening이다. 실제 flake 크기, polymer flow, filament tolerance 또는 생산 신뢰성의 측정값이 아니다.
- 외부 Fusion result file이 아직 없어 imported case는 0이고 binding/correlation은 pending이다. 가상의 응력·변위 값을 채우지 않았다.
- 구매·가공·통전·cutter/screw/heater 시험은 수행하지 않았다. 물리 lockout과 사용자 확인 없이는 검증 완료로 승격하지 않는다.

---

## v0.6.1 기준선 기록

- release: `SAFETY_ORCHESTRATION_BASELINE`
- implementation: `IMPLEMENTATION_BASELINE`
- virtual physics: `VIRTUAL_PHYSICS_VALIDATED`
- empirical: `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- cross solver: `CROSS_SOLVER_VALIDATION_PENDING`
- geometry: v0.6 SHA `60ccd92fe9a7df35b550a2a57649b1263da09d10`에서 변경 없음

|Gate|현재 디지털 결과|근거|
|---|---|---|
|Envelope|470 × 700 × 930 mm|`cad/generation/assembly_metadata.json`|
|Geometry/print|closed B-Rep, unexpected collision 0, 12 print family, planning mass 1,012.70 g|`validation/results/*`, `exports/print/print_manifest.csv`|
|Firmware|pure C++ `MachineSupervisor`, host 7/7, Mega 2560 compile PASS|`firmware/arduino_mega`, `validation/results/arduino_mega_compile.json`|
|Runtime|production-linked 43 scenarios/116 traces, invariant failure 0, fixed 4×64 bounded events PASS|`validation/results/runtime_supervisor.json`|
|Red-team|false-PASS mutation 14/14 검출|`validation/results/red_team_orchestration.json`|
|Contract|11 process phases, 8 power phases, firmware/Modelica drift 0|`validation/results/orchestration_contract.json`|
|OpenModelica|mandatory 111/111 PASS, failure 0; rundown response 0.1 s, quality requalification entry→READY 27.8 s|`simulation/openmodelica/results/summary.json`|
|Power|독립 계산 8 phases PASS; 최대 477.2 W, 최소 reserve 122.8 W|`calculations/orchestration_power.json`|
|Dynamic load|cutter 21.994 N·m, phase 20.000 N·m, bearing 1.857 kN, chain 0.603 kN|`simulation/openmodelica/results/dynamic_load_envelope.json`|
|Structure|10 closed-form + 2 CalculiX×3 mesh; 변위 수렴 1.1644%/0.3119%|`analysis/structural/results/structural_screening.json`|
|Fusion handoff|STEP 9, LC01–LC10 모두 rerun/PENDING, exact engineering-source hash binding|`exports/fusion_validation/run_binding.json`|
|Budget|v0.6.2 conditional 178,729; reserve 포함 198,729; 계획 여유 1,271 KRW; verified `NOT_ESTABLISHED`|`bom/verified_budget.csv`|

## 안전 orchestration 정량 경계

- Fan-first start: healthy feedback 1.5 s 연속, timeout 3.0 s; proof 전 heater와 모든 motion 0.
- Purge: feed 승인과 waste-path 확인을 분리하고 120 s/32 command-derived revolution, stable temperature, no fault, 시각 확인을 요구한다.
- Hot purge 종료: STOP/PAUSE와 성공 완료 모두 validated cooling으로 T1–Tdie 60 °C 이하까지 `COOLDOWN`; E-stop은 즉시 all-zero.
- Requalification: 20 valid samples, U95 ≤0.03 mm, 직경/ovality ≤0.05 mm 각 10 s, puller 비포화, cooling valid, transport PLA/PET 26.7/28.6 s, explicit rethread.
- Dancer: warning/controlled stop/hard stop 0.32/0.36/0.4363 rad. Hard-stop contact는 sensitivity에서만 허용한다.
- Empty/Half/Full jam peak dancer angle은 0.37228/0.37227/0.37226 rad이며 hard stop은 접촉하지 않았다. Prelimit scenario peak는 0.43535 rad에서 contact 없이 정지했고, sensitivity-only hard-stop peak는 0.44573 rad/reaction 0.6108 N·m이다.
- Gauge dropout의 maximum diameter error 0.5425 mm, out-of-tolerance 8.8 s, recovery 85.8 s였으며 invalid 구간 spool eligibility는 전체 0이다. 이는 품질 PASS가 아니라 containment/requalification PASS다.
- Purge revolution은 `COMMAND_DERIVED_ESTIMATE_NOT_MEASURED`; 80 g/120 g도 measured mass가 아니다.

최종 commit의 CI-LIGHT/CI-FULL은 깨끗한 clone에서 다시 실행하며 exact SHA, OpenModelica scenario count, artifact count와 mismatch count를 release commit 밖의 exact-head evidence에 기록한다. 저장된 과거 PASS 또는 dirty-tree 진단은 release 증거로 사용하지 않는다.

이 검증은 실제 fan airflow, 절단 성능, melt flow, filament tolerance, Fusion solve 또는 하드웨어 safety chain 시험이 아니다. `CROSS_SOLVER_GATE`는 PENDING이고 구매·가공·통전·commissioning은 모두 `USER_APPROVAL_REQUIRED`다.
