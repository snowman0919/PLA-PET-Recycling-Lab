# 요구사항 준수·증거 매트릭스

기준일: 2026-08-28. 이 표는 설계 증거와 물리 합격을 분리한다. `AUTOMATED_PASS`는 현재 저장소에서 완결된 검사/문서 gate, `DESIGN_EVIDENCE`는 구현·해석 증거가 있으나 물리 T/D가 열린 상태, `PHYSICAL_OPEN`은 성능 측정이 핵심인 상태, `BLOCKED_EXTERNAL`은 donor·선정부품·견적 없이는 닫을 수 없는 상태다.

## 집계

| 상태 | 수 |
|---|---:|
| AUTOMATED_PASS | 3 |
| BLOCKED_EXTERNAL | 6 |
| DESIGN_EVIDENCE | 30 |
| PHYSICAL_OPEN | 4 |

총 43개 요구사항이다. 물리 시험이나 외부 증거가 필요한 행은 자동 검사 통과로 닫지 않는다.

## 추적표

| ID | 판정 | 로컬 증거 | 자동 증거 | 남은 검증 | 책임 |
|---|---|---|---|---|---|
| REQ-FUNC-001 | DESIGN_EVIDENCE | `requirements/constraints.md`<br>`docs/operation.md`<br>`software/raspberry_pi/config/recipes.json` | `software/raspberry_pi/tests/test_pi_core.py` | PLA and PET batch demonstration | User |
| REQ-FUNC-002 | DESIGN_EVIDENCE | `software/raspberry_pi/recycler/classifier.py`<br>`docs/operation.md` | `software/raspberry_pi/tests/test_pi_core.py` | Calibrated unknown and TPU sample reject demonstration | User |
| REQ-FUNC-003 | DESIGN_EVIDENCE | `software/raspberry_pi/recycler/classifier.py`<br>`firmware/arduino_mega/src/control_core.cpp`<br>`electronics/protocol/frp1.md` | `software/raspberry_pi/tests/test_pi_core.py`<br>`firmware/arduino_mega/tests/test_control_core.cpp` | Calibrated camera current tach and vibration fusion trace | User |
| REQ-FUNC-004 | DESIGN_EVIDENCE | `software/raspberry_pi/recycler/classifier.py`<br>`cad/freecad/input_classifier/geometry.py` | `software/raspberry_pi/tests/test_pi_core.py`<br>`validation/test_input_classifier_geometry.py` | Physical color calibration and seven-bin routing | User |
| REQ-FUNC-005 | DESIGN_EVIDENCE | `decisions/ADR-003-stage1-narrow-throat-drive.md`<br>`decisions/ADR-005-stage2-single-rotor-bed-knife.md`<br>`decisions/ADR-006-stage3-screen-family.md` | `validation/test_stage1_kinematics.py`<br>`validation/test_stage2_kinematics.py`<br>`validation/test_stage3_kinematics.py` | Three-stage material size samples | User |
| REQ-FUNC-006 | DESIGN_EVIDENCE | `decisions/ADR-007-two-deck-vibratory-sorter.md`<br>`cad/freecad/vibratory_sorter/geometry.py` | `validation/test_sorter_geometry.py` | Physical three-stream separation demonstration | User |
| REQ-FUNC-007 | DESIGN_EVIDENCE | `calculations/thermal/dryer_feeder.md`<br>`software/raspberry_pi/config/recipes.json`<br>`firmware/arduino_mega/filament_recycler_mega.ino` | `validation/test_dryer_feeder_budget.py`<br>`firmware/arduino_mega/tests/test_sketch_compile.cpp` | Temperature dew-point moisture and mass-feed logs | User |
| REQ-FUNC-008 | DESIGN_EVIDENCE | `docs/operation.md`<br>`software/raspberry_pi/recycler/supervisor.py` | `software/raspberry_pi/tests/test_pi_core.py` | UI interlock and purge-waste path demonstration | User |
| REQ-FUNC-009 | DESIGN_EVIDENCE | `decisions/ADR-009-18mm-single-screw-extruder.md`<br>`calculations/extruder/screw_design.md` | `validation/test_extruder_design.py` | Stable PLA and PET extrusion runs | User |
| REQ-FUNC-010 | DESIGN_EVIDENCE | `calculations/forming/line_design.md`<br>`software/raspberry_pi/recycler/diameter.py` | `validation/test_forming_line.py`<br>`software/raspberry_pi/tests/test_pi_core.py` | Traceable dual-axis gauge calibration and log | User |
| REQ-FUNC-011 | DESIGN_EVIDENCE | `decisions/ADR-010-air-cooled-dual-view-forming-line.md`<br>`software/raspberry_pi/recycler/supervisor.py` | `validation/test_forming_line.py` | Physical puller step response | User |
| REQ-FUNC-012 | DESIGN_EVIDENCE | `calculations/forming/line_design.md`<br>`cad/freecad/spooler/geometry.py` | `validation/test_spooler_geometry.py` | Full one-kilogram spool winding demonstration | User |
| REQ-FUNC-013 | DESIGN_EVIDENCE | `decisions/ADR-002-safety-authority-and-power-phases.md`<br>`electronics/protocol/frp1.md`<br>`firmware/arduino_mega/src/control_core.cpp` | `firmware/arduino_mega/tests/test_control_core.cpp`<br>`software/raspberry_pi/tests/test_pi_core.py` | Physical Pi cable removal safe-stop test | User |
| REQ-FUNC-014 | DESIGN_EVIDENCE | `software/raspberry_pi/recycler/history.py`<br>`software/raspberry_pi/recycler/dataset.py` | `software/raspberry_pi/tests/test_pi_core.py` | Production batch export using calibrated measurements | User |
| REQ-PERF-001 | PHYSICAL_OPEN | `validation/test_plans/extruder_coupon.md`<br>`docs/validation_report_ko.md` | `validation/test_extruder_design.py` | Thirty-minute mass-balance at or above 200 g per hour | User |
| REQ-PERF-002 | PHYSICAL_OPEN | `validation/test_plans/forming_line_coupon.md`<br>`docs/calibration.md` | `validation/test_forming_line.py` | Thirty-minute calibrated diameter record within 1.70 to 1.80 mm | User |
| REQ-PERF-003 | PHYSICAL_OPEN | `calculations/forming/line_design.md`<br>`validation/test_plans/forming_line_coupon.md` | `validation/test_forming_line.py` | Measured improved tolerance and ovality evidence | User |
| REQ-PERF-004 | DESIGN_EVIDENCE | `calculations/thermal/dryer_feeder.md`<br>`cad/freecad/input_classifier/geometry.py` | `validation/test_dryer_feeder_budget.py`<br>`validation/test_input_classifier_geometry.py` | Mass capacity and physical anti-reach refill test | User |
| REQ-MECH-001 | DESIGN_EVIDENCE | `cad/freecad/input_classifier/geometry.py`<br>`requirements/constraints.md` | `validation/test_input_classifier_geometry.py` | Physical 200 by 200 fixture and 500 mL bottle passage test | User |
| REQ-MECH-002 | DESIGN_EVIDENCE | `docs/design_report_ko.typ`<br>`cad/freecad/full_assembly/generate.py` | `validation/test_cad_generation.py` | Assembly inspection of metal load path and frame joints | User |
| REQ-MECH-003 | AUTOMATED_PASS | `cad/parameters/baseline.json`<br>`validation/test_cad_generation.py` | `validation/test_cad_generation.py` | None for current generated geometry | Codex |
| REQ-MECH-004 | DESIGN_EVIDENCE | `calculations/shredder/stage1_proof_design.md`<br>`exports/drawings/stage1_cutter_notes.md` | `validation/test_stage1_kinematics.py` | Measured shim stack and loaded-clearance test | User |
| REQ-MECH-005 | DESIGN_EVIDENCE | `calculations/shredder/stage1_proof_design.md`<br>`calculations/forming/line_design.md`<br>`calculations/structural/beam_fea.md`<br>`simulation/structural/beam_crosscheck.json` | `validation/test_stage1_kinematics.py`<br>`validation/test_spooler_geometry.py`<br>`validation/test_structural_beam_fea.py` | 3D mesh/contact/notch/joint convergence and loaded physical confirmation | Codex and User |
| REQ-MECH-006 | DESIGN_EVIDENCE | `exports/drawings/stage1_bearing_plate_notes.md`<br>`exports/drawings/extruder_notes.md`<br>`docs/maintenance.md` | `validation/test_cad_generation.py` | Tool-access and module-removal physical review | User |
| REQ-THERM-001 | DESIGN_EVIDENCE | `calculations/extruder/screw_design.md`<br>`firmware/arduino_mega/filament_recycler_mega.ino` | `validation/test_extruder_design.py`<br>`firmware/arduino_mega/tests/test_sketch_compile.cpp` | Zone sensor heater and recipe commissioning trace | User |
| REQ-THERM-002 | PHYSICAL_OPEN | `calculations/thermal/dryer_feeder.md`<br>`electronics/schematics/safety_power_control.md` | `validation/test_dryer_feeder_budget.py` | Worst-case thermocouple test on guards and polymer housings | User |
| REQ-PWR-001 | BLOCKED_EXTERNAL | `requirements/assumptions.md`<br>`calculations/power/power_budget.csv` | `validation/test_electronics_interfaces.py` | PSU label terminal inspection and measured branch budget | User |
| REQ-PWR-002 | DESIGN_EVIDENCE | `calculations/controls/safety_timing.md`<br>`firmware/arduino_mega/src/control_core.cpp` | `firmware/arduino_mega/tests/test_control_core.cpp` | Instrumented phase and branch-current fault test | User |
| REQ-INT-001 | DESIGN_EVIDENCE | `electronics/pinout/mega_pinout.csv`<br>`electronics/wiring/harness_schedule.csv` | `validation/test_electronics_interfaces.py` | Finished-harness continuity insulation and earth tests | User |
| REQ-INT-002 | DESIGN_EVIDENCE | `electronics/protocol/frp1.md`<br>`firmware/arduino_mega/src/protocol.cpp` | `firmware/arduino_mega/tests/test_control_core.cpp`<br>`software/raspberry_pi/tests/test_pi_core.py` | Physical USB dropout and noise injection | User |
| REQ-SAFE-001 | BLOCKED_EXTERNAL | `electronics/schematics/safety_power_control.md`<br>`firmware/arduino_mega/src/control_core.cpp` | `firmware/arduino_mega/tests/test_control_core.cpp` | Controller-fault hardware energy-isolation test with selected relay and contactor | User |
| REQ-SAFE-002 | DESIGN_EVIDENCE | `electronics/schematics/safety_power_control.md`<br>`electronics/pinout/mega_pinout.csv` | `validation/test_electronics_interfaces.py` | Wire-open and cover-open hard-enable test | User |
| REQ-SAFE-003 | DESIGN_EVIDENCE | `cad/freecad/input_classifier/geometry.py`<br>`docs/safety.md` | `validation/test_input_classifier_geometry.py` | Standardized physical reach probe and fragment-containment test | User |
| REQ-SAFE-004 | BLOCKED_EXTERNAL | `electronics/schematics/safety_power_control.md`<br>`firmware/arduino_mega/src/control_core.cpp` | `firmware/arduino_mega/tests/test_control_core.cpp` | Independent fuse high-limit and welded-driver fault tests | User |
| REQ-SAFE-005 | DESIGN_EVIDENCE | `calculations/controls/safety_timing.md`<br>`firmware/arduino_mega/src/control_core.cpp` | `firmware/arduino_mega/tests/test_control_core.cpp` | Low-energy physical jam and coast-down demonstration | User |
| REQ-SAFE-006 | BLOCKED_EXTERNAL | `firmware/arduino_mega/src/configuration.h`<br>`firmware/arduino_mega/src/control_core.cpp`<br>`docs/calibration.md` | `firmware/arduino_mega/tests/test_control_core.cpp` | Full physical fault-injection matrix after sensor selection | User |
| REQ-SAFE-007 | DESIGN_EVIDENCE | `docs/safety.md`<br>`docs/maintenance.md`<br>`cad/freecad/full_assembly/generate.py` | `validation/test_cad_generation.py` | Guard inspection and lockout procedure demonstration | User |
| REQ-SAFE-008 | DESIGN_EVIDENCE | `docs/operation.md`<br>`docs/safety.md`<br>`requirements/constraints.md` | `validation/test_release_package.py` | Implemented TFT startup acknowledgement and physical UI review | Codex and User |
| REQ-COST-001 | BLOCKED_EXTERNAL | `bom/target_budget_design.csv`<br>`bom/cost_rollup.csv`<br>`bom/cost_evidence.csv` | `validation/test_bom.py` | Landed quotes and validated stock proving total at or below 200000 KRW | User |
| REQ-COST-002 | BLOCKED_EXTERNAL | `bom/cost_rollup.csv`<br>`exports/cnc_quote_packages/README.md`<br>`requirements/responsibility_matrix.md` | `validation/test_bom.py`<br>`validation/test_cnc_quote_packages.py` | Final fabrication-release drawings and actual quotes totaling at or below 100000 KRW | Codex and User |
| REQ-COST-003 | AUTOMATED_PASS | `bom/target_budget_design.csv`<br>`bom/engineering_recommended_design.csv`<br>`bom/cost_analysis.md` | `validation/test_bom.py` | None for document separation; prices remain external | Codex |
| REQ-DOC-001 | AUTOMATED_PASS | `cad/generation/generate_all.py`<br>`artifacts/manifest.json`<br>`docs/validation_report_ko.md` | `validation/test_cad_generation.py`<br>`validation/test_release_package.py` | None for current package; FreeCAD runtime must be provisioned for each rebuild | Codex |
| REQ-DOC-002 | DESIGN_EVIDENCE | `docs/build_manual_ko.pdf`<br>`bom/bom.csv`<br>`electronics/pinout/mega_pinout.csv`<br>`docs/calibration.md`<br>`docs/operation.md`<br>`docs/maintenance.md`<br>`docs/validation_report_ko.md` | `validation/test_release_package.py` | Independent third-party fabrication document review | User |

## 해석 제한

- 이 매트릭스는 요구사항 누락을 드러내기 위한 감사표이며 CE/UL/KC 또는 기계안전 인증서가 아니다.
- `DESIGN_EVIDENCE`와 `PHYSICAL_OPEN`은 release 승인과 동의어가 아니다.
- 사용자 승인 없는 구매·CNC 주문·고전류 통전은 수행하지 않는다.
