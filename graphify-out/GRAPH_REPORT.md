# Graph Report - PPR-c2.1-codex-20260921  (2026-09-27)

## Corpus Check
- 1132 files · ~14,086,138 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1437 file(s) not represented in the graph (top: .stl 649, .step 243, .log 204)

## Summary
- 2000 nodes · 3691 edges · 183 communities (97 shown, 86 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cef73129`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- architectures.py
- process_model.py
- pull_cool_mount
- os
- guards.py
- hashlib
- drive_teeth.py
- winder.py
- c2.1/src/build_cad.py
- test_telemetry.py
- S2
- i6_surrogate.py
- downstream.py
- flow_localize.py
- traceback
- relocated_gravity.py
- full_machine.py
- test_contract.py
- filament-quality-route.md
- s1_event
- generate
- Inputs
- electrical_bay.py
- components
- Thermal
- run_study.py
- InvalidMechanism
- NonphysicalError
- test_r03_causality.py
- d4_accounting.py
- run_case.py
- analyze.py
- render_reviewer_scenes.py
- d2_torque.py
- design.py
- C2 Engineering Contracts
- Controller
- json
- ControllerTests
- run_combo
- PPR C1 Dimensioned Engineering Review Package
- make_drawings.py
- DesignContracts
- controller_core.cpp
- structural_screen.py
- Outputs
- build_machine_integration.py
- chute.py
- engineering.py
- s1_physx.py
- C2.1 S2 Transmission Schematic
- ChuteGeometry
- BondManager
- VP1 whole-machine Isaac Sim validation
- c2/src/build_cad.py
- bonds.py
- ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)
- d3_bond.py
- run_r1.py
- TestVerifier
- Open Physical Actions Register
- _box
- ProcessModelPhysicsTests
- run_r4_t2b.py
- PPR-KODEX (영구 규칙 · 목표)
- auger_shaft
- _prism_xz
- src/build_cad.py
- screen_open_area
- run_r2.py
- Fail-Closed Thermal and Jam Control Reference
- DownstreamGeometryTests
- emit_usd.py
- C2.3-A-R3 리뷰 핸드오프 (판정 요청)
- d0_clock.py
- strengths_for_class
- C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)
- d1_contact.py
- PPR_C2_1_machine_wiring_erc.json
- build_machine_wiring.py
- pan_floor
- _feed_gear
- REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)
- PPR C1 CAD Inspection Image
- subprocess
- Limits
- FeedbackTests
- TestSchema
- C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F
- MissingEvidenceError
- Single-Input Reverse-Output S2 Drivetrain
- worm_sleeve
- GearRatioKinematics
- ES-16 groove and washer stop spool escape, with axial float
- power_sim.py
- run_r3.py
- comparison_contract
- C2.2 VP1 실행 씬 출처와 증거 경계
- Fixed C2 System Constraints
- TestSchema
- Active C2 Baseline
- C2.2 — VP1 전체 기계 Isaac Sim 검증
- REFERENCE/UNRATED worm, wheel, shafts, bearings and motor
- Shared M1 one-degree-of-freedom S1/S2 drive
- convergence/manifest.json
- r2/manifest.json
- r3/manifest.json
- sample_candidates
- C1 Digital Contracts
- Stage 5 active chute auger
- Function-preserving integration reliefs
- Four-turn auger and transverse screw active chute
- argparse
- check_baseline_present
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
5. `_box()` - 26 edges
6. `BondManager` - 26 edges
7. `components()` - 23 edges
8. `_cyl()` - 22 edges
9. `s1_event()` - 22 edges
10. `generate()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Small Pin-Ring Feasibility Screen` --semantically_similar_to--> `S2 Cycloidal Guide, Sleeve, and Pin Rings`  [INFERRED] [semantically similar]
  c2/docs/C2_ENGINEERING_NOTES.md → drawings/PPR_C1_dimensioned_review.pdf
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `Evidence and Safety Boundaries` --semantically_similar_to--> `Safety-Preserving Cost Reduction Order`  [INFERRED] [semantically similar]
  AGENTS.md → c2/docs/CALIBRATION_AND_RFQ.md
- `Short clutch fault is not rescued by feedback` --semantically_similar_to--> `Isolated modeled winding-clutch fault`  [INFERRED] [semantically similar]
  STATUS.md → docs/decisions/filament-quality-route.md
- `Separate puller idler rotation and vertical compliance` --semantically_similar_to--> `Corrected vertical puller idler and motor clearance`  [INFERRED] [semantically similar]
  STATUS.md → docs/decisions/filament-quality-route.md

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

## Communities (183 total, 86 thin omitted)

### Community 0 - "architectures.py"
Cohesion: 0.20
Nodes (16): validate_mechanisms(), Architecture, check_clearance(), check_direction(), I4 mechanism architecture library (Isaac-independent, numpy-free). 7 variants:…, S2-A law: phi = -theta/q (reverse, sign -1)., _s1a(), _s1b() (+8 more)

### Community 1 - "process_model.py"
Cohesion: 0.05
Nodes (56): build_library(), library_for_source(), main(), Host-build the portable controller core; no target flash or energization., Build the same C++ PI kernel used by the host controller self-test., Avoid stale shared code in process-model calculations., _add(), chute_checks() (+48 more)

### Community 2 - "pull_cool_mount"
Cohesion: 0.13
Nodes (19): pull_cool_mount(), Rear-profile rack carries the thin cooling tray and puller separately. Face…, Steel bearing/motor load path to the front 20 mm Al upright. The flange sweeps…, Ø70×58 steel tube, 2 mm wall, with two 3 mm internal steel webs. The Ø17 web…, spool_drum(), winder_mount(), Isolated modeled winding-clutch fault, Corrected vertical puller idler and motor clearance (+11 more)

### Community 3 - "os"
Cohesion: 0.06
Nodes (47): Gate F follow-on: refit surrogate anchors on REAL dynamics data (additive).…, Gate C: DERIVED transfer assets (S1 discharge + chute + S2 entry/exit). C2.1…, _load(), Gate A-F dynamics contract tests (no SimulationApp: manifest/schema only)., A reused STL path erased the south S1 tread in the executable scene., test_dt_sweep_complete(), test_full_machine_compound_solids_have_distinct_contact_meshes(), test_gap_screen_sweep_complete() (+39 more)

### Community 4 - "guards.py"
Cohesion: 0.18
Nodes (16): _box(), components(), guard_chain_a(), guard_chain_b(), guard_lid_interlock_seat(), guard_s2_ring(), VP1 Stage 2: real containment guards, E-stop mounts and interlock seats.…, Named guard parts in absolute machine coordinates (group 'guard'). (+8 more)

### Community 5 - "hashlib"
Cohesion: 0.07
Nodes (27): column_name(), main(), Build the active C2.1 system BOM without mutating the historical C1 BOM., rows(), write_xlsx(), Verify the C2.1 P0-P6 digital package without granting hardware approval., candidate_hashes(), canonical_sha256() (+19 more)

### Community 6 - "drive_teeth.py"
Cohesion: 0.09
Nodes (40): legacy_parts(), chain_length_mm(), gear_center_distance(), gear_pitch_radius(), ratio_chain(), Pure kinematics/math for the VP1 common drive — NO cadquery dependency. Split…, Transverse pitch radius of a helical gear (normal module mn)., External tangent construction in XZ. Returns the two touch-point 4-tuples, the… (+32 more)

### Community 7 - "winder.py"
Cohesion: 0.09
Nodes (46): _box(), components(), _cyl(), _flange(), _idler_z(), nip_opening_mm(), nip_range_mm(), pull_frame() (+38 more)

### Community 8 - "c2.1/src/build_cad.py"
Cohesion: 0.05
Nodes (70): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+62 more)

### Community 9 - "test_telemetry.py"
Cohesion: 0.09
Nodes (15): aggregate(), load_run(), A2 aggregate: telemetry.jsonl + events.jsonl -> derived quantities. Mass:…, reject_proxy(), ledger(), load_run(), A2 partial mechanical energy ledger (NEVER claims closure). residual = W_in -…, A2 telemetry/analysis tests (>=10): integrals, mass, ledger, convergence, proxy… (+7 more)

### Community 10 - "S2"
Cohesion: 0.15
Nodes (13): Any, generalized_torque(), hook_polygon(), kinematics(), packaging(), point_jacobian(), polygon_area(), ndarray (+5 more)

### Community 11 - "i6_surrogate.py"
Cohesion: 0.12
Nodes (23): bo_search(), build_pareto(), dominates(), evaluate_on_rows(), features(), load_i5_rows(), main(), pareto_front() (+15 more)

### Community 12 - "downstream.py"
Cohesion: 0.11
Nodes (30): _bounds(), _box(), build_result(), components(), cool_duct(), cool_fan_3_ref(), _cyl(), gauge_contact_a() (+22 more)

### Community 13 - "flow_localize.py"
Cohesion: 0.05
Nodes (41): main(), Create the native FreeCAD C2.1 machine assembly from checked STEP parts., read_shape(), buffer_throat_contains(), gravity_mouth_contains(), gravity_receiver_contains(), hole_transition(), main() (+33 more)

### Community 14 - "traceback"
Cohesion: 0.25
Nodes (6): Gate A loader: open c2.2/sim/assets/usd/machine.usda headless, report stage…, fail(), main(), I0 SimulationApp smoke: headless stage + one rigid cube, 60 physics steps. Gate…, # NOTE: close() os._exit()s via fast shutdown on success, so the JSON, traceback

### Community 15 - "relocated_gravity.py"
Cohesion: 0.15
Nodes (23): at_box(), gravity_parts(), loft_section(), main(), nominal_mass(), other_parts(), pairs(), Independent, non-release relocated S2 gravity-handoff alternative. Runs against… (+15 more)

### Community 16 - "full_machine.py"
Cohesion: 0.06
Nodes (47): _bbox(), candidate_manifest(), _candidate_mass_properties(), _candidate_parts(), git_head(), _lod_of(), main(), Path (+39 more)

### Community 17 - "test_contract.py"
Cohesion: 0.09
Nodes (13): check_executor_label(), _forbidden_labels(), A1 contract tests (stdlib unittest, goal section 22). Banned terminal labels…, Accept only the Isaac Sim / PhysX backend descriptor., Proxy records (analytic diagnostic only) are inadmissible., reject_proxy(), rel_change(), rel_mass_error() (+5 more)

### Community 18 - "filament-quality-route.md"
Cohesion: 0.09
Nodes (28): Three-fan cooling thermal sensitivity and geometric apertures, Seller-price sensor candidates and unquoted total landed cost, 269 mm formation-to-gauge feedback dead time, NVIDIA EULA refusal prevents new Isaac native contact-flow test, 500 W operating cap leaves 76 W before unselected auxiliary motors, Two-axis uncalibrated gauge and missing-readout reject gate, Single-pass feedback A, optional reheating B, same-hardware fixed C comparison, 1. 사용자 결정과 작업 상태 (+20 more)

### Community 19 - "s1_event"
Cohesion: 0.11
Nodes (19): BenchmarkError, _equiv_dims(), _load_dir_for_arch(), main(), RuntimeError, Run S1 fracture event; return dataset record + fragment list. threshold_scale…, Feed IDENTICAL saved S1 fragments through S2 arch screen model. eff_scale…, P0/P1 may not enter S2 fracture (wrap study S1-only). (+11 more)

### Community 20 - "generate"
Cohesion: 0.14
Nodes (12): check_admissible(), generate(), main(), OversizeError, ValueError, random_quaternion(), I2 deterministic waste taxonomy generator (stdlib + numpy only). Classes: W1…, I2 waste generator regressions (read-only vs C2.1; stdlib+unittest+numpy).… (+4 more)

### Community 21 - "Inputs"
Cohesion: 0.07
Nodes (27): Inputs, aux_demand_W, band_rotation_ms, buffer_full, estop_closed, fan_required, fan_tach_ok, gauge_major_mm (+19 more)

### Community 22 - "electrical_bay.py"
Cohesion: 0.15
Nodes (24): _box(), components(), contactor(), current_limiter(), din_rail(), driver(), driver_1(), driver_2() (+16 more)

### Community 23 - "components"
Cohesion: 0.12
Nodes (24): auger_bearings(), belt_bearings(), belt_chain(), belt_drum(), belt_follower_sprocket(), components(), cross_feed_bearings(), cross_feed_shell() (+16 more)

### Community 24 - "Thermal"
Cohesion: 0.29
Nodes (5): Carry thermal state through batch/fan-fault segments; still uncalibrated., Thermal, thermal_duty_run(), thermal_run(), ThermalTests

### Community 25 - "run_study.py"
Cohesion: 0.13
Nodes (16): allocate_power(), Fail-closed control reference. NOT deployable motor/heater firmware., Reference admission only; PSU 792 W rating does not raise this budget., evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., Lower-bound heat capacities from generated C2 metal volumes, not measured…, thermal_capacities_from_cad() (+8 more)

### Community 26 - "InvalidMechanism"
Cohesion: 0.27
Nodes (7): check_envelope(), get(), InvalidMechanism, ValueError, Zero clearance, bad direction sign, missing baseline, bad envelope., TestEnvelope, TestInvalidGap

### Community 27 - "NonphysicalError"
Cohesion: 0.14
Nodes (13): _components(), find(), union(), FractureInputError, FractureResult, Fragment, NonphysicalError, RuntimeError (+5 more)

### Community 28 - "test_r03_causality.py"
Cohesion: 0.06
Nodes (8): R0.3 causality/accounting unit tests (system python3, isaac-free). >= 10 tests:…, TestAtomicVsComponent, TestD3Distinguishability, TestD4Faults, TestD4Ledger, TestDiagConstants, TestNullStatus, TestTimedDisable

### Community 29 - "d4_accounting.py"
Cohesion: 0.16
Nodes (19): compare_metrics(), _isaac_child(), jam_status(), main(), make_buckets(), ordered_sum(), passage_status(), D4 observability / accounting / negative tests (Goal R0 section 4, D4). Isaac… (+11 more)

### Community 30 - "run_case.py"
Cohesion: 0.15
Nodes (19): build_run_config(), dt_label(), dt_source_mapping(), finalize(), _import_s1(), main(), prepare(), A2 single-case Isaac headless runner (ONE frozen case + ONE ladder dt). REUSE… (+11 more)

### Community 31 - "analyze.py"
Cohesion: 0.18
Nodes (14): csv, scipy_linalg, scipy_optimize, allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is… (+6 more)

### Community 32 - "render_reviewer_scenes.py"
Cohesion: 0.18
Nodes (17): isaac_capture(), look_at_matrix(), main(), probe_positions(), Path, Reviewer scenes for the PPR VP1 full machine (c2.2 acceptance item 2). Renders…, Use only a connected probe run for this exact STEP and USD., RTX attempt with a disk heartbeat. Kit quirk on this host: exceptions raised… (+9 more)

### Community 33 - "d2_torque.py"
Cohesion: 0.08
Nodes (21): boundary_work(), _cross(), _dot(), _isaac_child(), on_post(), main(), D2 torque/work semantics diagnostic (Goal R0 section 4, D2). Definitions…, Axial contact torque on ONE shaft. contacts: iterable of (position_p,… (+13 more)

### Community 34 - "design.py"
Cohesion: 0.11
Nodes (15): copy, box(), cyl(), part(), plate(), PPR C1 dimensional master. Generates a backend-neutral constructive-solid model., ring(), write_all() (+7 more)

### Community 35 - "C2 Engineering Contracts"
Cohesion: 0.11
Nodes (18): Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, C2 Engineering Contracts, Run C2 Numerical Study, Run C2 Unit Tests, Actual Run Counts Must Equal Dynamic Evidence Inventory Counts (+10 more)

### Community 36 - "Controller"
Cohesion: 0.12
Nodes (18): Controller, BAND_ROTATION_PERIOD_MS, command_, gauge_gate_, gauge_seen_, integral_, latched_, limits_ (+10 more)

### Community 37 - "json"
Cohesion: 0.08
Nodes (30): VP1 Stage 4 rev 2: S2 negative-rotation direction audit (Isaac evidence). The…, PowerGateTests, Behavioral regressions for reference-feed extrusion and gauge geometry., VP1 Stage 1: real drivetrain geometry + S1->S2 chute tests. CAD-dependent tests…, I3 single-event fracture smoke benchmark (Isaac-independent, numpy-only). 12…, I4 cheap geometric/kinematic screening (Isaac-independent, numpy LHS). Samples…, I5 low-resolution end-to-end S1->S2 benchmark (Isaac-independent, numpy).…, I3 fallback bond manager over the I2 BondGraph data model. Same… (+22 more)

### Community 39 - "run_combo"
Cohesion: 0.16
Nodes (11): check_ordering(), main(), OrderingError, RuntimeError, Fixed-lattice probe: identical geometry+seed, class strengths vary. Elementwise…, P0/P1 strand bundles carry no fracture claim (wrap risk only)., Nominal class ordering violated — nonphysical configuration., run_combo() (+3 more)

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
Cohesion: 0.19
Nodes (16): assembly_geometry_checks(), imported(), bbox_overlap(), bounds(), c21_parts(), collision_audit(), extent(), main() (+8 more)

### Community 47 - "chute.py"
Cohesion: 0.15
Nodes (12): bypass_channel_floor(), cutter_sweep_solids(), _guide(), _prism_xy(), VP1 Stage 1: real transfer chute from the S1 discharge opening to the C2.1 S2…, Conservative S1 cutter sweep envelopes for clearance checks., No stationary ribs in the screw pickup or flight zone., Longitudinal U cradle, opened locally into the powered cross pickup. The old… (+4 more)

### Community 48 - "engineering.py"
Cohesion: 0.16
Nodes (14): design_set(), diverse_selection(), equivalent_motor_load(), main(), Path, C2 deterministic engineering study. Numerical assumptions are not test evidence., write_json(), fit_gp() (+6 more)

### Community 49 - "s1_physx.py"
Cohesion: 0.25
Nodes (7): build_bond_list(), cell_lattice(), main(), Gate B: PhysX S1 twin-shaft (S1-A) + waste fragment clusters + breaking bonds.…, # NOTE: NO use_backend("tensor") scope: the ContactSensor, Recover lattice (nx,ny,nz,dx,dy,dz) by regenerating the specimen., Rebuild 6-neighbourhood lattice bonds matching bonds.lattice_graph.

### Community 50 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 51 - "ChuteGeometry"
Cohesion: 0.14
Nodes (4): ChainGeometry, ChuteGeometry, GearGeometry, skipUnless

### Community 52 - "BondManager"
Cohesion: 0.23
Nodes (9): load_dir_for(), BondManager, Deterministic fallback fracture over a BondGraph., fixed_lattice(), TestDeterminism, TestInvalidInput, TestOrientationDependence, TestW1ZFirst (+1 more)

### Community 53 - "VP1 whole-machine Isaac Sim validation"
Cohesion: 0.14
Nodes (14): Connected particulate transport HOLD, CROSS_FEED_SHAFT transverse screw, Rear output plate feed-mount clearance, S2 negative-direction geometry sweep, Historical proxy-result exclusion, Development PR versus physical-release policy, VP1 STEP/USD and result provenance, Stage-wise material flow localization (+6 more)

### Community 54 - "c2/src/build_cad.py"
Cohesion: 0.23
Nodes (13): box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector(), wire() (+5 more)

### Community 55 - "bonds.py"
Cohesion: 0.25
Nodes (8): Bond, BondGraph, Cell, lattice_graph(), I2 bond-graph: cells/chunks + directional bonds (nominal strengths only).…, 6-neighbourhood lattice; x->in_raster, y->cross_raster, z->inter_layer_z. Cell…, Return list of violations (empty == valid)., TestBondValidity

### Community 56 - "ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)"
Cohesion: 0.15
Nodes (12): ADDENDUM (2026-09-22, VP1 Stage 4, rev B — SUPERSEDES the rev A decision), ADDENDUM 3 (2026-09-23, VP1 Stage 5 활성 오거 — 연결 이송 HOLD), ADDENDUM 4 (2026-09-23, VP1 횡방향 이송과 S2 출력 지지판), ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs), REV B 부록 2 (2026-09-22, Isaac 통합 피드백 2건), 검증 경계와 HOLD, 결정 (rev B), 결정 (부품별) (+4 more)

### Community 57 - "d3_bond.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), D3 two-body coupling causality diagnostic (Goal R0 section 4, D3). CONSTRAINT…, run_one(), run_paths(), sha256_file(), Diagnostic Summary

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

### Community 64 - "PPR-KODEX (영구 규칙 · 목표)"
Cohesion: 0.20
Nodes (9): 1. VP1 경성 목표 (Hard Goal), 2. 고정 조건 (변경 금지, 합의 필요 시에만 사용자 승인으로 변경), 3. 방법론, 4. 검증 경계, 5. Git 경계, PPR-KODEX (영구 규칙 · 목표), C2.1 Active Digital Iteration, Base Runtime and CAD Dependencies (+1 more)

### Community 65 - "auger_shaft"
Cohesion: 0.25
Nodes (11): auger_shaft(), _cross_feed_flight(), cross_feed_shaft(), _helix_z(), _path_frame(), Split shaft with a swept, opposite-hand screw and keyed spur., Point and unit tangent at the initial vertex of a swept helix., Single right-hand helicoid with a 3 mm swept flight face. (+3 more)

### Community 66 - "_prism_xz"
Cohesion: 0.13
Nodes (15): belt_loop(), capsule(), intake_lip(), _prism_xz(), Historical ratchet rib retained for inspection, not installed., Historical pan-only ribs, superseded by the active transfer design., 45deg intake lip under the S1 -X side strip (the opening's west edge); all…, Two side loops leave a continuous, separately driven central lane. (+7 more)

### Community 67 - "src/build_cad.py"
Cohesion: 0.39
Nodes (6): bbox(), build(), main(), primitive(), CadQuery/OCP verification backend for the shared constructive-solid master. The…, wire3()

### Community 68 - "screen_open_area"
Cohesion: 0.22
Nodes (6): main(), screen_candidate(), Open-area fraction proxy: hole pitch ~ 2x diameter triangular grid. Returns…, screen_open_area(), TestHopperGate, TestScreenArea

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

### Community 75 - "strengths_for_class"
Cohesion: 0.20
Nodes (6): graph_from_meta(), Rebuild the exact I2 lattice from waste_gen metadata. Mirrors…, strengths_for_class(), TestMassConservation, TestAnisotropyOrdering, TestMassConservation

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

### Community 84 - "subprocess"
Cohesion: 0.18
Nodes (10): load(), main(), Build deterministic P0-P6 + VP1 digital status and artifact manifests., sha256(), Gate E: 3-level dt sweep on one W1 + one W4 case (thin driver over s1_physx).…, main(), Gate F: real gap x screen sweep on survivors (thin driver). S1 gap sweep: shaft…, run() (+2 more)

### Community 85 - "Limits"
Cohesion: 0.29
Nodes (6): Limits, jam_current_A, jam_minimum_rpm, maximum_temperature_C, operational_cap_W, stale_feedback_ms

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

### Community 93 - "ES-16 groove and washer stop spool escape, with axial float"
Cohesion: 0.40
Nodes (5): Smalley ES-16 dimensional candidate without project load rating, SSB-0087 published work height incompatible with present clutch seat, Thrust washer radial margin is conditional not a strength claim, SSB-0087 rated work height is not matched by 1 mm clutch seat, ES-16 groove and washer stop spool escape, with axial float

### Community 94 - "power_sim.py"
Cohesion: 0.38
Nodes (6): admitted_load(), demand_at(), main(), VP1 Stage 4: virtual duty-cycle power simulation over the nameplate table.…, (demands, stage) at time t_s. loads = {key: W}., Mirror firmware admission; unknown/denied aux holds the entire line.

### Community 95 - "run_r3.py"
Cohesion: 0.33
Nodes (6): _isaac_child(), main(), R3 runner: staged sustained-contact diagnostics T1/T2/T3. Reviewer-approved…, run_paths(), run_stage_dt(), sha256_file()

### Community 97 - "C2.2 VP1 실행 씬 출처와 증거 경계"
Cohesion: 0.40
Nodes (4): C2.2 VP1 실행 씬 출처와 증거 경계, 디지털 검증과 물리 검증의 구분, 정책, 활성 원본

### Community 98 - "Fixed C2 System Constraints"
Cohesion: 0.40
Nodes (5): PPR C2 Engineering Baseline, 136-Row Cost Review Ledger, Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope

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

### Community 112 - "sample_candidates"
Cohesion: 0.29
Nodes (6): lhs(), ndarray, ValueError, sample_candidates(), ScreenInputError, TestSamplerDeterminism

### Community 117 - "argparse"
Cohesion: 0.22
Nodes (8): argparse, Gate D: real hole-geometry collision screen passage (S2-A rotor + S2-B ref). No…, deck(), main(), Path, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., reaction_force(), shutil

### Community 119 - "check_baseline_present"
Cohesion: 0.40
Nodes (4): check_baseline_present(), validate_all(), TestBaselinePresent, TestBaselinePresent

## Knowledge Gaps
- **235 isolated node(s):** `$schema`, `coordinate_units`, `date`, `included_severities`, `kicad_version` (+230 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 828 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **86 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `winder_mount()` connect `pull_cool_mount` to `winder.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `7. 같은 제품의 기준 원료 모델·제어·비용 비교 (VP1)` connect `pull_cool_mount` to `filament-quality-route.md`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `pull_cool_mount()` connect `pull_cool_mount` to `winder.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `$schema`, `coordinate_units`, `date` to the rest of the system?**
  _235 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `process_model.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05432692307692308 - nodes in this community are weakly interconnected._
- **Should `pull_cool_mount` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._
- **Should `os` be split into smaller, more focused modules?**
  _Cohesion score 0.05974025974025974 - nodes in this community are weakly interconnected._