# Graph Report - PPR-c2.1-codex-20260921  (2026-09-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1989 nodes · 3669 edges · 196 communities (102 shown, 94 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 294 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `228f4f93`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- c2.1/src/build_cad.py
- process_model.py
- full_machine.py
- json
- verify_contract.py
- drive_teeth.py
- test_telemetry.py
- engineering.py
- winder.py
- i6_surrogate.py
- downstream.py
- run_one_phase
- performance.py
- filament-quality-route.md
- test_contract.py
- s1_event
- Inputs
- hashlib
- run_study.py
- generate
- ControllerTests
- electrical_bay.py
- components
- traceback
- BondManager
- d4_accounting.py
- run_case.py
- build_machine_integration.py
- NonphysicalError
- render_reviewer_scenes.py
- approx
- C2 Engineering Contracts
- Controller
- c2/src/build_cad.py
- guards.py
- i3_coupon.py
- PPR C1 Dimensioned Engineering Review Package
- design.py
- analyze.py
- make_drawings.py
- controller_core.cpp
- structural_screen.py
- relocated_gravity.py
- Outputs
- os
- architectures.py
- bonds.py
- d2_torque.py
- C2.1 S2 Transmission Schematic
- chute.py
- _prism_xz
- DesignContracts
- VP1 whole-machine Isaac Sim validation
- ChuteGeometry
- ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)
- build_freecad.py
- run_r1.py
- TestVerifier
- Open Physical Actions Register
- _box
- ProcessModelPhysicsTests
- InvalidMechanism
- run_r4_t2b.py
- auger_shaft
- run_r2.py
- Fail-Closed Thermal and Jam Control Reference
- hopper_panels.py
- pull_cool_mount
- DownstreamGeometryTests
- emit_usd.py
- C2.3-A-R3 리뷰 핸드오프 (판정 요청)
- d0_clock.py
- d3_bond.py
- PPR-KODEX (영구 규칙 · 목표)
- train_performance.py
- sample_candidates
- C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)
- d1_contact.py
- PPR_C2_1_machine_wiring_erc.json
- build_machine_wiring.py
- build_system_bom.py
- pan_floor
- _feed_gear
- REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)
- PPR C1 CAD Inspection Image
- Limits
- power_sim.py
- MaterialPathApertures
- C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F
- screen_candidate
- MissingEvidenceError
- c2/src/verify_artifacts.py
- geometry.py
- Single-Input Reverse-Output S2 Drivetrain
- worm_sleeve
- c2.1/src/verify_artifacts.py
- check_admissible
- check_baseline_present
- TestD4Ledger
- TestNullStatus
- GearRatioKinematics
- C2.2 VP1 실행 씬 출처와 증거 경계
- Fixed C2 System Constraints
- Active C2 Baseline
- nip_opening_mm
- pull_roller_adj
- FeedbackTests
- C2.2 — VP1 전체 기계 Isaac Sim 검증
- s2a_direction_phi
- TestSchema
- TestD3Distinguishability
- TestD4Faults
- REFERENCE/UNRATED worm, wheel, shafts, bearings and motor
- Shared M1 one-degree-of-freedom S1/S2 drive
- comparison_contract
- TestSchema
- convergence/manifest.json
- r2/manifest.json
- r3/manifest.json
- TestDiagConstants
- TestAtomicVsComponent
- TestDiagConstants
- TestTimedDisable
- C1 Digital Contracts
- Stage 5 active chute auger
- Function-preserving integration reliefs
- Four-turn auger and transverse screw active chute
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

## Communities (196 total, 94 thin omitted)

### Community 0 - "c2.1/src/build_cad.py"
Cohesion: 0.06
Nodes (68): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+60 more)

### Community 1 - "process_model.py"
Cohesion: 0.06
Nodes (53): build_library(), library_for_source(), main(), Build the same C++ PI kernel used by the host controller self-test., Avoid stale shared code in process-model calculations., _add(), chute_checks(), _dist_to_s2() (+45 more)

### Community 2 - "full_machine.py"
Cohesion: 0.06
Nodes (47): _bbox(), candidate_manifest(), _candidate_mass_properties(), _candidate_parts(), git_head(), _lod_of(), main(), Path (+39 more)

### Community 3 - "json"
Cohesion: 0.08
Nodes (31): argparse, VP1 Stage 4 rev 2: S2 negative-rotation direction audit (Isaac evidence). The…, PowerGateTests, Behavioral regressions for reference-feed extrusion and gauge geometry., VP1 Stage 1: real drivetrain geometry + S1->S2 chute tests. CAD-dependent tests…, I4 cheap geometric/kinematic screening (Isaac-independent, numpy LHS). Samples…, I5 low-resolution end-to-end S1->S2 benchmark (Isaac-independent, numpy).…, I3 fallback bond manager over the I2 BondGraph data model. Same… (+23 more)

### Community 4 - "verify_contract.py"
Cohesion: 0.06
Nodes (45): Gate F follow-on: refit surrogate anchors on REAL dynamics data (additive).…, _load(), Gate A-F dynamics contract tests (no SimulationApp: manifest/schema only)., A reused STL path erased the south S1 tread in the executable scene., test_dt_sweep_complete(), test_full_machine_compound_solids_have_distinct_contact_meshes(), test_gap_screen_sweep_complete(), test_s1_runs_real_physics() (+37 more)

### Community 5 - "drive_teeth.py"
Cohesion: 0.09
Nodes (39): chain_length_mm(), gear_center_distance(), gear_pitch_radius(), ratio_chain(), Pure kinematics/math for the VP1 common drive — NO cadquery dependency. Split…, Transverse pitch radius of a helical gear (normal module mn)., External tangent construction in XZ. Returns the two touch-point 4-tuples, the…, Kinematic chain from the VP1 Stage 4 layout (teeth counts only). M1 -> DRV-… (+31 more)

### Community 6 - "test_telemetry.py"
Cohesion: 0.09
Nodes (15): aggregate(), load_run(), A2 aggregate: telemetry.jsonl + events.jsonl -> derived quantities. Mass:…, reject_proxy(), ledger(), load_run(), A2 partial mechanical energy ledger (NEVER claims closure). residual = W_in -…, A2 telemetry/analysis tests (>=10): integrals, mass, ledger, convergence, proxy… (+7 more)

### Community 7 - "engineering.py"
Cohesion: 0.12
Nodes (18): design_set(), diverse_selection(), equivalent_motor_load(), generalized_torque(), hook_polygon(), kinematics(), main(), packaging() (+10 more)

### Community 8 - "winder.py"
Cohesion: 0.12
Nodes (35): _box(), components(), _cyl(), _flange(), pull_frame(), pull_motor_ref(), pull_nip_stop(), pull_roller_fixed() (+27 more)

### Community 9 - "i6_surrogate.py"
Cohesion: 0.10
Nodes (27): main(), Gate F: real gap x screen sweep on survivors (thin driver). S1 gap sweep: shaft…, run(), bo_search(), build_pareto(), dominates(), evaluate_on_rows(), features() (+19 more)

### Community 10 - "downstream.py"
Cohesion: 0.11
Nodes (30): _bounds(), _box(), build_result(), components(), cool_duct(), cool_fan_3_ref(), _cyl(), gauge_contact_a() (+22 more)

### Community 11 - "run_one_phase"
Cohesion: 0.07
Nodes (23): buffer_throat_contains(), gravity_mouth_contains(), gravity_receiver_contains(), hole_transition(), main(), Path, Return (candidate, completed_hole) for one descending physics step. The…, Sphere envelope inside the actual octagonal Ø13 lower clear throat. (+15 more)

### Community 12 - "performance.py"
Cohesion: 0.12
Nodes (14): candidate_hashes(), canonical_sha256(), evidence_inventory(), EvidenceError, main(), nondominated(), ndarray, Path (+6 more)

### Community 13 - "filament-quality-route.md"
Cohesion: 0.09
Nodes (31): Three-fan cooling thermal sensitivity and geometric apertures, Seller-price sensor candidates and unquoted total landed cost, 269 mm formation-to-gauge feedback dead time, NVIDIA EULA refusal prevents new Isaac native contact-flow test, 500 W operating cap leaves 76 W before unselected auxiliary motors, Two-axis uncalibrated gauge and missing-readout reject gate, Single-pass feedback A, optional reheating B, same-hardware fixed C comparison, 1. 사용자 결정과 작업 상태 (+23 more)

### Community 14 - "test_contract.py"
Cohesion: 0.09
Nodes (13): check_executor_label(), _forbidden_labels(), A1 contract tests (stdlib unittest, goal section 22). Banned terminal labels…, Accept only the Isaac Sim / PhysX backend descriptor., Proxy records (analytic diagnostic only) are inadmissible., reject_proxy(), rel_change(), rel_mass_error() (+5 more)

### Community 15 - "s1_event"
Cohesion: 0.10
Nodes (20): BenchmarkError, _equiv_dims(), _load_dir_for_arch(), main(), RuntimeError, Run S1 fracture event; return dataset record + fragment list. threshold_scale…, Feed IDENTICAL saved S1 fragments through S2 arch screen model. eff_scale…, P0/P1 may not enter S2 fracture (wrap study S1-only). (+12 more)

### Community 16 - "Inputs"
Cohesion: 0.07
Nodes (27): Inputs, aux_demand_W, band_rotation_ms, buffer_full, estop_closed, fan_required, fan_tach_ok, gauge_major_mm (+19 more)

### Community 17 - "hashlib"
Cohesion: 0.11
Nodes (20): Host-build the portable controller core; no target flash or energization., load(), main(), Build deterministic P0-P6 + VP1 digital status and artifact manifests., sha256(), _isaac_child(), main(), R3 runner: staged sustained-contact diagnostics T1/T2/T3. Reviewer-approved… (+12 more)

### Community 18 - "run_study.py"
Cohesion: 0.17
Nodes (13): Carry thermal state through batch/fan-fault segments; still uncalibrated., Lower-bound heat capacities from generated C2 metal volumes, not measured…, Thermal, thermal_capacities_from_cad(), thermal_duty_run(), thermal_matrix(), thermal_run(), _canon() (+5 more)

### Community 19 - "generate"
Cohesion: 0.10
Nodes (14): build_bond_list(), cell_lattice(), main(), Recover lattice (nx,ny,nz,dx,dy,dz) by regenerating the specimen., Rebuild 6-neighbourhood lattice bonds matching bonds.lattice_graph., strengths_for_class(), generate(), main() (+6 more)

### Community 20 - "ControllerTests"
Cohesion: 0.13
Nodes (7): allocate_power(), Controller, Fail-closed control reference. NOT deployable motor/heater firmware., Reference admission only; PSU 792 W rating does not raise this budget., controller(), ControllerTests, dataclasses

### Community 21 - "electrical_bay.py"
Cohesion: 0.15
Nodes (24): _box(), components(), contactor(), current_limiter(), din_rail(), driver(), driver_1(), driver_2() (+16 more)

### Community 22 - "components"
Cohesion: 0.12
Nodes (24): auger_bearings(), belt_bearings(), belt_chain(), belt_drum(), belt_follower_sprocket(), components(), cross_feed_bearings(), cross_feed_shell() (+16 more)

### Community 23 - "traceback"
Cohesion: 0.11
Nodes (15): Gate A loader: open c2.2/sim/assets/usd/machine.usda headless, report stage…, fail(), main(), I0 SimulationApp smoke: headless stage + one rigid cube, 60 physics steps. Gate…, # NOTE: close() os._exit()s via fast shutdown on success, so the JSON, Gate B: PhysX S1 twin-shaft (S1-A) + waste fragment clusters + breaking bonds.…, # NOTE: NO use_backend("tensor") scope: the ContactSensor, Gate D: real hole-geometry collision screen passage (S2-A rotor + S2-B ref). No… (+7 more)

### Community 24 - "BondManager"
Cohesion: 0.19
Nodes (11): BondManager, Deterministic fallback fracture over a BondGraph., fixed_lattice(), I3 fracture regressions: determinism, conservation, orderings, gaps. Evidence:…, TestDeterminism, TestInvalidInput, TestMassConservation, TestOrientationDependence (+3 more)

### Community 25 - "d4_accounting.py"
Cohesion: 0.16
Nodes (19): compare_metrics(), _isaac_child(), jam_status(), main(), make_buckets(), ordered_sum(), passage_status(), D4 observability / accounting / negative tests (Goal R0 section 4, D4). Isaac… (+11 more)

### Community 26 - "run_case.py"
Cohesion: 0.15
Nodes (19): build_run_config(), dt_label(), dt_source_mapping(), finalize(), _import_s1(), main(), prepare(), A2 single-case Isaac headless runner (ONE frozen case + ONE ladder dt). REUSE… (+11 more)

### Community 27 - "build_machine_integration.py"
Cohesion: 0.17
Nodes (18): assembly_geometry_checks(), imported(), bbox_overlap(), bounds(), c21_parts(), collision_audit(), extent(), legacy_parts() (+10 more)

### Community 28 - "NonphysicalError"
Cohesion: 0.14
Nodes (13): _components(), find(), union(), FractureInputError, FractureResult, Fragment, NonphysicalError, RuntimeError (+5 more)

### Community 29 - "render_reviewer_scenes.py"
Cohesion: 0.18
Nodes (17): isaac_capture(), look_at_matrix(), main(), probe_positions(), Path, Reviewer scenes for the PPR VP1 full machine (c2.2 acceptance item 2). Renders…, Use only a connected probe run for this exact STEP and USD., RTX attempt with a disk heartbeat. Kit quirk on this host: exceptions raised… (+9 more)

### Community 30 - "approx"
Cohesion: 0.16
Nodes (5): approx(), TestBoundaryWork, TestD0SubstepMapping, TestD1UnitRule, TestShaftTorque

### Community 31 - "C2 Engineering Contracts"
Cohesion: 0.11
Nodes (18): Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, C2 Engineering Contracts, Run C2 Numerical Study, Run C2 Unit Tests, Actual Run Counts Must Equal Dynamic Evidence Inventory Counts (+10 more)

### Community 32 - "Controller"
Cohesion: 0.12
Nodes (18): Controller, BAND_ROTATION_PERIOD_MS, command_, gauge_gate_, gauge_seen_, integral_, latched_, limits_ (+10 more)

### Community 33 - "c2/src/build_cad.py"
Cohesion: 0.20
Nodes (14): box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector(), wire() (+6 more)

### Community 34 - "guards.py"
Cohesion: 0.18
Nodes (16): _box(), components(), guard_chain_a(), guard_chain_b(), guard_lid_interlock_seat(), guard_s2_ring(), VP1 Stage 2: real containment guards, E-stop mounts and interlock seats.…, Named guard parts in absolute machine coordinates (group 'guard'). (+8 more)

### Community 35 - "i3_coupon.py"
Cohesion: 0.18
Nodes (13): check_ordering(), load_dir_for(), main(), OrderingError, RuntimeError, I3 single-event fracture smoke benchmark (Isaac-independent, numpy-only). 12…, Fixed-lattice probe: identical geometry+seed, class strengths vary. Elementwise…, P0/P1 strand bundles carry no fracture claim (wrap risk only). (+5 more)

### Community 36 - "PPR C1 Dimensioned Engineering Review Package"
Cohesion: 0.12
Nodes (17): BLOCKED_PERFORMANCE_DATA, C1-SEED Comparison Point, Coupled Kinematic Work Model, Eccentric Sleeve Wall Constraint, Geometry and Assembly Screen, PLA PET and TPU Calibration Plan, 144-Job Performance Manifest, Qualified GP and MLP Performance Learning Pipeline (+9 more)

### Community 37 - "design.py"
Cohesion: 0.15
Nodes (10): copy, box(), cyl(), part(), plate(), PPR C1 dimensional master. Generates a backend-neutral constructive-solid model., ring(), write_all() (+2 more)

### Community 38 - "analyze.py"
Cohesion: 0.18
Nodes (14): csv, scipy_linalg, scipy_optimize, allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is… (+6 more)

### Community 39 - "make_drawings.py"
Cohesion: 0.21
Nodes (16): ezdxf, reportlab_lib_pagesizes, reportlab_pdfbase, reportlab_pdfbase_ttfonts, reportlab_pdfgen, shapely_ops, dim(), drawshape() (+8 more)

### Community 40 - "controller_core.cpp"
Cohesion: 0.16
Nodes (15): algorithm, array, band_count(), diameter_pi_step(), main(), PowerDevice, name, W (+7 more)

### Community 41 - "structural_screen.py"
Cohesion: 0.19
Nodes (14): ast, bending_point(), case(), flange_thickness(), literal_dict_assignment(), margin(), Bounded, non-qualifying structural and thermal screen for VP1 hardware. Run:…, Read dimension constants without importing CadQuery or regenerating CAD. (+6 more)

### Community 42 - "relocated_gravity.py"
Cohesion: 0.25
Nodes (14): at_box(), gravity_parts(), loft_section(), main(), nominal_mass(), other_parts(), pairs(), Independent, non-release relocated S2 gravity-handoff alternative. Runs against… (+6 more)

### Community 43 - "Outputs"
Cohesion: 0.14
Nodes (14): Outputs, admitted_W, aux_enable, fans_enable, gauge_in_tolerance, h100_enable, h60_enable, m1_enable (+6 more)

### Community 44 - "os"
Cohesion: 0.14
Nodes (10): Gate E: 3-level dt sweep on one W1 + one W4 case (thin driver over s1_physx).…, Gate C: DERIVED transfer assets (S1 discharge + chute + S2 entry/exit). C2.1…, FIX A: material-flow localization for the integrated PPR VP1 machine. The last…, # NOTE: the contact-report event stream (subscribe_contact_report_, body_of(), Full-machine motion verification under Isaac Sim 6.1 headless PhysX. Loads the…, Classify a collision prim path into a body token., # NOTE: extra_args is the only channel that reaches the kit process — (+2 more)

### Community 45 - "architectures.py"
Cohesion: 0.25
Nodes (14): validate_mechanisms(), Architecture, check_clearance(), check_direction(), get(), I4 mechanism architecture library (Isaac-independent, numpy-free). 7 variants:…, _s1a(), _s1b() (+6 more)

### Community 46 - "bonds.py"
Cohesion: 0.22
Nodes (10): graph_from_meta(), Rebuild the exact I2 lattice from waste_gen metadata. Mirrors…, Bond, BondGraph, Cell, lattice_graph(), I2 bond-graph: cells/chunks + directional bonds (nominal strengths only).…, 6-neighbourhood lattice; x->in_raster, y->cross_raster, z->inter_layer_z. Cell… (+2 more)

### Community 47 - "d2_torque.py"
Cohesion: 0.21
Nodes (14): boundary_work(), _cross(), _dot(), _isaac_child(), on_post(), main(), D2 torque/work semantics diagnostic (Goal R0 section 4, D2). Definitions…, Axial contact torque on ONE shaft. contacts: iterable of (position_p,… (+6 more)

### Community 48 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 49 - "chute.py"
Cohesion: 0.15
Nodes (12): bypass_channel_floor(), cutter_sweep_solids(), _guide(), _prism_xy(), VP1 Stage 1: real transfer chute from the S1 discharge opening to the C2.1 S2…, Conservative S1 cutter sweep envelopes for clearance checks., No stationary ribs in the screw pickup or flight zone., Longitudinal U cradle, opened locally into the powered cross pickup. The old… (+4 more)

### Community 50 - "_prism_xz"
Cohesion: 0.13
Nodes (15): belt_loop(), capsule(), intake_lip(), _prism_xz(), Historical ratchet rib retained for inspection, not installed., Historical pan-only ribs, superseded by the active transfer design., 45deg intake lip under the S1 -X side strip (the opening's west edge); all…, Two side loops leave a continuous, separately driven central lane. (+7 more)

### Community 52 - "VP1 whole-machine Isaac Sim validation"
Cohesion: 0.14
Nodes (14): Connected particulate transport HOLD, CROSS_FEED_SHAFT transverse screw, Rear output plate feed-mount clearance, S2 negative-direction geometry sweep, Historical proxy-result exclusion, Development PR versus physical-release policy, VP1 STEP/USD and result provenance, Stage-wise material flow localization (+6 more)

### Community 53 - "ChuteGeometry"
Cohesion: 0.14
Nodes (4): ChainGeometry, ChuteGeometry, GearGeometry, skipUnless

### Community 54 - "ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)"
Cohesion: 0.15
Nodes (12): ADDENDUM (2026-09-22, VP1 Stage 4, rev B — SUPERSEDES the rev A decision), ADDENDUM 3 (2026-09-23, VP1 Stage 5 활성 오거 — 연결 이송 HOLD), ADDENDUM 4 (2026-09-23, VP1 횡방향 이송과 S2 출력 지지판), ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs), REV B 부록 2 (2026-09-22, Isaac 통합 피드백 2건), 검증 경계와 HOLD, 결정 (rev B), 결정 (부품별) (+4 more)

### Community 55 - "build_freecad.py"
Cohesion: 0.23
Nodes (11): main(), Create the native FreeCAD C2.1 machine assembly from checked STEP parts., read_shape(), freecad, part, build(), face(), primitive() (+3 more)

### Community 56 - "run_r1.py"
Cohesion: 0.23
Nodes (10): build_case_geometry(), _isaac_child(), main(), R1 runner: one canonical case at ONE ladder dt, equal 2.4 s physics. Contract:…, # NOTE: Gf.Vector3f hard-crashes (SIGSEGV) in this Isaac build;, # NOTE: work integral requires tau_shaft from typed contacts;, Deterministic per-case fragment positions from waste_gen dims., run_case_dt() (+2 more)

### Community 58 - "Open Physical Actions Register"
Cohesion: 0.17
Nodes (12): C2.1 Digital Assembly Service and Test Package, Lockout and Staged Physical Test, DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD, P6 Full Machine Digital Integration, Remaining Rating and Performance Holds, Motor Floor Exceeds System Soft Budget, Open Physical Actions Register, C2.1 P0-P6 Integration Plan (+4 more)

### Community 59 - "_box"
Cohesion: 0.17
Nodes (12): _box(), bypass_wall_north_lower(), bypass_wall_south(), guide_left(), guide_right(), South containment, relieved only at the low-y spur-gear face., North containment ends before the orthogonal screw's west cheek., Central lane wall; transverse screw supplies lateral transport. (+4 more)

### Community 61 - "InvalidMechanism"
Cohesion: 0.23
Nodes (8): check_envelope(), InvalidMechanism, ValueError, Open-area fraction proxy: hole pitch ~ 2x diameter triangular grid. Returns…, Zero clearance, bad direction sign, missing baseline, bad envelope., screen_open_area(), TestEnvelope, TestScreenArea

### Community 62 - "run_r4_t2b.py"
Cohesion: 0.17
Nodes (9): R4-T2b: chain suspended via end posts (FixedJoint), NO pin, gravity + preload…, isaacsim, isaacsim_core_experimental_objects, isaacsim_core_experimental_prims, isaacsim_core_experimental_utils_stage, isaacsim_core_simulation_manager, omni_physx, omni_timeline (+1 more)

### Community 63 - "auger_shaft"
Cohesion: 0.25
Nodes (11): auger_shaft(), _cross_feed_flight(), cross_feed_shaft(), _helix_z(), _path_frame(), Split shaft with a swept, opposite-hand screw and keyed spur., Point and unit tangent at the initial vertex of a swept helix., Single right-hand helicoid with a 3 mm swept flight face. (+3 more)

### Community 64 - "run_r2.py"
Cohesion: 0.29
Nodes (8): R2 Review Handoff Summary, build_case_geometry(), _isaac_child(), main(), R2 runner: per-physics-step contact stream + signed shaft load + boundary work…, run_case_dt(), run_paths(), sha256_file()

### Community 65 - "Fail-Closed Thermal and Jam Control Reference"
Cohesion: 0.25
Nodes (11): CAD-Derived Heat-Capacity Lower Bounds, Clean-Air Cooling Path, Clean Filter, Clogged Filter, and Fan-Failure Sensitivity, Fail-Closed Thermal and Jam Control Reference, Five-Node Chamber and Drivetrain Thermal Circuit, Fixed-Shear Sensor Path, Independent Hardware Safety Chain, P5 Digital Thermal and Control Boundary (+3 more)

### Community 66 - "hopper_panels.py"
Cohesion: 0.40
Nodes (9): _bore(), components(), _inner_y(), _nut_boss(), Split the historical C1 hopper BRep into bounded PC panels and steel seam…, Return two distinct PC print solids and two steel bolted seam straps. The split…, _strap(), ocp_brepextrema (+1 more)

### Community 67 - "pull_cool_mount"
Cohesion: 0.24
Nodes (10): pull_cool_mount(), Rear-profile rack carries the thin cooling tray and puller separately. Face…, Ø70×58 steel tube, 2 mm wall, with two 3 mm internal steel webs. The Ø17 web…, spool_drum(), Direct steel puller and cooling tray rack, 7. 같은 제품의 기준 원료 모델·제어·비용 비교 (VP1), Hollow steel winding drum mass and unrated mount, PULL_COOL_MOUNT rear-frame tray and nip load path (+2 more)

### Community 69 - "emit_usd.py"
Cohesion: 0.36
Nodes (9): box_mesh(), convex_hull_of_verts(), git_head(), load_stl_verts_faces(), main(), mesh_prim(), Path, Gate A: machine USD emission from staged STL + parametric DERIVED transfer… (+1 more)

### Community 70 - "C2.3-A-R3 리뷰 핸드오프 (판정 요청)"
Cohesion: 0.20
Nodes (9): 1. R3 결과 요약, 2. T1 상세 (5% GATE_MET), 3. T2 BLOCKED 상세 (픽스처 반복 이력), 4. 리뷰어 지시 반영 상태, 5. 미해결 (리뷰어 승인 필요), 6. 실행자 결론 불가, 7. CI 상태 (정확 커밋 a431df75), 8. R4-T2b 추가 반복 (리뷰어 승인 fixture 변경 실행 결과) (+1 more)

### Community 71 - "d0_clock.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), D0 clock + 2.4 s horizon diagnostic (Goal R0 section 4, D0). Minimal scene:…, Child body: runs under the Isaac venv python; one dt only., run_dt(), run_paths(), sha256_file()

### Community 72 - "d3_bond.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), D3 two-body coupling causality diagnostic (Goal R0 section 4, D3). CONSTRAINT…, run_one(), run_paths(), sha256_file(), Diagnostic Summary

### Community 73 - "PPR-KODEX (영구 규칙 · 목표)"
Cohesion: 0.20
Nodes (9): 1. VP1 경성 목표 (Hard Goal), 2. 고정 조건 (변경 금지, 합의 필요 시에만 사용자 승인으로 변경), 3. 방법론, 4. 검증 경계, 5. Git 경계, PPR-KODEX (영구 규칙 · 목표), C2.1 Active Digital Iteration, Base Runtime and CAD Dependencies (+1 more)

### Community 74 - "train_performance.py"
Cohesion: 0.33
Nodes (8): Any, Path, write_json(), fit_gp(), fit_mlp(), grouped_split(), main(), Material-specific GP or deep-ensemble training on verified S2 PERFORMANCE only.…

### Community 75 - "sample_candidates"
Cohesion: 0.25
Nodes (7): lhs(), main(), ndarray, ValueError, sample_candidates(), ScreenInputError, TestSamplerDeterminism

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

### Community 80 - "build_system_bom.py"
Cohesion: 0.36
Nodes (7): column_name(), main(), Build the active C2.1 system BOM without mutating the historical C1 BOM., rows(), write_xlsx(), collections, xml_sax_saxutils

### Community 81 - "pan_floor"
Cohesion: 0.25
Nodes (8): _c21_transform(), _obstruction_solid(), pan_floor(), Apply the frozen c2_subassembly_transform to a c2 local-frame part., Frozen S2 jacket solids that pierce the chute floor plane: the…, S1 discharge basin with a recessed, supported belt pocket., Landing ledge over the mouth (x 278.5..310, y 255..295); cut where the frozen…, trough_floor()

### Community 82 - "_feed_gear"
Cohesion: 0.25
Nodes (8): cross_feed_gear(), cross_feed_idler(), _feed_gear(), pdl_feed_gear(), Six-mm, 12T involute spur face, keyed on its +X bore flank., 12T keyed output gear sharing the existing PDL shaft., 12T integral intermediate wheel on its own two supported journals., Equal 12T keyed output wheel; two external meshes restore PDL sign.

### Community 83 - "REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)"
Cohesion: 0.25
Nodes (7): 1. 구현 (작성 파일 — 커밋 없음), 2. 실행 (진단별 결과 — 수치), 3. 수렴 (해당 없음 — R0는 진단, 수렴 판정 아님), 4. 미수렴 (해당 없음), 5. 미해결 (리뷰어 승인 필요 — 실행자가 해소 불가), 6. 실행자 결론 불가 항목, REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)

### Community 84 - "PPR C1 CAD Inspection Image"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 85 - "Limits"
Cohesion: 0.29
Nodes (6): Limits, jam_current_A, jam_minimum_rpm, maximum_temperature_C, operational_cap_W, stale_feedback_ms

### Community 86 - "power_sim.py"
Cohesion: 0.38
Nodes (6): admitted_load(), demand_at(), main(), VP1 Stage 4: virtual duty-cycle power simulation over the nameplate table.…, (demands, stage) at time t_s. loads = {key: W}., Mirror firmware admission; unknown/denied aux holds the entire line.

### Community 88 - "C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F"
Cohesion: 0.29
Nodes (6): (a) I0–I6 numpy 프록시층 (유지, UNCALIBRATED ordering smoke), (b) C2.2b 실제 headless PhysX 동역학 Gates A–F (Isaac 6.1.0.0, `c2.2/results/dyn_*`), C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F, HOLD / 미해결 (승인 없이 진행 금지), 게이트 테이블, 리비전

### Community 89 - "screen_candidate"
Cohesion: 0.33
Nodes (3): screen_candidate(), TestHopperGate, TestInvalidGap

### Community 90 - "MissingEvidenceError"
Cohesion: 0.33
Nodes (6): MissingEvidenceError, RuntimeError, Raised when calibrated (measured) strength data is requested. No physical…, Calibrated fracture strength lookup — always fails loudly (no data)., require_calibrated_strength(), TestMissingEvidence

### Community 91 - "c2/src/verify_artifacts.py"
Cohesion: 0.38
Nodes (5): evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., _canon(), Check active C2 evidence and CAD integrity without authorizing hardware.

### Community 92 - "geometry.py"
Cohesion: 0.29
Nodes (5): chain_center(), gear_section(), hooks(), Deterministic section geometry. Units: millimetres, radians., Reference involute section; root fillets/tolerances NOT a manufacturing profile.

### Community 93 - "Single-Input Reverse-Output S2 Drivetrain"
Cohesion: 0.33
Nodes (6): Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative, Torque and Reaction Path, Unverified Rating and Fabrication Limits

### Community 94 - "worm_sleeve"
Cohesion: 0.33
Nodes (6): auger_wheel(), _helix_about_y(), Right-hand helix advancing along +Y with a specified bottom phase., PDL_WORM: right-hand two-start swept threads keyed to the shaft., Sector gear at the auger end, generated against the actual worm. The swept worm…, worm_sleeve()

### Community 95 - "c2.1/src/verify_artifacts.py"
Cohesion: 0.33
Nodes (3): Verify the C2.1 P0-P6 digital package without granting hardware approval., xml_etree_elementtree, zipfile

### Community 96 - "check_admissible"
Cohesion: 0.40
Nodes (4): check_admissible(), OversizeError, ValueError, TestHopperReject

### Community 97 - "check_baseline_present"
Cohesion: 0.40
Nodes (4): check_baseline_present(), validate_all(), TestBaselinePresent, TestBaselinePresent

### Community 101 - "C2.2 VP1 실행 씬 출처와 증거 경계"
Cohesion: 0.40
Nodes (4): C2.2 VP1 실행 씬 출처와 증거 경계, 디지털 검증과 물리 검증의 구분, 정책, 활성 원본

### Community 102 - "Fixed C2 System Constraints"
Cohesion: 0.40
Nodes (5): PPR C2 Engineering Baseline, 136-Row Cost Review Ledger, Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope

### Community 103 - "Active C2 Baseline"
Cohesion: 0.50
Nodes (4): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Safety-Preserving Cost Reduction Order

### Community 104 - "nip_opening_mm"
Cohesion: 0.33
Nodes (4): nip_opening_mm(), nip_range_mm(), Minimum nip gap with the carriage seated on the cam positive stop: roller…, (minimum at the hard stop, maximum with the cam screw fully open).

### Community 105 - "pull_roller_adj"
Cohesion: 0.50
Nodes (4): pull_roller_adj(), Coil spring (helical sweep) between the carriage and the frame cap., Dia-20 SPRING-LOADED adjustable roller at the hard-stop position (minimum nip…, _spring()

### Community 107 - "C2.2 — VP1 전체 기계 Isaac Sim 검증"
Cohesion: 0.50
Nodes (3): C2.2 — VP1 전체 기계 Isaac Sim 검증, 검증 경계, 주요 경로

### Community 108 - "s2a_direction_phi"
Cohesion: 0.50
Nodes (3): S2-A law: phi = -theta/q (reverse, sign -1)., s2a_direction_phi(), TestS2ADirection

### Community 112 - "REFERENCE/UNRATED worm, wheel, shafts, bearings and motor"
Cohesion: 0.67
Nodes (3): Keyed PDL, auger, S2 and jackshaft torque paths, REFERENCE/UNRATED worm, wheel, shafts, bearings and motor, Single 15T/40T helical mesh

### Community 113 - "Shared M1 one-degree-of-freedom S1/S2 drive"
Cohesion: 0.67
Nodes (3): S2 single-input reference kinematics, Shared M1 one-degree-of-freedom S1/S2 drive, VP1 fixed electrical, envelope, budget and material constraints

## Knowledge Gaps
- **233 isolated node(s):** `디지털 검증과 물리 검증의 구분`, `정책`, `활성 원본`, `검증 경계`, `주요 경로` (+228 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 828 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **94 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ControllerTests` connect `ControllerTests` to `json`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `pull_cool_mount()` connect `pull_cool_mount` to `winder.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `7. 같은 제품의 기준 원료 모델·제어·비용 비교 (VP1)` connect `pull_cool_mount` to `filament-quality-route.md`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `디지털 검증과 물리 검증의 구분`, `정책`, `활성 원본` to the rest of the system?**
  _233 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `c2.1/src/build_cad.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05636114911080711 - nodes in this community are weakly interconnected._
- **Should `process_model.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05683060109289618 - nodes in this community are weakly interconnected._
- **Should `full_machine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05875706214689266 - nodes in this community are weakly interconnected._