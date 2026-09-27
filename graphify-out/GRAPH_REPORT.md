# Graph Report - PPR-c2.1-codex-20260921  (2026-09-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1995 nodes · 3675 edges · 189 communities (95 shown, 94 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 295 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f958f28f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- architectures.py
- process_model.py
- json
- verify_contract.py
- relocated_gravity.py
- performance.py
- drive_teeth.py
- winder.py
- Transmission
- test_telemetry.py
- engineering.py
- i6_surrogate.py
- downstream.py
- run_one_phase
- os
- c2.1/src/build_cad.py
- convert.py
- test_contract.py
- filament-quality-route.md
- s1_event
- generate
- Inputs
- electrical_bay.py
- components
- main
- run_study.py
- c2/src/build_cad.py
- bond_manager.py
- d3_bond.py
- d4_accounting.py
- run_case.py
- numpy
- render_reviewer_scenes.py
- approx
- design.py
- C2 Engineering Contracts
- Controller
- hashlib
- ControllerTests
- i3_coupon.py
- PPR C1 Dimensioned Engineering Review Package
- make_drawings.py
- DesignContracts
- controller_core.cpp
- structural_screen.py
- Outputs
- build_machine_integration.py
- chute.py
- d2_torque.py
- Thermal
- C2.1 S2 Transmission Schematic
- build_system_bom.py
- BondManager
- VP1 whole-machine Isaac Sim validation
- ChuteGeometry
- bonds.py
- ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)
- build_freecad.py
- run_r1.py
- TestVerifier
- Open Physical Actions Register
- _box
- ProcessModelPhysicsTests
- run_r4_t2b.py
- build_p6_drawings.py
- auger_shaft
- _prism_xz
- pull_cool_mount
- strengths_for_class
- run_r2.py
- Fail-Closed Thermal and Jam Control Reference
- DownstreamGeometryTests
- emit_usd.py
- C2.3-A-R3 리뷰 핸드오프 (판정 요청)
- d0_clock.py
- PPR-KODEX (영구 규칙 · 목표)
- C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)
- d1_contact.py
- PPR_C2_1_machine_wiring_erc.json
- build_machine_wiring.py
- pan_floor
- _feed_gear
- REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)
- PPR C1 CAD Inspection Image
- src/build_cad.py
- Limits
- bypass_channel_floor
- MaterialPathApertures
- C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F
- MissingEvidenceError
- Single-Input Reverse-Output S2 Drivetrain
- worm_sleeve
- TestD4Ledger
- TestNullStatus
- admitted_load
- write_json
- GearRatioKinematics
- C2.2 VP1 실행 씬 출처와 증거 경계
- Fixed C2 System Constraints
- ES-16 groove and washer stop spool escape, with axial float
- Active C2 Baseline
- FeedbackTests
- C2.2 — VP1 전체 기계 Isaac Sim 검증
- TestSchema
- TestD3Distinguishability
- TestD4Faults
- REFERENCE/UNRATED worm, wheel, shafts, bearings and motor
- Shared M1 one-degree-of-freedom S1/S2 drive
- TestSchema
- convergence/manifest.json
- r2/manifest.json
- r3/manifest.json
- TestDiagConstants
- C1 Digital Contracts
- Stage 5 active chute auger
- Function-preserving integration reliefs
- Four-turn auger and transverse screw active chute
- nip_opening_mm
- nip_range_mm
- retention_fit_screen
- 24V 33A PSU, 500W soft target and 792W current ceiling
- Digital verification is not physical approval
- VP1 integrated product hard goal
- Clause A1 (Steps-per-run)
- Clause A2 (Metrics calculation)
- Clause A3 (Mass conservation)
- Clause A4 (Missing-event handling)
- Clause A5 (Scene provenance)
- Clause A6 (Break/fragment accounting)
- Clause A7 (Threshold applicability)
- Host-tested firmware power allocation
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
- Conservative cycloidal pin-ring screen
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
- Goal R0 §2 (Numerical reliability closure)
- Hopper Interior Geometry
- ISAAC_PHYSX backend
- Kinematic Frame F0 Definition
- C2.3 tribometer, crown and joint expansion stopped
- Real-geometry candidate validation method
- Machine Body Dimensions
- Mass conservation threshold
- Motion Law Equations
- Nominal Motion Parameters
- Revision R1
- BLOCKED_PERFORMANCE_DATA
- Required artifacts list
- Residence time threshold
- S1 Cutter Parameters
- S2 Local Frame Definition
- Shaft work threshold

## God Nodes (most connected - your core abstractions)
1. `components()` - 41 edges
2. `S2` - 32 edges
3. `Inputs` - 31 edges
4. `Transmission` - 30 edges
5. `BondManager` - 26 edges
6. `_box()` - 26 edges
7. `s1_event()` - 22 edges
8. `generate()` - 22 edges
9. `_cyl()` - 22 edges
10. `components()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Small Pin-Ring Feasibility Screen` --semantically_similar_to--> `S2 Cycloidal Guide, Sleeve, and Pin Rings`  [INFERRED] [semantically similar]
  c2/docs/C2_ENGINEERING_NOTES.md → drawings/PPR_C1_dimensioned_review.pdf
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `WIND_MOUNT bearing and motor frame load path` --references--> `winder_mount()`  [EXTRACTED]
  STATUS.md → c2.1/src/winder.py
- `Evidence and Safety Boundaries` --semantically_similar_to--> `Safety-Preserving Cost Reduction Order`  [INFERRED] [semantically similar]
  AGENTS.md → c2/docs/CALIBRATION_AND_RFQ.md
- `Open Physical Actions Register` --semantically_similar_to--> `Nominal Drawing Fabrication Hold`  [INFERRED] [semantically similar]
  c2.1/docs/OPEN_ACTIONS_KO.md → c2.1/drawings/PPR_C2_1_P6_nominal_plate_review.pdf

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

## Communities (189 total, 94 thin omitted)

### Community 0 - "architectures.py"
Cohesion: 0.06
Nodes (44): lhs(), main(), ndarray, ValueError, I4 cheap geometric/kinematic screening (Isaac-independent, numpy LHS). Samples…, sample_candidates(), screen_candidate(), ScreenInputError (+36 more)

### Community 1 - "process_model.py"
Cohesion: 0.06
Nodes (53): build_library(), library_for_source(), main(), Build the same C++ PI kernel used by the host controller self-test., Avoid stale shared code in process-model calculations., _add(), chute_checks(), _dist_to_s2() (+45 more)

### Community 2 - "json"
Cohesion: 0.07
Nodes (36): VP1 Stage 4: virtual duty-cycle power simulation over the nameplate table.…, VP1 Stage 4 rev 2: S2 negative-rotation direction audit (Isaac evidence). The…, PowerGateTests, Behavioral regressions for reference-feed extrusion and gauge geometry., VP1 Stage 1: real drivetrain geometry + S1->S2 chute tests. CAD-dependent tests…, VP1 material choices and bounded mass properties for STEP-derived solids. These…, I5 low-resolution end-to-end S1->S2 benchmark (Isaac-independent, numpy).…, FIX A: material-flow localization for the integrated PPR VP1 machine. The last… (+28 more)

### Community 3 - "verify_contract.py"
Cohesion: 0.06
Nodes (45): Gate F follow-on: refit surrogate anchors on REAL dynamics data (additive).…, _load(), Gate A-F dynamics contract tests (no SimulationApp: manifest/schema only)., A reused STL path erased the south S1 tread in the executable scene., test_dt_sweep_complete(), test_full_machine_compound_solids_have_distinct_contact_meshes(), test_gap_screen_sweep_complete(), test_s1_runs_real_physics() (+37 more)

### Community 4 - "relocated_gravity.py"
Cohesion: 0.08
Nodes (39): at_box(), gravity_parts(), loft_section(), main(), nominal_mass(), other_parts(), pairs(), Independent, non-release relocated S2 gravity-handoff alternative. Runs against… (+31 more)

### Community 5 - "performance.py"
Cohesion: 0.09
Nodes (21): candidate_hashes(), canonical_sha256(), evidence_inventory(), EvidenceError, main(), nondominated(), ndarray, Path (+13 more)

### Community 6 - "drive_teeth.py"
Cohesion: 0.09
Nodes (39): chain_length_mm(), gear_center_distance(), gear_pitch_radius(), ratio_chain(), Pure kinematics/math for the VP1 common drive — NO cadquery dependency. Split…, Transverse pitch radius of a helical gear (normal module mn)., External tangent construction in XZ. Returns the two touch-point 4-tuples, the…, Kinematic chain from the VP1 Stage 4 layout (teeth counts only). M1 -> DRV-… (+31 more)

### Community 7 - "winder.py"
Cohesion: 0.11
Nodes (39): _box(), components(), _cyl(), _flange(), pull_frame(), pull_motor_ref(), pull_nip_stop(), pull_roller_adj() (+31 more)

### Community 8 - "Transmission"
Cohesion: 0.12
Nodes (24): main(), cad_positive_y_rotation_xz(), coupling(), external_mesh_sign(), ideal_virtual_work(), loaded_contact_sweep(), loaded_contact_takeup(), residual() (+16 more)

### Community 9 - "test_telemetry.py"
Cohesion: 0.09
Nodes (15): aggregate(), load_run(), A2 aggregate: telemetry.jsonl + events.jsonl -> derived quantities. Mass:…, reject_proxy(), ledger(), load_run(), A2 partial mechanical energy ledger (NEVER claims closure). residual = W_in -…, A2 telemetry/analysis tests (>=10): integrals, mass, ledger, convergence, proxy… (+7 more)

### Community 10 - "engineering.py"
Cohesion: 0.12
Nodes (17): design_set(), diverse_selection(), equivalent_motor_load(), generalized_torque(), hook_polygon(), kinematics(), main(), point_jacobian() (+9 more)

### Community 11 - "i6_surrogate.py"
Cohesion: 0.10
Nodes (27): main(), Gate F: real gap x screen sweep on survivors (thin driver). S1 gap sweep: shaft…, run(), bo_search(), build_pareto(), dominates(), evaluate_on_rows(), features() (+19 more)

### Community 12 - "downstream.py"
Cohesion: 0.11
Nodes (30): _bounds(), _box(), build_result(), components(), cool_duct(), cool_fan_3_ref(), _cyl(), gauge_contact_a() (+22 more)

### Community 13 - "run_one_phase"
Cohesion: 0.07
Nodes (23): buffer_throat_contains(), gravity_mouth_contains(), gravity_receiver_contains(), hole_transition(), main(), Path, Return (candidate, completed_hole) for one descending physics step. The…, Sphere envelope inside the actual octagonal Ø13 lower clear throat. (+15 more)

### Community 14 - "os"
Cohesion: 0.08
Nodes (19): argparse, Gate A loader: open c2.2/sim/assets/usd/machine.usda headless, report stage…, fail(), main(), I0 SimulationApp smoke: headless stage + one rigid cube, 60 physics steps. Gate…, # NOTE: close() os._exit()s via fast shutdown on success, so the JSON, Gate E: 3-level dt sweep on one W1 + one W4 case (thin driver over s1_physx).…, Gate B: PhysX S1 twin-shaft (S1-A) + waste fragment clusters + breaking bonds.… (+11 more)

### Community 15 - "c2.1/src/build_cad.py"
Cohesion: 0.16
Nodes (30): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+22 more)

### Community 16 - "convert.py"
Cohesion: 0.11
Nodes (24): _bbox(), candidate_manifest(), _candidate_mass_properties(), _candidate_parts(), git_head(), _lod_of(), main(), Path (+16 more)

### Community 17 - "test_contract.py"
Cohesion: 0.09
Nodes (13): check_executor_label(), _forbidden_labels(), A1 contract tests (stdlib unittest, goal section 22). Banned terminal labels…, Accept only the Isaac Sim / PhysX backend descriptor., Proxy records (analytic diagnostic only) are inadmissible., reject_proxy(), rel_change(), rel_mass_error() (+5 more)

### Community 18 - "filament-quality-route.md"
Cohesion: 0.09
Nodes (29): Three-fan cooling thermal sensitivity and geometric apertures, Seller-price sensor candidates and unquoted total landed cost, 269 mm formation-to-gauge feedback dead time, NVIDIA EULA refusal prevents new Isaac native contact-flow test, 500 W operating cap leaves 76 W before unselected auxiliary motors, Two-axis uncalibrated gauge and missing-readout reject gate, Single-pass feedback A, optional reheating B, same-hardware fixed C comparison, 1. 사용자 결정과 작업 상태 (+21 more)

### Community 19 - "s1_event"
Cohesion: 0.11
Nodes (19): BenchmarkError, _equiv_dims(), _load_dir_for_arch(), main(), RuntimeError, Run S1 fracture event; return dataset record + fragment list. threshold_scale…, Feed IDENTICAL saved S1 fragments through S2 arch screen model. eff_scale…, P0/P1 may not enter S2 fracture (wrap study S1-only). (+11 more)

### Community 20 - "generate"
Cohesion: 0.10
Nodes (17): build_bond_list(), cell_lattice(), main(), Recover lattice (nx,ny,nz,dx,dy,dz) by regenerating the specimen., Rebuild 6-neighbourhood lattice bonds matching bonds.lattice_graph., check_admissible(), generate(), main() (+9 more)

### Community 21 - "Inputs"
Cohesion: 0.07
Nodes (27): Inputs, aux_demand_W, band_rotation_ms, buffer_full, estop_closed, fan_required, fan_tach_ok, gauge_major_mm (+19 more)

### Community 22 - "electrical_bay.py"
Cohesion: 0.15
Nodes (24): _box(), components(), contactor(), current_limiter(), din_rail(), driver(), driver_1(), driver_2() (+16 more)

### Community 23 - "components"
Cohesion: 0.12
Nodes (24): auger_bearings(), belt_bearings(), belt_chain(), belt_drum(), belt_follower_sprocket(), components(), cross_feed_bearings(), cross_feed_shell() (+16 more)

### Community 24 - "main"
Cohesion: 0.12
Nodes (20): main(), mesh_volume(), Path, FIX B(1): convex-hull fidelity audit for the integrated machine. For every…, Signed volume of a closed triangle mesh via the divergence theorem (mm^3). CAD-…, Sample a centre and 16 rim rays of each Ø3 screen exit in mesh XY., screen_vertical_mesh_paths(), sha256_file() (+12 more)

### Community 25 - "run_study.py"
Cohesion: 0.13
Nodes (16): allocate_power(), Fail-closed control reference. NOT deployable motor/heater firmware., Reference admission only; PSU 792 W rating does not raise this budget., evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., Lower-bound heat capacities from generated C2 metal volumes, not measured…, thermal_capacities_from_cad() (+8 more)

### Community 26 - "c2/src/build_cad.py"
Cohesion: 0.18
Nodes (18): Any, box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector() (+10 more)

### Community 27 - "bond_manager.py"
Cohesion: 0.14
Nodes (14): _components(), find(), union(), FractureInputError, FractureResult, Fragment, NonphysicalError, RuntimeError (+6 more)

### Community 28 - "d3_bond.py"
Cohesion: 0.12
Nodes (11): _isaac_child(), main(), D3 two-body coupling causality diagnostic (Goal R0 section 4, D3). CONSTRAINT…, run_one(), run_paths(), sha256_file(), R0.3 causality/accounting unit tests (system python3, isaac-free). >= 10 tests:…, TestAtomicVsComponent (+3 more)

### Community 29 - "d4_accounting.py"
Cohesion: 0.16
Nodes (19): compare_metrics(), _isaac_child(), jam_status(), main(), make_buckets(), ordered_sum(), passage_status(), D4 observability / accounting / negative tests (Goal R0 section 4, D4). Isaac… (+11 more)

### Community 30 - "run_case.py"
Cohesion: 0.15
Nodes (19): build_run_config(), dt_label(), dt_source_mapping(), finalize(), _import_s1(), main(), prepare(), A2 single-case Isaac headless runner (ONE frozen case + ONE ladder dt). REUSE… (+11 more)

### Community 31 - "numpy"
Cohesion: 0.16
Nodes (16): numpy, scipy_linalg, scipy_optimize, allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is… (+8 more)

### Community 32 - "render_reviewer_scenes.py"
Cohesion: 0.18
Nodes (17): isaac_capture(), look_at_matrix(), main(), probe_positions(), Path, Reviewer scenes for the PPR VP1 full machine (c2.2 acceptance item 2). Renders…, Use only a connected probe run for this exact STEP and USD., RTX attempt with a disk heartbeat. Kit quirk on this host: exceptions raised… (+9 more)

### Community 33 - "approx"
Cohesion: 0.16
Nodes (5): approx(), TestBoundaryWork, TestD0SubstepMapping, TestD1UnitRule, TestShaftTorque

### Community 34 - "design.py"
Cohesion: 0.13
Nodes (12): copy, box(), cyl(), part(), plate(), PPR C1 dimensional master. Generates a backend-neutral constructive-solid model., ring(), write_all() (+4 more)

### Community 35 - "C2 Engineering Contracts"
Cohesion: 0.11
Nodes (18): Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, C2 Engineering Contracts, Run C2 Numerical Study, Run C2 Unit Tests, Actual Run Counts Must Equal Dynamic Evidence Inventory Counts (+10 more)

### Community 36 - "Controller"
Cohesion: 0.12
Nodes (18): Controller, BAND_ROTATION_PERIOD_MS, command_, gauge_gate_, gauge_seen_, integral_, latched_, limits_ (+10 more)

### Community 37 - "hashlib"
Cohesion: 0.16
Nodes (14): Host-build the portable controller core; no target flash or energization., load(), main(), Build deterministic P0-P6 + VP1 digital status and artifact manifests., sha256(), deck(), main(), Path (+6 more)

### Community 39 - "i3_coupon.py"
Cohesion: 0.18
Nodes (13): check_ordering(), load_dir_for(), main(), OrderingError, RuntimeError, I3 single-event fracture smoke benchmark (Isaac-independent, numpy-only). 12…, Fixed-lattice probe: identical geometry+seed, class strengths vary. Elementwise…, P0/P1 strand bundles carry no fracture claim (wrap risk only). (+5 more)

### Community 40 - "PPR C1 Dimensioned Engineering Review Package"
Cohesion: 0.12
Nodes (17): BLOCKED_PERFORMANCE_DATA, C1-SEED Comparison Point, Coupled Kinematic Work Model, Eccentric Sleeve Wall Constraint, Geometry and Assembly Screen, PLA PET and TPU Calibration Plan, 144-Job Performance Manifest, Qualified GP and MLP Performance Learning Pipeline (+9 more)

### Community 41 - "make_drawings.py"
Cohesion: 0.21
Nodes (16): ezdxf, reportlab_lib_pagesizes, reportlab_pdfbase, reportlab_pdfbase_ttfonts, reportlab_pdfgen, shapely_ops, dim(), drawshape() (+8 more)

### Community 43 - "controller_core.cpp"
Cohesion: 0.16
Nodes (15): algorithm, array, band_count(), diameter_pi_step(), main(), PowerDevice, name, W (+7 more)

### Community 44 - "structural_screen.py"
Cohesion: 0.19
Nodes (14): ast, bending_point(), case(), flange_thickness(), literal_dict_assignment(), margin(), Bounded, non-qualifying structural and thermal screen for VP1 hardware. Run:…, Read dimension constants without importing CadQuery or regenerating CAD. (+6 more)

### Community 45 - "Outputs"
Cohesion: 0.14
Nodes (14): Outputs, admitted_W, aux_enable, fans_enable, gauge_in_tolerance, h100_enable, h60_enable, m1_enable (+6 more)

### Community 46 - "build_machine_integration.py"
Cohesion: 0.21
Nodes (14): bbox_overlap(), c21_parts(), collision_audit(), extent(), legacy_parts(), main(), normalize_step_timestamp(), Build and verify the C2.1 S2 subassembly inside the complete C1 machine. C1 is… (+6 more)

### Community 47 - "chute.py"
Cohesion: 0.14
Nodes (14): cutter_sweep_solids(), _guide(), _prism_xy(), VP1 Stage 1: real transfer chute from the S1 discharge opening to the C2.1 S2…, Conservative S1 cutter sweep envelopes for clearance checks., Historical ratchet rib retained for inspection, not installed., No stationary ribs in the screw pickup or flight zone., Historical pan-only ribs, superseded by the active transfer design. (+6 more)

### Community 48 - "d2_torque.py"
Cohesion: 0.21
Nodes (14): boundary_work(), _cross(), _dot(), _isaac_child(), on_post(), main(), D2 torque/work semantics diagnostic (Goal R0 section 4, D2). Definitions…, Axial contact torque on ONE shaft. contacts: iterable of (position_p,… (+6 more)

### Community 49 - "Thermal"
Cohesion: 0.29
Nodes (5): Carry thermal state through batch/fan-fault segments; still uncalibrated., Thermal, thermal_duty_run(), thermal_run(), ThermalTests

### Community 50 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 51 - "build_system_bom.py"
Cohesion: 0.17
Nodes (11): column_name(), main(), Build the active C2.1 system BOM without mutating the historical C1 BOM., rows(), write_xlsx(), Verify the C2.1 P0-P6 digital package without granting hardware approval., collections, csv (+3 more)

### Community 52 - "BondManager"
Cohesion: 0.26
Nodes (8): BondManager, Deterministic fallback fracture over a BondGraph., fixed_lattice(), TestDeterminism, TestInvalidInput, TestOrientationDependence, TestW1ZFirst, TestW4Isotropy

### Community 53 - "VP1 whole-machine Isaac Sim validation"
Cohesion: 0.14
Nodes (14): Connected particulate transport HOLD, CROSS_FEED_SHAFT transverse screw, Rear output plate feed-mount clearance, S2 negative-direction geometry sweep, Historical proxy-result exclusion, Development PR versus physical-release policy, VP1 STEP/USD and result provenance, Stage-wise material flow localization (+6 more)

### Community 54 - "ChuteGeometry"
Cohesion: 0.14
Nodes (4): ChainGeometry, ChuteGeometry, GearGeometry, skipUnless

### Community 55 - "bonds.py"
Cohesion: 0.25
Nodes (8): Bond, BondGraph, Cell, lattice_graph(), I2 bond-graph: cells/chunks + directional bonds (nominal strengths only).…, 6-neighbourhood lattice; x->in_raster, y->cross_raster, z->inter_layer_z. Cell…, Return list of violations (empty == valid)., TestBondValidity

### Community 56 - "ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)"
Cohesion: 0.15
Nodes (12): ADDENDUM (2026-09-22, VP1 Stage 4, rev B — SUPERSEDES the rev A decision), ADDENDUM 3 (2026-09-23, VP1 Stage 5 활성 오거 — 연결 이송 HOLD), ADDENDUM 4 (2026-09-23, VP1 횡방향 이송과 S2 출력 지지판), ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs), REV B 부록 2 (2026-09-22, Isaac 통합 피드백 2건), 검증 경계와 HOLD, 결정 (rev B), 결정 (부품별) (+4 more)

### Community 57 - "build_freecad.py"
Cohesion: 0.23
Nodes (11): main(), Create the native FreeCAD C2.1 machine assembly from checked STEP parts., read_shape(), freecad, part, build(), face(), primitive() (+3 more)

### Community 58 - "run_r1.py"
Cohesion: 0.23
Nodes (10): build_case_geometry(), _isaac_child(), main(), R1 runner: one canonical case at ONE ladder dt, equal 2.4 s physics. Contract:…, # NOTE: Gf.Vector3f hard-crashes (SIGSEGV) in this Isaac build;, # NOTE: work integral requires tau_shaft from typed contacts;, Deterministic per-case fragment positions from waste_gen dims., run_case_dt() (+2 more)

### Community 60 - "Open Physical Actions Register"
Cohesion: 0.17
Nodes (12): C2.1 Digital Assembly Service and Test Package, Lockout and Staged Physical Test, DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD, P6 Full Machine Digital Integration, Remaining Rating and Performance Holds, Motor Floor Exceeds System Soft Budget, Open Physical Actions Register, C2.1 P0-P6 Integration Plan (+4 more)

### Community 61 - "_box"
Cohesion: 0.17
Nodes (12): _box(), bypass_wall_north_lower(), bypass_wall_south(), guide_left(), guide_right(), South containment, relieved only at the low-y spur-gear face., North containment ends before the orthogonal screw's west cheek., Central lane wall; transverse screw supplies lateral transport. (+4 more)

### Community 63 - "run_r4_t2b.py"
Cohesion: 0.17
Nodes (9): R4-T2b: chain suspended via end posts (FixedJoint), NO pin, gravity + preload…, isaacsim, isaacsim_core_experimental_objects, isaacsim_core_experimental_prims, isaacsim_core_experimental_utils_stage, isaacsim_core_simulation_manager, omni_physx, omni_timeline (+1 more)

### Community 64 - "build_p6_drawings.py"
Cohesion: 0.27
Nodes (10): dimension(), main(), Export the few C2.1 plate drawings needed for fabrication review. These are…, ring_page(), sha256(), support_page(), datetime, matplotlib_backends_backend_pdf (+2 more)

### Community 65 - "auger_shaft"
Cohesion: 0.25
Nodes (11): auger_shaft(), _cross_feed_flight(), cross_feed_shaft(), _helix_z(), _path_frame(), Split shaft with a swept, opposite-hand screw and keyed spur., Point and unit tangent at the initial vertex of a swept helix., Single right-hand helicoid with a 3 mm swept flight face. (+3 more)

### Community 66 - "_prism_xz"
Cohesion: 0.18
Nodes (11): belt_loop(), capsule(), intake_lip(), _prism_xz(), 45deg intake lip under the S1 -X side strip (the opening's west edge); all…, Two side loops leave a continuous, separately driven central lane., Level central lane on the common M1 drum, running beneath AUG., One small-module 12T spur keyed to the east drum or feeder axle. (+3 more)

### Community 67 - "pull_cool_mount"
Cohesion: 0.24
Nodes (11): pull_cool_mount(), Rear-profile rack carries the thin cooling tray and puller separately. Face…, Ø70×58 steel tube, 2 mm wall, with two 3 mm internal steel webs. The Ø17 web…, spool_drum(), Direct steel puller and cooling tray rack, 7. 같은 제품의 기준 원료 모델·제어·비용 비교 (VP1), Hollow steel winding drum mass and unrated mount, Physical operation procurement and test HOLD (+3 more)

### Community 68 - "strengths_for_class"
Cohesion: 0.20
Nodes (6): graph_from_meta(), Rebuild the exact I2 lattice from waste_gen metadata. Mirrors…, strengths_for_class(), TestMassConservation, TestAnisotropyOrdering, TestMassConservation

### Community 69 - "run_r2.py"
Cohesion: 0.29
Nodes (8): R2 Review Handoff Summary, build_case_geometry(), _isaac_child(), main(), R2 runner: per-physics-step contact stream + signed shaft load + boundary work…, run_case_dt(), run_paths(), sha256_file()

### Community 70 - "Fail-Closed Thermal and Jam Control Reference"
Cohesion: 0.25
Nodes (11): CAD-Derived Heat-Capacity Lower Bounds, Clean-Air Cooling Path, Clean Filter, Clogged Filter, and Fan-Failure Sensitivity, Fail-Closed Thermal and Jam Control Reference, Five-Node Chamber and Drivetrain Thermal Circuit, Fixed-Shear Sensor Path, Independent Hardware Safety Chain, P5 Digital Thermal and Control Boundary (+3 more)

### Community 72 - "emit_usd.py"
Cohesion: 0.36
Nodes (9): box_mesh(), convex_hull_of_verts(), git_head(), load_stl_verts_faces(), main(), mesh_prim(), Path, Gate A: machine USD emission from staged STL + parametric DERIVED transfer… (+1 more)

### Community 73 - "C2.3-A-R3 리뷰 핸드오프 (판정 요청)"
Cohesion: 0.20
Nodes (9): 1. R3 결과 요약, 2. T1 상세 (5% GATE_MET), 3. T2 BLOCKED 상세 (픽스처 반복 이력), 4. 리뷰어 지시 반영 상태, 5. 미해결 (리뷰어 승인 필요), 6. 실행자 결론 불가, 7. CI 상태 (정확 커밋 a431df75), 8. R4-T2b 추가 반복 (리뷰어 승인 fixture 변경 실행 결과) (+1 more)

### Community 74 - "d0_clock.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), D0 clock + 2.4 s horizon diagnostic (Goal R0 section 4, D0). Minimal scene:…, Child body: runs under the Isaac venv python; one dt only., run_dt(), run_paths(), sha256_file()

### Community 75 - "PPR-KODEX (영구 규칙 · 목표)"
Cohesion: 0.20
Nodes (9): 1. VP1 경성 목표 (Hard Goal), 2. 고정 조건 (변경 금지, 합의 필요 시에만 사용자 승인으로 변경), 3. 방법론, 4. 검증 경계, 5. Git 경계, PPR-KODEX (영구 규칙 · 목표), C2.1 Active Digital Iteration, Base Runtime and CAD Dependencies (+1 more)

### Community 76 - "C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)"
Cohesion: 0.22
Nodes (8): 1. 구현, 2. 실행, 3. 수렴 (주 쌍 0.0025 vs 0.00125), 4. 수렴하지 않은 항목 (정직 기록), 5. overall_numerically_converged = True의 의미, 6. 미해결 (리뷰어 승인 필요), 7. 실행자 결론 불가, C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)

### Community 77 - "d1_contact.py"
Cohesion: 0.36
Nodes (6): _isaac_child(), main(), D1 contact units + isolation diagnostic (Goal R0 section 4, D1). Exact…, run_one(), run_paths(), sha256_file()

### Community 78 - "PPR_C2_1_machine_wiring_erc.json"
Cohesion: 0.25
Nodes (7): coordinate_units, date, included_severities, kicad_version, $schema, sheets, source

### Community 79 - "build_machine_wiring.py"
Cohesion: 0.36
Nodes (6): connector_symbol(), main(), Generate the review-only KiCad machine wiring schematic and pin/net ledger., uid(), write_schematic(), uuid

### Community 80 - "pan_floor"
Cohesion: 0.25
Nodes (8): _c21_transform(), _obstruction_solid(), pan_floor(), Apply the frozen c2_subassembly_transform to a c2 local-frame part., Frozen S2 jacket solids that pierce the chute floor plane: the…, S1 discharge basin with a recessed, supported belt pocket., Landing ledge over the mouth (x 278.5..310, y 255..295); cut where the frozen…, trough_floor()

### Community 81 - "_feed_gear"
Cohesion: 0.25
Nodes (8): cross_feed_gear(), cross_feed_idler(), _feed_gear(), pdl_feed_gear(), Six-mm, 12T involute spur face, keyed on its +X bore flank., 12T keyed output gear sharing the existing PDL shaft., 12T integral intermediate wheel on its own two supported journals., Equal 12T keyed output wheel; two external meshes restore PDL sign.

### Community 82 - "REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)"
Cohesion: 0.25
Nodes (7): 1. 구현 (작성 파일 — 커밋 없음), 2. 실행 (진단별 결과 — 수치), 3. 수렴 (해당 없음 — R0는 진단, 수렴 판정 아님), 4. 미수렴 (해당 없음), 5. 미해결 (리뷰어 승인 필요 — 실행자가 해소 불가), 6. 실행자 결론 불가 항목, REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)

### Community 83 - "PPR C1 CAD Inspection Image"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 84 - "src/build_cad.py"
Cohesion: 0.39
Nodes (6): bbox(), build(), main(), primitive(), CadQuery/OCP verification backend for the shared constructive-solid master. The…, wire3()

### Community 85 - "Limits"
Cohesion: 0.29
Nodes (6): Limits, jam_current_A, jam_minimum_rpm, maximum_temperature_C, operational_cap_W, stale_feedback_ms

### Community 86 - "bypass_channel_floor"
Cohesion: 0.33
Nodes (6): assembly_geometry_checks(), imported(), bounds(), Verify that the exported STEP retains the active chute and auger. This is…, bypass_channel_floor(), Longitudinal U cradle, opened locally into the powered cross pickup. The old…

### Community 88 - "C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F"
Cohesion: 0.29
Nodes (6): (a) I0–I6 numpy 프록시층 (유지, UNCALIBRATED ordering smoke), (b) C2.2b 실제 headless PhysX 동역학 Gates A–F (Isaac 6.1.0.0, `c2.2/results/dyn_*`), C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F, HOLD / 미해결 (승인 없이 진행 금지), 게이트 테이블, 리비전

### Community 89 - "MissingEvidenceError"
Cohesion: 0.33
Nodes (6): MissingEvidenceError, RuntimeError, Raised when calibrated (measured) strength data is requested. No physical…, Calibrated fracture strength lookup — always fails loudly (no data)., require_calibrated_strength(), TestMissingEvidence

### Community 90 - "Single-Input Reverse-Output S2 Drivetrain"
Cohesion: 0.33
Nodes (6): Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative, Torque and Reaction Path, Unverified Rating and Fabrication Limits

### Community 91 - "worm_sleeve"
Cohesion: 0.33
Nodes (6): auger_wheel(), _helix_about_y(), Right-hand helix advancing along +Y with a specified bottom phase., PDL_WORM: right-hand two-start swept threads keyed to the shaft., Sector gear at the auger end, generated against the actual worm. The swept worm…, worm_sleeve()

### Community 94 - "admitted_load"
Cohesion: 0.40
Nodes (5): admitted_load(), demand_at(), main(), (demands, stage) at time t_s. loads = {key: W}., Mirror firmware admission; unknown/denied aux holds the entire line.

### Community 95 - "write_json"
Cohesion: 0.40
Nodes (4): _canon(), Path, write_json(), MotionArtifactTests

### Community 97 - "C2.2 VP1 실행 씬 출처와 증거 경계"
Cohesion: 0.40
Nodes (4): C2.2 VP1 실행 씬 출처와 증거 경계, 디지털 검증과 물리 검증의 구분, 정책, 활성 원본

### Community 98 - "Fixed C2 System Constraints"
Cohesion: 0.40
Nodes (5): PPR C2 Engineering Baseline, 136-Row Cost Review Ledger, Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope

### Community 99 - "ES-16 groove and washer stop spool escape, with axial float"
Cohesion: 0.40
Nodes (5): Smalley ES-16 dimensional candidate without project load rating, SSB-0087 published work height incompatible with present clutch seat, Thrust washer radial margin is conditional not a strength claim, SSB-0087 rated work height is not matched by 1 mm clutch seat, ES-16 groove and washer stop spool escape, with axial float

### Community 100 - "Active C2 Baseline"
Cohesion: 0.50
Nodes (4): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Safety-Preserving Cost Reduction Order

### Community 102 - "C2.2 — VP1 전체 기계 Isaac Sim 검증"
Cohesion: 0.50
Nodes (3): C2.2 — VP1 전체 기계 Isaac Sim 검증, 검증 경계, 주요 경로

### Community 106 - "REFERENCE/UNRATED worm, wheel, shafts, bearings and motor"
Cohesion: 0.67
Nodes (3): Keyed PDL, auger, S2 and jackshaft torque paths, REFERENCE/UNRATED worm, wheel, shafts, bearings and motor, Single 15T/40T helical mesh

### Community 107 - "Shared M1 one-degree-of-freedom S1/S2 drive"
Cohesion: 0.67
Nodes (3): S2 single-input reference kinematics, Shared M1 one-degree-of-freedom S1/S2 drive, VP1 fixed electrical, envelope, budget and material constraints

## Knowledge Gaps
- **235 isolated node(s):** `검증 경계`, `주요 경로`, `runs`, `schema`, `runs` (+230 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 831 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **94 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `S2` connect `engineering.py` to `convert.py`, `run_study.py`, `c2/src/build_cad.py`, `c2.1/src/build_cad.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `DesignContracts` connect `DesignContracts` to `json`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `pull_cool_mount()` connect `pull_cool_mount` to `winder.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `검증 경계`, `주요 경로`, `runs` to the rest of the system?**
  _235 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `architectures.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06041986687147977 - nodes in this community are weakly interconnected._
- **Should `process_model.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05683060109289618 - nodes in this community are weakly interconnected._
- **Should `json` be split into smaller, more focused modules?**
  _Cohesion score 0.06939890710382514 - nodes in this community are weakly interconnected._