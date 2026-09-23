# Graph Report - PPR-c2.1-codex-20260921  (2026-09-23)

## Corpus Check
- Large corpus: 1069 files · ~3,419,144 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 1730 nodes · 3109 edges · 192 communities (95 shown, 97 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 273 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- c2.1/src/build_cad.py
- test_telemetry.py
- test_contract.py
- i6_surrogate.py
- s1_event
- Inputs
- performance.py
- TestD4Ledger
- TestNullStatus
- TestD4Faults
- S2
- i3_coupon.py
- architectures.py
- d2_torque.py
- generate
- bonds.py
- ControllerTests
- Thermal
- bond_manager.py
- screen_open_area
- test_vp1_stage1.py
- i4_screen.py
- controller_core.cpp
- Outputs
- TestVerifier
- test_r03_causality.py
- DesignContracts
- Limits
- BondManager
- Controller
- MaterialPathApertures
- check_baseline_present
- GearRatioKinematics
- test_architectures.py
- MissingEvidenceError
- chute.py
- winder.py
- traceback
- _rect_prism
- verify_contract.py
- aggregate_r1.py
- drive_kinematics.py
- main
- sys
- pathlib
- unittest
- os
- aggregate_r2.py
- convergence.py
- math
- gap_screen_sweep.py
- render_cad.py
- argparse
- d4_accounting.py
- run_case.py
- run_full
- full_machine.py
- build_freecad.py
- run_study.py
- flow_localize.py
- d1_contact.py
- run_r1.py
- build_machine_integration.py
- path_check.py
- run_r4_t2b.py
- run_r2.py
- make_drawings.py
- emit_usd.py
- d0_clock.py
- d3_bond.py
- build_system_bom.py
- power_sim.py
- c2/src/build_cad.py
- run_r3.py
- analyze.py
- json
- build_release_manifest.py
- build_machine_wiring.py
- test_dynamics.py
- drive_teeth.py
- design.py
- C2.2 — VP1 전체 기계 Isaac Sim 검증
- PPR_C2_1_machine_wiring_erc.json
- ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)
- C2.3-A-R3 리뷰 핸드오프 (판정 요청)
- C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)
- REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)
- C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F
- convergence/manifest.json
- r2/manifest.json
- r3/manifest.json
- PPR-KODEX (영구 규칙 · 목표)
- PPR VP1 현재 상태 (2026-09-23)
- C2.2 VP1 실행 씬 출처와 증거 경계
- Param Trace Document
- Amendment Log
- CONTRACT (superseded)
- Contract Baseline Cutter Gap
- Contract Baseline q
- Contract Baseline Screen Aperture
- Next Checkpoint Plan
- Requirements Evidence
- Review Handoff Summary
- CONTRACT R1
- Material Calibration Evidence
- Motor and Driver RFQ Evidence
- Unsubmitted DEM Job Queue
- C2 Research and CAD Dependencies
- Contact impulse threshold
- Convergence metrics
- Coupling Window Radius
- dt ladder values
- Forbidden actions in R0
- Fragment / bond-break count threshold
- Baseline S1-A (twin-shaft hook shear)
- Baseline S2-A (q=8, e=7 mm)
- Cutter gap
- Impulse scale
- Friction / gravity / solver iterations
- Initial poses
- Screen aperture
- Frozen waste cases (FDM, PURGE, WRAP)
- USD Asset File
- Goal R0 §2 (Numerical reliability closure)
- Hopper Interior Geometry
- ISAAC_PHYSX backend
- Joint Traversal Path
- Kinematic Frame F0 Definition
- Machine Body Dimensions
- Mass conservation threshold
- Motion Law Equations
- Nominal Motion Parameters
- Probes Created
- Revision R1
- BLOCKED_PERFORMANCE_DATA
- Required artifacts list
- Residence time threshold
- Rigid Body Views
- Smoke8 Run Parameters
- Smoke9 Run Parameters
- Smoke_cfix Run Parameters
- Smoke_fixc Run Parameters
- S1 Cutter Parameters
- S2 Local Frame Definition
- Shaft work threshold
- Simulation Parameters
- Simulation Setup Details
- Simulation Views
- REFERENCE/UNRATED worm, wheel, shafts, bearings and motor
- Stage 5 active chute auger
- Function-preserving integration reliefs
- Host-tested firmware power allocation
- 24V 33A PSU, 500W soft target and 792W current ceiling
- Conservative cycloidal pin-ring screen
- C2.3 tribometer, crown and joint expansion stopped
- AST graph update does not complete semantic extraction
- C2 Engineering Contracts
- PPR C1 Dimensioned Engineering Review Package
- C2.1 S2 Transmission Schematic
- Material-flow HOLD despite localized S2 cap-bore transfer
- Open Physical Actions Register
- VP1 whole-machine Isaac Sim validation
- Fail-Closed Thermal and Jam Control Reference
- PPR C1 CAD Inspection Image
- Single-Input Reverse-Output S2 Drivetrain
- Fixed C2 System Constraints
- Active C2 Baseline
- Base Runtime and CAD Dependencies
- C1 Digital Contracts
- Clause A1 (Steps-per-run)
- Clause A2 (Metrics calculation)
- Clause A3 (Mass conservation)
- Clause A4 (Missing-event handling)
- Clause A5 (Scene provenance)
- Clause A6 (Break/fragment accounting)
- Clause A7 (Threshold applicability)
- Smoke8 Simulation Run
- Smoke9 Simulation Run
- Smoke_cfix Simulation Run
- Smoke_fixc Simulation Run

## God Nodes (most connected - your core abstractions)
1. `S2` - 32 edges
2. `components()` - 29 edges
3. `Transmission` - 28 edges
4. `Inputs` - 26 edges
5. `BondManager` - 26 edges
6. `s1_event()` - 22 edges
7. `generate()` - 22 edges
8. `EvidenceTests` - 20 edges
9. `_box()` - 20 edges
10. `GeometryTests` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Small Pin-Ring Feasibility Screen` --semantically_similar_to--> `S2 Cycloidal Guide, Sleeve, and Pin Rings`  [INFERRED] [semantically similar]
  c2/docs/C2_ENGINEERING_NOTES.md → drawings/PPR_C1_dimensioned_review.pdf
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `Open Physical Actions Register` --semantically_similar_to--> `Nominal Drawing Fabrication Hold`  [INFERRED] [semantically similar]
  c2.1/docs/OPEN_ACTIONS_KO.md → c2.1/drawings/PPR_C2_1_P6_nominal_plate_review.pdf
- `Open Physical Actions Register` --semantically_similar_to--> `Electrical Fabrication and Energization Hold`  [INFERRED] [semantically similar]
  c2.1/docs/OPEN_ACTIONS_KO.md → c2.1/electrical/PPR_C2_1_machine_wiring.pdf
- `Evidence and Safety Boundaries` --semantically_similar_to--> `Safety-Preserving Cost Reduction Order`  [INFERRED] [semantically similar]
  AGENTS.md → c2/docs/CALIBRATION_AND_RFQ.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Connected material-route verification boundary** — c2_1_docs_adr_002_chain_routing_active_auger, c2_1_docs_adr_002_chain_routing_cross_feed_shaft, c2_1_docs_adr_002_chain_routing_connected_transport_hold, c2_2_readme_flow_localization [EXTRACTED 1.00]
- **C1 RFQ-Only Dimensioned Drawing Set** — drawings_ppr_c1_dimensioned_review_drive_and_bearing_plates, drawings_ppr_c1_dimensioned_review_s1_cutter_system, drawings_ppr_c1_dimensioned_review_s2_cycloidal_components, drawings_ppr_c1_dimensioned_review_interface_and_fit_schedules [EXTRACTED 1.00]
- **C2 and C2.1 Numerical Evidence CI Pipeline** — _github_workflows_c2_engineering_c2_numerical_study_step, _github_workflows_c2_engineering_c2_unit_tests_step, _github_workflows_c2_engineering_gp_performance_training_step, _github_workflows_c2_engineering_mlp_performance_training_step, _github_workflows_c2_engineering_c2_artifact_verification_step, _github_workflows_c2_engineering_c2_1_transmission_step, _github_workflows_c2_engineering_c2_1_unit_tests_step, _github_workflows_c2_engineering_c2_1_artifact_verification_step [EXTRACTED 1.00]
- **C2 P5 Thermal and Control Evidence** — c2_docs_c2_engineering_notes_s2_thermal_development_module, c2_docs_c2_engineering_notes_five_node_thermal_circuit, c2_docs_c2_engineering_notes_cad_derived_heat_capacity_bounds, c2_docs_c2_engineering_notes_cooling_fault_sensitivity, c2_docs_c2_engineering_notes_fail_closed_control_reference, c2_docs_c2_engineering_notes_independent_hardware_safety_chain, c2_docs_c2_engineering_notes_p5_digital_thermal_control_boundary [EXTRACTED 1.00]
- **C2 Performance Evidence Gate** — c2_docs_c2_engineering_notes_performance_job_manifest, c2_docs_c2_engineering_notes_qualified_performance_learning_pipeline, c2_docs_c2_engineering_notes_blocked_performance_data, c2_docs_c2_engineering_notes_material_calibration_plan [EXTRACTED 1.00]
- **C2 S2 Geometry Decision Flow** — c2_docs_c2_engineering_notes_s2_parameter_search, c2_docs_c2_engineering_notes_geometry_assembly_screen, c2_docs_c2_engineering_notes_small_pin_ring_feasibility, c2_docs_c2_engineering_notes_split_dual_path_alternative [EXTRACTED 1.00]
- **Diagnostic Outcomes relate to Requirements** — c2_3_revisions_r1_diagnostic_summary [INFERRED 0.85]
- **Digital Evidence Without External Hardware Release** — _github_workflows_c2_engineering_no_hardware_approval_gate, _github_workflows_c2_engineering_dynamic_evidence_count_contract, _github_workflows_c2_engineering_procurement_fabrication_energization_hold_contract [INFERRED 0.95]

## Communities (192 total, 97 thin omitted)

### Community 0 - "c2.1/src/build_cad.py"
Cohesion: 0.06
Nodes (66): Transmission, TransmissionContracts, analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder() (+58 more)

### Community 11 - "test_telemetry.py"
Cohesion: 0.09
Nodes (15): TestConvergence, TestIntegrals, TestLedger, TestRunnerHelpers, aggregate(), load_run(), reject_proxy(), ledger() (+7 more)

### Community 12 - "test_contract.py"
Cohesion: 0.09
Nodes (13): TestContractFrozen, TestEvaluators, check_executor_label(), _forbidden_labels(), reject_proxy(), rel_change(), rel_mass_error(), require_isaac_physx() (+5 more)

### Community 13 - "i6_surrogate.py"
Cohesion: 0.08
Nodes (27): SurrogateInputError, TestDeterminism, TestGroupedSplit, TestInvalidInput, TestParetoDominance, TestRobustnessBounds, TestSchema, bo_search() (+19 more)

### Community 15 - "s1_event"
Cohesion: 0.10
Nodes (22): BenchmarkError, WrapOnlyS2Error, TestInvalidInput, TestMassConservation, TestS1Determinism, TestSameInputIdentity, TestSchema, TestSliverMetric (+14 more)

### Community 16 - "Inputs"
Cohesion: 0.09
Nodes (22): Inputs, aux_demand_W, band_rotation_ms, buffer_full, estop_closed, fan_required, fan_tach_ok, guard_closed (+14 more)

### Community 17 - "performance.py"
Cohesion: 0.10
Nodes (19): EvidenceError, EvidenceTests, candidate_hashes(), canonical_sha256(), evidence_inventory(), main(), nondominated(), training_gate() (+11 more)

### Community 2 - "S2"
Cohesion: 0.16
Nodes (12): S2, GeometryTests, generalized_torque(), hook_polygon(), kinematics(), packaging(), point_jacobian(), polygon_area() (+4 more)

### Community 22 - "i3_coupon.py"
Cohesion: 0.18
Nodes (13): OrderingError, WrapOnlyError, TestOrderingGate, TestWrapOnly, check_ordering(), load_dir_for(), main(), run_combo() (+5 more)

### Community 23 - "architectures.py"
Cohesion: 0.16
Nodes (19): Architecture, InvalidMechanism, TestEnvelope, TestInvalidGap, check_clearance(), check_direction(), check_envelope(), get() (+11 more)

### Community 24 - "d2_torque.py"
Cohesion: 0.08
Nodes (21): TestBoundaryWork, TestD0SubstepMapping, TestD1UnitRule, TestDiagConstants, TestShaftTorque, boundary_work(), _cross(), _dot() (+13 more)

### Community 26 - "generate"
Cohesion: 0.14
Nodes (12): OversizeError, TestFamilyCoverage, TestHopperReject, TestSeedDeterminism, TestThermalIndexBounds, check_admissible(), generate(), main() (+4 more)

### Community 3 - "bonds.py"
Cohesion: 0.15
Nodes (13): Bond, BondGraph, Cell, TestAnisotropyOrdering, TestBondValidity, TestMassConservation, graph_from_meta(), lattice_graph() (+5 more)

### Community 32 - "Thermal"
Cohesion: 0.29
Nodes (5): Thermal, ThermalTests, thermal_duty_run(), thermal_run(), Carry thermal state through batch/fan-fault segments; still uncalibrated.

### Community 34 - "bond_manager.py"
Cohesion: 0.14
Nodes (14): FractureInputError, FractureResult, Fragment, NonphysicalError, _components(), find(), union(), RuntimeError (+6 more)

### Community 36 - "screen_open_area"
Cohesion: 0.50
Nodes (3): TestScreenArea, screen_open_area(), Open-area fraction proxy: hole pitch ~ 2x diameter triangular grid. Returns…

### Community 38 - "test_vp1_stage1.py"
Cohesion: 0.14
Nodes (6): ChainGeometry, ChuteGeometry, GearGeometry, skipUnless, VP1 Stage 1: real drivetrain geometry + S1->S2 chute tests. CAD-dependent tests…, cadquery

### Community 43 - "i4_screen.py"
Cohesion: 0.18
Nodes (11): ScreenInputError, TestHopperGate, TestSamplerDeterminism, lhs(), main(), sample_candidates(), screen_candidate(), validate_mechanisms() (+3 more)

### Community 45 - "controller_core.cpp"
Cohesion: 0.22
Nodes (10): PowerDevice, band_count(), main(), safe_inputs(), array, name, W, cassert (+2 more)

### Community 47 - "Outputs"
Cohesion: 0.18
Nodes (11): Outputs, admitted_W, aux_enable, fans_enable, h100_enable, h60_enable, m1_enable, m2_enable (+3 more)

### Community 50 - "test_r03_causality.py"
Cohesion: 0.13
Nodes (5): TestAtomicVsComponent, TestD3Distinguishability, TestDiagConstants, TestTimedDisable, R0.3 causality/accounting unit tests (system python3, isaac-free). >= 10 tests:…

### Community 57 - "Limits"
Cohesion: 0.22
Nodes (8): Limits, jam_current_A, jam_minimum_rpm, maximum_temperature_C, power_ceiling_W, power_target_W, stale_feedback_ms, uint32_t

### Community 6 - "BondManager"
Cohesion: 0.19
Nodes (11): BondManager, TestDeterminism, TestInvalidInput, TestMassConservation, TestOrientationDependence, TestSummarySchema, TestW1ZFirst, TestW4Isotropy (+3 more)

### Community 60 - "Controller"
Cohesion: 0.33
Nodes (5): Controller, BAND_ROTATION_PERIOD_MS, latched_, limits_, State

### Community 67 - "check_baseline_present"
Cohesion: 0.50
Nodes (3): TestBaselinePresent, check_baseline_present(), validate_all()

### Community 75 - "test_architectures.py"
Cohesion: 0.17
Nodes (8): TestBaselinePresent, TestContractEquality, TestS2ADirection, TestScreenOutput, comparison_contract(), s2a_direction_phi(), S2-A law: phi = -theta/q (reverse, sign -1)., I4 architecture + screening regressions (Isaac-independent). Evidence:…

### Community 80 - "MissingEvidenceError"
Cohesion: 0.33
Nodes (6): MissingEvidenceError, TestMissingEvidence, require_calibrated_strength(), RuntimeError, Raised when calibrated (measured) strength data is requested. No physical…, Calibrated fracture strength lookup — always fails loudly (no data).

### Community 1 - "chute.py"
Cohesion: 0.05
Nodes (76): auger_bearings(), auger_shaft(), auger_wheel(), _box(), bypass_channel_floor(), bypass_wall_north_lower(), bypass_wall_south(), _c21_transform() (+68 more)

### Community 10 - "winder.py"
Cohesion: 0.11
Nodes (37): _box(), components(), _cyl(), _flange(), nip_opening_mm(), nip_range_mm(), pull_frame(), pull_motor_ref() (+29 more)

### Community 14 - "traceback"
Cohesion: 0.25
Nodes (6): fail(), main(), Gate A loader: open c2.2/sim/assets/usd/machine.usda headless, report stage…, I0 SimulationApp smoke: headless stage + one rigid cube, 60 physics steps. Gate…, # NOTE: close() os._exit()s via fast shutdown on success, so the JSON, traceback

### Community 167 - "_rect_prism"
Cohesion: 0.67
Nodes (3): run(), _rect_prism(), Straight chain run: 11 mm radial x 5 mm axial prism from t1 to t2.

### Community 168 - "verify_contract.py"
Cohesion: 0.32
Nodes (11): check_config_hashes(), check_convergence(), check_ladder(), check_mass(), check_runs(), check_work_impulse(), main(), scan_banned() (+3 more)

### Community 169 - "aggregate_r1.py"
Cohesion: 0.25
Nodes (8): aggregate_run(), load_thresholds(), main(), eval_metric(), rel_change(), Gate F follow-on: refit surrogate anchors on REAL dynamics data (additive).…, R1.4 aggregation + convergence evaluation (reads runs, never reruns).…, glob

### Community 170 - "drive_kinematics.py"
Cohesion: 0.27
Nodes (9): chain_length_mm(), sprocket_pitch_radius(), _tangent_data(), _chain_loop(), _sector_prism(), Pure kinematics/math for the VP1 common drive — NO cadquery dependency. Split…, External tangent construction in XZ. Returns the two touch-point 4-tuples, the…, Wrap tube: extrusion of an annular sector (XZ) along +Y. (+1 more)

### Community 171 - "main"
Cohesion: 0.22
Nodes (10): gear_center_distance(), gear_pitch_radius(), ratio_chain(), chain_components(), count_teeth(), main(), Transverse pitch radius of a helical gear (normal module mn)., Kinematic chain from the VP1 Stage 4 layout (teeth counts only). M1 -> DRV-… (+2 more)

### Community 172 - "sys"
Cohesion: 0.22
Nodes (8): build_bond_list(), cell_lattice(), main(), Gate B: PhysX S1 twin-shaft (S1-A) + waste fragment clusters + breaking bonds.…, # NOTE: NO use_backend("tensor") scope: the ContactSensor, Recover lattice (nx,ny,nz,dx,dy,dz) by regenerating the specimen., Rebuild 6-neighbourhood lattice bonds matching bonds.lattice_graph., sys

### Community 173 - "pathlib"
Cohesion: 0.27
Nodes (7): evaluate(), main(), _canon(), Full incremental procurement coverage. A missing quotation is not zero cost., Check active C2 evidence and CAD integrity without authorizing hardware., Validate exported STEP topology and volume, not physical performance., pathlib

### Community 174 - "unittest"
Cohesion: 0.20
Nodes (7): chain_center(), cycloid_profile(), gear_section(), hooks(), Deterministic section geometry. Units: millimetres, radians., Reference involute section; root fillets/tolerances NOT a manufacturing profile., unittest

### Community 175 - "os"
Cohesion: 0.22
Nodes (6): Gate C: DERIVED transfer assets (S1 discharge + chute + S2 entry/exit). C2.1…, A4 verifier tests (>=8): tamper detection, recompute checks. Forbidden terminal…, copy, os, shutil, tempfile

### Community 176 - "aggregate_r2.py"
Cohesion: 0.36
Nodes (7): aggregate_run(), load_thresholds(), main(), eval_metric(), rel_change(), R2 aggregate + convergence evaluation (reads runs, never reruns). Primary pair:…, re

### Community 177 - "convergence.py"
Cohesion: 0.53
Nodes (5): epsilon(), evaluate(), _frag_count(), load_thresholds(), A2 convergence evaluator. Thresholds are parsed, NEVER hardcoded. Sources:…

### Community 18 - "math"
Cohesion: 0.18
Nodes (11): design_set(), diverse_selection(), equivalent_motor_load(), main(), C2 deterministic engineering study. Numerical assumptions are not test evidence., Profile validity and full-orbit roller clearance for a compact cycloid…, math, numpy (+3 more)

### Community 180 - "gap_screen_sweep.py"
Cohesion: 0.50
Nodes (4): main(), run(), Gate F: real gap x screen sweep on survivors (thin driver). S1 gap sweep: shaft…, itertools

### Community 181 - "render_cad.py"
Cohesion: 0.40
Nodes (3): Orthographic mesh render of actual BRep parts, not an image-generated concept., pil, trimesh

### Community 19 - "d4_accounting.py"
Cohesion: 0.16
Nodes (19): compare_metrics(), _isaac_child(), jam_status(), main(), make_buckets(), ordered_sum(), passage_status(), reconcile_mass() (+11 more)

### Community 20 - "run_case.py"
Cohesion: 0.15
Nodes (19): build_run_config(), dt_label(), dt_source_mapping(), finalize(), _import_s1(), main(), prepare(), run() (+11 more)

### Community 21 - "run_full"
Cohesion: 0.18
Nodes (14): _bbox(), git_head(), _lod_of(), main(), _reconstruct_parts(), run_full(), _iou(), _vol() (+6 more)

### Community 27 - "full_machine.py"
Cohesion: 0.07
Nodes (35): main(), mesh_volume(), sha256_file(), add_mesh(), convex_hull_of_verts(), decimated_hull(), git_head(), load_stl_verts_faces() (+27 more)

### Community 28 - "build_freecad.py"
Cohesion: 0.23
Nodes (11): main(), read_shape(), build(), face(), primitive(), run(), wire(), Create the native FreeCAD C2.1 machine assembly from checked STEP parts. (+3 more)

### Community 30 - "run_study.py"
Cohesion: 0.16
Nodes (12): allocate_power(), thermal_capacities_from_cad(), thermal_matrix(), _canon(), main(), controller(), polymer(), write_json() (+4 more)

### Community 33 - "flow_localize.py"
Cohesion: 0.06
Nodes (27): main(), run_one_phase(), _ray(), touch_probe(), sha256_file(), zone_analysis(), body_of(), is_by_design() (+19 more)

### Community 37 - "d1_contact.py"
Cohesion: 0.36
Nodes (6): _isaac_child(), main(), run_one(), run_paths(), sha256_file(), D1 contact units + isolation diagnostic (Goal R0 section 4, D1). Exact…

### Community 39 - "run_r1.py"
Cohesion: 0.23
Nodes (10): build_case_geometry(), _isaac_child(), main(), run_case_dt(), run_paths(), sha256_file(), R1 runner: one canonical case at ONE ladder dt, equal 2.4 s physics. Contract:…, # NOTE: Gf.Vector3f hard-crashes (SIGSEGV) in this Isaac build; (+2 more)

### Community 4 - "build_machine_integration.py"
Cohesion: 0.06
Nodes (56): assembly_geometry_checks(), matches(), bbox_overlap(), bounds(), c21_parts(), collision_audit(), extent(), legacy_parts() (+48 more)

### Community 42 - "path_check.py"
Cohesion: 0.24
Nodes (10): _add(), chute_checks(), _dist_to_s2(), downstream_checks(), main(), _screen_aperture(), VP1 material-path geometry checkpoints; not a product-flow certificate.…, Measure the open-arc aperture of the S2 screen at the liner radius. (+2 more)

### Community 44 - "run_r4_t2b.py"
Cohesion: 0.17
Nodes (9): R4-T2b: chain suspended via end posts (FixedJoint), NO pin, gravity + preload…, isaacsim, isaacsim_core_experimental_objects, isaacsim_core_experimental_prims, isaacsim_core_experimental_utils_stage, isaacsim_core_simulation_manager, omni_physx, omni_timeline (+1 more)

### Community 49 - "run_r2.py"
Cohesion: 0.29
Nodes (8): build_case_geometry(), _isaac_child(), main(), run_case_dt(), run_paths(), sha256_file(), R2 runner: per-physics-step contact stream + signed shaft load + boundary work…, R2 Review Handoff Summary

### Community 53 - "make_drawings.py"
Cohesion: 0.19
Nodes (17): dim(), drawshape(), header(), hole_table(), main(), paragraph(), section(), shape2() (+9 more)

### Community 54 - "emit_usd.py"
Cohesion: 0.36
Nodes (9): box_mesh(), convex_hull_of_verts(), git_head(), load_stl_verts_faces(), main(), mesh_prim(), sha256_file(), Path (+1 more)

### Community 55 - "d0_clock.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), run_dt(), run_paths(), sha256_file(), D0 clock + 2.4 s horizon diagnostic (Goal R0 section 4, D0). Minimal scene:…, Child body: runs under the Isaac venv python; one dt only.

### Community 56 - "d3_bond.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), run_one(), run_paths(), sha256_file(), D3 two-body coupling causality diagnostic (Goal R0 section 4, D3). CONSTRAINT…, Diagnostic Summary

### Community 58 - "build_system_bom.py"
Cohesion: 0.18
Nodes (10): column_name(), main(), rows(), write_xlsx(), Build the active C2.1 system BOM without mutating the historical C1 BOM., Verify the C2.1 P0-P6 digital package without granting hardware approval., collections, xml_etree_elementtree (+2 more)

### Community 61 - "power_sim.py"
Cohesion: 0.38
Nodes (6): admitted_load(), demand_at(), main(), VP1 Stage 4: virtual duty-cycle power simulation over the nameplate table.…, (demands, stage) at time t_s. loads = {key: W}., Apply the controller allocator policy at 1 s resolution.

### Community 65 - "c2/src/build_cad.py"
Cohesion: 0.26
Nodes (13): box(), cylinder(), from_c1(), main(), primitive(), sector(), wire(), xz() (+5 more)

### Community 68 - "run_r3.py"
Cohesion: 0.33
Nodes (6): _isaac_child(), main(), run_paths(), run_stage_dt(), sha256_file(), R3 runner: staged sustained-contact diagnostics T1/T2/T3. Reviewer-approved…

### Community 7 - "analyze.py"
Cohesion: 0.18
Nodes (13): allocate(), clearance_metric(), cooling(), main(), shaft_beam(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is…, Euler-Bernoulli beam with free rotation/simple-support translations; SI… (+5 more)

### Community 70 - "json"
Cohesion: 0.17
Nodes (11): deck(), main(), reaction_force(), Path, Host-build the portable controller core; no target flash or energization., Gate E: 3-level dt sweep on one W1 + one W4 case (thin driver over s1_physx).…, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., C1 compatibility gate for the existing repository pre-push hook. (+3 more)

### Community 71 - "build_release_manifest.py"
Cohesion: 0.60
Nodes (4): load(), main(), sha256(), Build deterministic P0-P6 + VP1 digital status and artifact manifests.

### Community 76 - "build_machine_wiring.py"
Cohesion: 0.36
Nodes (6): connector_symbol(), main(), uid(), write_schematic(), Generate the review-only KiCad machine wiring schematic and pin/net ledger., uuid

### Community 78 - "test_dynamics.py"
Cohesion: 0.29
Nodes (11): _load(), test_dt_sweep_complete(), test_gap_screen_sweep_complete(), test_s1_runs_real_physics(), test_screen_proxy_free(), test_surrogate_refit_additive(), test_transfer_derived_only(), test_usd_load_pass() (+3 more)

### Community 8 - "drive_teeth.py"
Cohesion: 0.16
Nodes (17): _gear_flank_pts(), _gear_local_solid(), _gear_profile_xy(), _inv(), _mesh_check(), replacement_local_solid(), _sprocket_local_solid(), _sprocket_profile_xz() (+9 more)

### Community 9 - "design.py"
Cohesion: 0.18
Nodes (9): box(), cyl(), part(), plate(), ring(), write_all(), add(), PPR C1 dimensional master. Generates a backend-neutral constructive-solid model. (+1 more)

### Community 166 - "C2.2 — VP1 전체 기계 Isaac Sim 검증"
Cohesion: 0.50
Nodes (3): C2.2 — VP1 전체 기계 Isaac Sim 검증, 검증 경계, 주요 경로

### Community 46 - "PPR_C2_1_machine_wiring_erc.json"
Cohesion: 0.25
Nodes (7): coordinate_units, date, included_severities, kicad_version, $schema, sheets, source

### Community 63 - "ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)"
Cohesion: 0.15
Nodes (12): ADDENDUM (2026-09-22, VP1 Stage 4, rev B — SUPERSEDES the rev A decision), ADDENDUM 3 (2026-09-23, VP1 Stage 5 활성 오거 — 연결 이송 HOLD), ADDENDUM 4 (2026-09-23, VP1 횡방향 이송과 S2 출력 지지판), ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs), REV B 부록 2 (2026-09-22, Isaac 통합 피드백 2건), 검증 경계와 HOLD, 결정 (rev B), 결정 (부품별) (+4 more)

### Community 66 - "C2.3-A-R3 리뷰 핸드오프 (판정 요청)"
Cohesion: 0.20
Nodes (9): 1. R3 결과 요약, 2. T1 상세 (5% GATE_MET), 3. T2 BLOCKED 상세 (픽스처 반복 이력), 4. 리뷰어 지시 반영 상태, 5. 미해결 (리뷰어 승인 필요), 6. 실행자 결론 불가, 7. CI 상태 (정확 커밋 a431df75), 8. R4-T2b 추가 반복 (리뷰어 승인 fixture 변경 실행 결과) (+1 more)

### Community 69 - "C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)"
Cohesion: 0.22
Nodes (8): 1. 구현, 2. 실행, 3. 수렴 (주 쌍 0.0025 vs 0.00125), 4. 수렴하지 않은 항목 (정직 기록), 5. overall_numerically_converged = True의 의미, 6. 미해결 (리뷰어 승인 필요), 7. 실행자 결론 불가, C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)

### Community 77 - "REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)"
Cohesion: 0.25
Nodes (7): 1. 구현 (작성 파일 — 커밋 없음), 2. 실행 (진단별 결과 — 수치), 3. 수렴 (해당 없음 — R0는 진단, 수렴 판정 아님), 4. 미수렴 (해당 없음), 5. 미해결 (리뷰어 승인 필요 — 실행자가 해소 불가), 6. 실행자 결론 불가 항목, REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)

### Community 79 - "C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F"
Cohesion: 0.29
Nodes (6): (a) I0–I6 numpy 프록시층 (유지, UNCALIBRATED ordering smoke), (b) C2.2b 실제 headless PhysX 동역학 Gates A–F (Isaac 6.1.0.0, `c2.2/results/dyn_*`), C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F, HOLD / 미해결 (승인 없이 진행 금지), 게이트 테이블, 리비전

### Community 85 - "PPR-KODEX (영구 규칙 · 목표)"
Cohesion: 0.29
Nodes (6): 1. VP1 경성 목표 (Hard Goal), 2. 고정 조건 (변경 금지, 합의 필요 시에만 사용자 승인으로 변경), 3. 방법론, 4. 검증 경계, 5. Git 경계, PPR-KODEX (영구 규칙 · 목표)

### Community 87 - "PPR VP1 현재 상태 (2026-09-23)"
Cohesion: 0.33
Nodes (5): PPR VP1 현재 상태 (2026-09-23), 미완료 기능과 물리 HOLD, 수정된 구조와 디지털 증거, 재현 순서, 통합 제품

### Community 88 - "C2.2 VP1 실행 씬 출처와 증거 경계"
Cohesion: 0.40
Nodes (4): C2.2 VP1 실행 씬 출처와 증거 경계, 디지털 검증과 물리 검증의 구분, 정책, 활성 원본

### Community 184 - "REFERENCE/UNRATED worm, wheel, shafts, bearings and motor"
Cohesion: 0.67
Nodes (3): REFERENCE/UNRATED worm, wheel, shafts, bearings and motor, Keyed PDL, auger, S2 and jackshaft torque paths, Single 15T/40T helical mesh

### Community 25 - "C2 Engineering Contracts"
Cohesion: 0.11
Nodes (18): C2 Engineering Contracts, Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, Run C2 Numerical Study, Run C2 Unit Tests, Run Gaussian Process Performance Training (+10 more)

### Community 29 - "PPR C1 Dimensioned Engineering Review Package"
Cohesion: 0.12
Nodes (17): C1-SEED Comparison Point, Coupled Kinematic Work Model, Eccentric Sleeve Wall Constraint, Geometry and Assembly Screen, PLA PET and TPU Calibration Plan, 144-Job Performance Manifest, Qualified GP and MLP Performance Learning Pipeline, S2 Latin-Hypercube Parameter Search (+9 more)

### Community 35 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Output Pins and Rollers, Output Shaft −ω/q, Rear Output Support (+7 more)

### Community 40 - "Material-flow HOLD despite localized S2 cap-bore transfer"
Cohesion: 0.14
Nodes (15): Four-turn auger and transverse screw active chute, Release manifest after generated evidence, S2 single-input reference kinematics, Shared M1 one-degree-of-freedom S1/S2 drive, VP1 integrated product hard goal, VP1 fixed electrical, envelope, budget and material constraints, VP1 integrated CAD, Isaac and BOM package, Current STEP, FreeCAD, USD and system BOM assembly (+7 more)

### Community 41 - "Open Physical Actions Register"
Cohesion: 0.17
Nodes (12): DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD, P6 Full Machine Digital Integration, C2.1 Digital Assembly Service and Test Package, Open Physical Actions Register, C2.1 P0-P6 Integration Plan, P6 Nominal Plate RFQ Review Package, Independent Machine Safety Architecture, Lockout and Staged Physical Test (+4 more)

### Community 48 - "VP1 whole-machine Isaac Sim validation"
Cohesion: 0.14
Nodes (14): Connected particulate transport HOLD, Rear output plate feed-mount clearance, S2 negative-direction geometry sweep, Stage-wise material flow localization, Dependent S1/S2/auger/puller/winder motion, Purchase, fabrication, energization and main-merge HOLD, Five-node material, cutter, wall, motor and gearbox thermal model, VP1 STEP/USD and result provenance (+6 more)

### Community 51 - "Fail-Closed Thermal and Jam Control Reference"
Cohesion: 0.25
Nodes (11): CAD-Derived Heat-Capacity Lower Bounds, Clean Filter, Clogged Filter, and Fan-Failure Sensitivity, Fail-Closed Thermal and Jam Control Reference, Five-Node Chamber and Drivetrain Thermal Circuit, Fixed-Shear Sensor Path, 500 W Power Allocation Screen, S2 Thermal Development CAD Module, Thermal Sensitivity Scenarios (+3 more)

### Community 59 - "PPR C1 CAD Inspection Image"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, PPR C1, Structural Frame, PPR C1 CAD Inspection Image, Hopper and Lid Hidden for Visibility

### Community 64 - "Single-Input Reverse-Output S2 Drivetrain"
Cohesion: 0.33
Nodes (6): Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative, Torque and Reaction Path, Fixed-Ring Cycloid Selection Rationale, Unverified Rating and Fabrication Limits

### Community 73 - "Fixed C2 System Constraints"
Cohesion: 0.40
Nodes (5): Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope, PPR C2 Engineering Baseline, 136-Row Cost Review Ledger

### Community 74 - "Active C2 Baseline"
Cohesion: 0.50
Nodes (4): Active C2 Baseline, Fixed System Constraints, Evidence and Safety Boundaries, Safety-Preserving Cost Reduction Order

### Community 84 - "Base Runtime and CAD Dependencies"
Cohesion: 0.67
Nodes (3): Base Runtime and CAD Dependencies, MLP Dependency Layer, C2.1 Active Digital Iteration

## Knowledge Gaps
- **221 isolated node(s):** `aux_demand_W`, `band_rotation_ms`, `buffer_full`, `estop_closed`, `fan_required` (+216 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 733 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **97 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `S2` connect `S2` to `c2.1/src/build_cad.py`, `c2/src/build_cad.py`, `math`, `run_full`, `run_study.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `aux_demand_W`, `band_rotation_ms`, `buffer_full` to the rest of the system?**
  _221 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `c2.1/src/build_cad.py` be split into smaller, more focused modules?**
  _Cohesion score 0.057703081232493 - nodes in this community are weakly interconnected._
- **Should `test_telemetry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09309309309309309 - nodes in this community are weakly interconnected._
- **Should `test_contract.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09462365591397849 - nodes in this community are weakly interconnected._
- **Should `i6_surrogate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `s1_event` be split into smaller, more focused modules?**
  _Cohesion score 0.10317460317460317 - nodes in this community are weakly interconnected._