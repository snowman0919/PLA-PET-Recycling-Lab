# Graph Report - PPR-c2.1-codex-20260921  (2026-09-27)

## Corpus Check
- 1154 files · ~14,071,811 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1450 file(s) not represented in the graph (top: .stl 671, .step 235, .log 204)

## Summary
- 1922 nodes · 3531 edges · 189 communities (103 shown, 86 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 290 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b1e02a99`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Transmission
- chute.py
- S2
- bonds.py
- electrical_bay.py
- TestVerifier
- BondManager
- analyze.py
- process_model.py
- run_study.py
- winder.py
- test_telemetry.py
- test_contract.py
- s1_event
- structural_screen.py
- relocated_gravity.py
- Inputs
- EvidenceTests
- components
- d4_accounting.py
- d2_torque.py
- run_full
- i3_coupon.py
- architectures.py
- approx
- C2 Engineering Contracts
- generate
- c2.1/src/build_cad.py
- run_one_phase
- PPR C1 Dimensioned Engineering Review Package
- sample_candidates
- ControllerTests
- downstream.py
- build_freecad.py
- NonphysicalError
- C2.1 S2 Transmission Schematic
- drive_teeth.py
- src/build_cad.py
- ChainGeometry
- run_r1.py
- Material-flow HOLD despite localized S2 cap-bore transfer
- Open Physical Actions Register
- path_check.py
- run_case.py
- os
- controller_core.cpp
- PPR_C2_1_machine_wiring_erc.json
- Outputs
- VP1 whole-machine Isaac Sim validation
- s2a_direction_phi
- d3_bond.py
- Fail-Closed Thermal and Jam Control Reference
- DesignContracts
- make_drawings.py
- emit_usd.py
- run_r4_t2b.py
- verify_contract.py
- Controller
- build_system_bom.py
- PPR C1 CAD Inspection Image
- design.py
- power_sim.py
- MaterialPathApertures
- ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)
- Single-Input Reverse-Output S2 Drivetrain
- build_machine_integration.py
- C2.3-A-R3 리뷰 핸드오프 (판정 요청)
- c2/src/build_cad.py
- run_r3.py
- C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)
- hashlib
- engineering.py
- render_reviewer_scenes.py
- Fixed C2 System Constraints
- Active C2 Baseline
- InvalidMechanism
- build_machine_wiring.py
- REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)
- test_dynamics.py
- C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F
- MissingEvidenceError
- convergence/manifest.json
- r2/manifest.json
- r3/manifest.json
- build_p6_drawings.py
- 결정 기록 — 저비용 1.75mm 필라멘트 품질 우선 경로
- C1 Digital Contracts
- test_waste_gen.py
- C2.2 VP1 실행 씬 출처와 증거 경계
- Clause A1 (Steps-per-run)
- Clause A2 (Metrics calculation)
- Clause A3 (Mass conservation)
- Clause A4 (Missing-event handling)
- Clause A5 (Scene provenance)
- Clause A6 (Break/fragment accounting)
- Clause A7 (Threshold applicability)
- Thermal
- d1_contact.py
- DownstreamGeometryTests
- main
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
- run_r2.py
- Goal R0 §2 (Numerical reliability closure)
- Hopper Interior Geometry
- ISAAC_PHYSX backend
- d0_clock.py
- Kinematic Frame F0 Definition
- Machine Body Dimensions
- Mass conservation threshold
- Motion Law Equations
- Nominal Motion Parameters
- ProcessModelPhysicsTests
- Revision R1
- BLOCKED_PERFORMANCE_DATA
- Required artifacts list
- Residence time threshold
- GearRatioKinematics
- DiameterGate
- ControllerSafetyTests
- build_release_manifest.py
- test_benchmark.py
- S1 Cutter Parameters
- S2 Local Frame Definition
- Shaft work threshold
- screen_open_area
- json
- TestSchema
- C2.2 — VP1 전체 기계 Isaac Sim 검증
- bypass_channel_floor
- write_json
- TestD4Ledger
- TestNullStatus
- _box
- i6_surrogate.py
- auger_shaft
- TestD3Distinguishability
- TestD4Faults
- comparison_contract
- TestDiagConstants
- pan_floor
- _feed_gear
- REFERENCE/UNRATED worm, wheel, shafts, bearings and motor
- Stage 5 active chute auger
- Function-preserving integration reliefs
- Host-tested firmware power allocation
- 24V 33A PSU, 500W soft target and 792W current ceiling
- Conservative cycloidal pin-ring screen
- C2.3 tribometer, crown and joint expansion stopped
- AST graph update does not complete semantic extraction
- worm_sleeve

## God Nodes (most connected - your core abstractions)
1. `components()` - 41 edges
2. `S2` - 32 edges
3. `Inputs` - 30 edges
4. `Transmission` - 30 edges
5. `_box()` - 26 edges
6. `BondManager` - 26 edges
7. `_cyl()` - 22 edges
8. `s1_event()` - 22 edges
9. `generate()` - 22 edges
10. `run_full()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `S2 Cycloidal Guide, Sleeve, and Pin Rings` --semantically_similar_to--> `Small Pin-Ring Feasibility Screen`  [INFERRED] [semantically similar]
  drawings/PPR_C1_dimensioned_review.pdf → c2/docs/C2_ENGINEERING_NOTES.md
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `Nominal Drawing Fabrication Hold` --semantically_similar_to--> `Open Physical Actions Register`  [INFERRED] [semantically similar]
  c2.1/drawings/PPR_C2_1_P6_nominal_plate_review.pdf → c2.1/docs/OPEN_ACTIONS_KO.md
- `Electrical Fabrication and Energization Hold` --semantically_similar_to--> `Open Physical Actions Register`  [INFERRED] [semantically similar]
  c2.1/electrical/PPR_C2_1_machine_wiring.pdf → c2.1/docs/OPEN_ACTIONS_KO.md
- `Safety-Preserving Cost Reduction Order` --semantically_similar_to--> `Evidence and Safety Boundaries`  [INFERRED] [semantically similar]
  c2/docs/CALIBRATION_AND_RFQ.md → AGENTS.md

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

## Communities (189 total, 86 thin omitted)

### Community 0 - "Transmission"
Cohesion: 0.12
Nodes (24): main(), cad_positive_y_rotation_xz(), coupling(), external_mesh_sign(), ideal_virtual_work(), loaded_contact_sweep(), loaded_contact_takeup(), residual() (+16 more)

### Community 1 - "chute.py"
Cohesion: 0.11
Nodes (22): belt_loop(), capsule(), cutter_sweep_solids(), intake_lip(), _prism_xz(), VP1 Stage 1: real transfer chute from the S1 discharge opening to the C2.1 S2…, Historical ratchet rib retained for inspection, not installed., No stationary ribs in the screw pickup or flight zone. (+14 more)

### Community 2 - "S2"
Cohesion: 0.14
Nodes (14): Any, design_set(), generalized_torque(), hook_polygon(), kinematics(), packaging(), point_jacobian(), polygon_area() (+6 more)

### Community 3 - "bonds.py"
Cohesion: 0.22
Nodes (10): graph_from_meta(), Rebuild the exact I2 lattice from waste_gen metadata. Mirrors…, Bond, BondGraph, Cell, lattice_graph(), I2 bond-graph: cells/chunks + directional bonds (nominal strengths only).…, 6-neighbourhood lattice; x->in_raster, y->cross_raster, z->inter_layer_z. Cell… (+2 more)

### Community 4 - "electrical_bay.py"
Cohesion: 0.15
Nodes (24): _box(), components(), contactor(), current_limiter(), din_rail(), driver(), driver_1(), driver_2() (+16 more)

### Community 6 - "BondManager"
Cohesion: 0.19
Nodes (11): BondManager, Deterministic fallback fracture over a BondGraph., fixed_lattice(), I3 fracture regressions: determinism, conservation, orderings, gaps. Evidence:…, TestDeterminism, TestInvalidInput, TestMassConservation, TestOrientationDependence (+3 more)

### Community 7 - "analyze.py"
Cohesion: 0.14
Nodes (16): main(), Gate F: real gap x screen sweep on survivors (thin driver). S1 gap sweep: shaft…, run(), itertools, scipy_linalg, allocate(), clearance_metric(), cooling() (+8 more)

### Community 8 - "process_model.py"
Cohesion: 0.09
Nodes (30): area_mm2(), cooling_rate_C_s(), h_effective(), HeaterSchedule, LineParams, LineState, ovality(), quality_summary() (+22 more)

### Community 9 - "run_study.py"
Cohesion: 0.12
Nodes (17): allocate_power(), Fail-closed control reference. NOT deployable motor/heater firmware., Reference admission only; PSU 792 W rating does not raise this budget., evaluate(), main(), Lower-bound heat capacities from generated C2 metal volumes, not measured…, thermal_capacities_from_cad(), thermal_matrix() (+9 more)

### Community 10 - "winder.py"
Cohesion: 0.11
Nodes (37): _box(), components(), _cyl(), _flange(), nip_opening_mm(), nip_range_mm(), pull_frame(), pull_motor_ref() (+29 more)

### Community 11 - "test_telemetry.py"
Cohesion: 0.09
Nodes (15): aggregate(), load_run(), A2 aggregate: telemetry.jsonl + events.jsonl -> derived quantities. Mass:…, reject_proxy(), ledger(), load_run(), A2 partial mechanical energy ledger (NEVER claims closure). residual = W_in -…, A2 telemetry/analysis tests (>=10): integrals, mass, ledger, convergence, proxy… (+7 more)

### Community 12 - "test_contract.py"
Cohesion: 0.09
Nodes (13): check_executor_label(), _forbidden_labels(), A1 contract tests (stdlib unittest, goal section 22). Banned terminal labels…, Accept only the Isaac Sim / PhysX backend descriptor., Proxy records (analytic diagnostic only) are inadmissible., reject_proxy(), rel_change(), rel_mass_error() (+5 more)

### Community 13 - "s1_event"
Cohesion: 0.14
Nodes (19): BenchmarkError, _equiv_dims(), _load_dir_for_arch(), main(), RuntimeError, I5 low-resolution end-to-end S1->S2 benchmark (Isaac-independent, numpy).…, Run S1 fracture event; return dataset record + fragment list. threshold_scale…, Feed IDENTICAL saved S1 fragments through S2 arch screen model. eff_scale… (+11 more)

### Community 14 - "structural_screen.py"
Cohesion: 0.19
Nodes (14): ast, bending_point(), case(), flange_thickness(), literal_dict_assignment(), margin(), Bounded, non-qualifying structural and thermal screen for VP1 hardware. Run:…, Read dimension constants without importing CadQuery or regenerating CAD. (+6 more)

### Community 15 - "relocated_gravity.py"
Cohesion: 0.08
Nodes (39): at_box(), gravity_parts(), loft_section(), main(), nominal_mass(), other_parts(), pairs(), Independent, non-release relocated S2 gravity-handoff alternative. Runs against… (+31 more)

### Community 16 - "Inputs"
Cohesion: 0.08
Nodes (26): Inputs, aux_demand_W, band_rotation_ms, buffer_full, estop_closed, fan_required, fan_tach_ok, gauge_diameter_mm (+18 more)

### Community 17 - "EvidenceTests"
Cohesion: 0.13
Nodes (11): evidence_inventory(), EvidenceError, main(), nondominated(), ndarray, Path, ValueError, training_gate() (+3 more)

### Community 18 - "components"
Cohesion: 0.12
Nodes (24): auger_bearings(), belt_bearings(), belt_chain(), belt_drum(), belt_follower_sprocket(), components(), cross_feed_bearings(), cross_feed_shell() (+16 more)

### Community 19 - "d4_accounting.py"
Cohesion: 0.16
Nodes (19): compare_metrics(), _isaac_child(), jam_status(), main(), make_buckets(), ordered_sum(), passage_status(), D4 observability / accounting / negative tests (Goal R0 section 4, D4). Isaac… (+11 more)

### Community 20 - "d2_torque.py"
Cohesion: 0.21
Nodes (14): boundary_work(), _cross(), _dot(), _isaac_child(), on_post(), main(), D2 torque/work semantics diagnostic (Goal R0 section 4, D2). Definitions…, Axial contact torque on ONE shaft. contacts: iterable of (position_p,… (+6 more)

### Community 21 - "run_full"
Cohesion: 0.10
Nodes (23): _bbox(), candidate_manifest(), _candidate_mass_properties(), _candidate_parts(), git_head(), _lod_of(), main(), Path (+15 more)

### Community 22 - "i3_coupon.py"
Cohesion: 0.18
Nodes (13): check_ordering(), load_dir_for(), main(), OrderingError, RuntimeError, I3 single-event fracture smoke benchmark (Isaac-independent, numpy-only). 12…, Fixed-lattice probe: identical geometry+seed, class strengths vary. Elementwise…, P0/P1 strand bundles carry no fracture claim (wrap risk only). (+5 more)

### Community 23 - "architectures.py"
Cohesion: 0.22
Nodes (16): validate_mechanisms(), Architecture, check_baseline_present(), check_clearance(), check_direction(), I4 mechanism architecture library (Isaac-independent, numpy-free). 7 variants:…, _s1a(), _s1b() (+8 more)

### Community 24 - "approx"
Cohesion: 0.16
Nodes (5): approx(), TestBoundaryWork, TestD0SubstepMapping, TestD1UnitRule, TestShaftTorque

### Community 25 - "C2 Engineering Contracts"
Cohesion: 0.11
Nodes (18): Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, C2 Engineering Contracts, Run C2 Numerical Study, Run C2 Unit Tests, Actual Run Counts Must Equal Dynamic Evidence Inventory Counts (+10 more)

### Community 26 - "generate"
Cohesion: 0.11
Nodes (15): build_bond_list(), cell_lattice(), main(), Recover lattice (nx,ny,nz,dx,dy,dz) by regenerating the specimen., Rebuild 6-neighbourhood lattice bonds matching bonds.lattice_graph., check_admissible(), generate(), main() (+7 more)

### Community 27 - "c2.1/src/build_cad.py"
Cohesion: 0.16
Nodes (30): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+22 more)

### Community 28 - "run_one_phase"
Cohesion: 0.07
Nodes (23): buffer_throat_contains(), gravity_mouth_contains(), gravity_receiver_contains(), hole_transition(), main(), Path, Return (candidate, completed_hole) for one descending physics step. The…, Sphere envelope inside the actual octagonal Ø13 lower clear throat. (+15 more)

### Community 29 - "PPR C1 Dimensioned Engineering Review Package"
Cohesion: 0.12
Nodes (17): BLOCKED_PERFORMANCE_DATA, C1-SEED Comparison Point, Coupled Kinematic Work Model, Eccentric Sleeve Wall Constraint, Geometry and Assembly Screen, PLA PET and TPU Calibration Plan, 144-Job Performance Manifest, Qualified GP and MLP Performance Learning Pipeline (+9 more)

### Community 30 - "sample_candidates"
Cohesion: 0.29
Nodes (6): lhs(), ndarray, ValueError, sample_candidates(), ScreenInputError, TestSamplerDeterminism

### Community 31 - "ControllerTests"
Cohesion: 0.19
Nodes (3): Controller, controller(), ControllerTests

### Community 32 - "downstream.py"
Cohesion: 0.13
Nodes (28): _bounds(), _box(), build_result(), components(), cool_duct(), _cyl(), gauge_contact_a(), gauge_frame() (+20 more)

### Community 33 - "build_freecad.py"
Cohesion: 0.21
Nodes (12): main(), Create the native FreeCAD C2.1 machine assembly from checked STEP parts., read_shape(), freecad, part, build(), face(), primitive() (+4 more)

### Community 34 - "NonphysicalError"
Cohesion: 0.14
Nodes (13): _components(), find(), union(), FractureInputError, FractureResult, Fragment, NonphysicalError, RuntimeError (+5 more)

### Community 35 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 36 - "drive_teeth.py"
Cohesion: 0.09
Nodes (40): legacy_parts(), chain_length_mm(), gear_center_distance(), gear_pitch_radius(), ratio_chain(), Pure kinematics/math for the VP1 common drive — NO cadquery dependency. Split…, Transverse pitch radius of a helical gear (normal module mn)., External tangent construction in XZ. Returns the two touch-point 4-tuples, the… (+32 more)

### Community 37 - "src/build_cad.py"
Cohesion: 0.39
Nodes (6): bbox(), build(), main(), primitive(), CadQuery/OCP verification backend for the shared constructive-solid master. The…, wire3()

### Community 38 - "ChainGeometry"
Cohesion: 0.15
Nodes (4): ChainGeometry, ChuteGeometry, GearGeometry, skipUnless

### Community 39 - "run_r1.py"
Cohesion: 0.23
Nodes (10): build_case_geometry(), _isaac_child(), main(), R1 runner: one canonical case at ONE ladder dt, equal 2.4 s physics. Contract:…, # NOTE: Gf.Vector3f hard-crashes (SIGSEGV) in this Isaac build;, # NOTE: work integral requires tau_shaft from typed contacts;, Deterministic per-case fragment positions from waste_gen dims., run_case_dt() (+2 more)

### Community 40 - "Material-flow HOLD despite localized S2 cap-bore transfer"
Cohesion: 0.14
Nodes (15): Four-turn auger and transverse screw active chute, Release manifest after generated evidence, S2 single-input reference kinematics, Real-geometry candidate validation method, Digital verification is not physical approval, Shared M1 one-degree-of-freedom S1/S2 drive, VP1 integrated product hard goal, Digital results do not release physical work or main merge (+7 more)

### Community 41 - "Open Physical Actions Register"
Cohesion: 0.17
Nodes (12): C2.1 Digital Assembly Service and Test Package, Lockout and Staged Physical Test, DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD, P6 Full Machine Digital Integration, Remaining Rating and Performance Holds, Motor Floor Exceeds System Soft Budget, Open Physical Actions Register, C2.1 P0-P6 Integration Plan (+4 more)

### Community 42 - "path_check.py"
Cohesion: 0.18
Nodes (14): _add(), chute_checks(), _dist_to_s2(), downstream_checks(), layout_options(), main(), VP1 material-path geometry checkpoints; not a product-flow certificate.…, Measure the exported VP1 S2 screen, not the historical C1 radial screen. (+6 more)

### Community 43 - "run_case.py"
Cohesion: 0.15
Nodes (19): build_run_config(), dt_label(), dt_source_mapping(), finalize(), _import_s1(), main(), prepare(), A2 single-case Isaac headless runner (ONE frozen case + ONE ladder dt). REUSE… (+11 more)

### Community 44 - "os"
Cohesion: 0.13
Nodes (11): Gate A loader: open c2.2/sim/assets/usd/machine.usda headless, report stage…, fail(), main(), I0 SimulationApp smoke: headless stage + one rigid cube, 60 physics steps. Gate…, # NOTE: close() os._exit()s via fast shutdown on success, so the JSON, Gate B: PhysX S1 twin-shaft (S1-A) + waste fragment clusters + breaking bonds.…, # NOTE: NO use_backend("tensor") scope: the ContactSensor, Gate D: real hole-geometry collision screen passage (S2-A rotor + S2-B ref). No… (+3 more)

### Community 45 - "controller_core.cpp"
Cohesion: 0.22
Nodes (10): array, band_count(), main(), PowerDevice, name, W, safe_inputs(), cassert (+2 more)

### Community 46 - "PPR_C2_1_machine_wiring_erc.json"
Cohesion: 0.25
Nodes (7): coordinate_units, date, included_severities, kicad_version, $schema, sheets, source

### Community 47 - "Outputs"
Cohesion: 0.18
Nodes (11): Outputs, admitted_W, aux_enable, fans_enable, h100_enable, h60_enable, m1_enable, m2_enable (+3 more)

### Community 48 - "VP1 whole-machine Isaac Sim validation"
Cohesion: 0.14
Nodes (14): Connected particulate transport HOLD, CROSS_FEED_SHAFT transverse screw, Rear output plate feed-mount clearance, S2 negative-direction geometry sweep, Historical proxy-result exclusion, Development PR versus physical-release policy, VP1 STEP/USD and result provenance, Stage-wise material flow localization (+6 more)

### Community 49 - "s2a_direction_phi"
Cohesion: 0.50
Nodes (3): S2-A law: phi = -theta/q (reverse, sign -1)., s2a_direction_phi(), TestS2ADirection

### Community 50 - "d3_bond.py"
Cohesion: 0.12
Nodes (11): _isaac_child(), main(), D3 two-body coupling causality diagnostic (Goal R0 section 4, D3). CONSTRAINT…, run_one(), run_paths(), sha256_file(), R0.3 causality/accounting unit tests (system python3, isaac-free). >= 10 tests:…, TestAtomicVsComponent (+3 more)

### Community 51 - "Fail-Closed Thermal and Jam Control Reference"
Cohesion: 0.25
Nodes (11): CAD-Derived Heat-Capacity Lower Bounds, Clean-Air Cooling Path, Clean Filter, Clogged Filter, and Fan-Failure Sensitivity, Fail-Closed Thermal and Jam Control Reference, Five-Node Chamber and Drivetrain Thermal Circuit, Fixed-Shear Sensor Path, Independent Hardware Safety Chain, P5 Digital Thermal and Control Boundary (+3 more)

### Community 53 - "make_drawings.py"
Cohesion: 0.21
Nodes (16): ezdxf, reportlab_lib_pagesizes, reportlab_pdfbase, reportlab_pdfbase_ttfonts, reportlab_pdfgen, shapely_ops, dim(), drawshape() (+8 more)

### Community 54 - "emit_usd.py"
Cohesion: 0.36
Nodes (9): box_mesh(), convex_hull_of_verts(), git_head(), load_stl_verts_faces(), main(), mesh_prim(), Path, Gate A: machine USD emission from staged STL + parametric DERIVED transfer… (+1 more)

### Community 55 - "run_r4_t2b.py"
Cohesion: 0.17
Nodes (9): R4-T2b: chain suspended via end posts (FixedJoint), NO pin, gravity + preload…, isaacsim, isaacsim_core_experimental_objects, isaacsim_core_experimental_prims, isaacsim_core_experimental_utils_stage, isaacsim_core_simulation_manager, omni_physx, omni_timeline (+1 more)

### Community 56 - "verify_contract.py"
Cohesion: 0.20
Nodes (16): epsilon(), evaluate(), _frag_count(), load_thresholds(), A2 convergence evaluator. Thresholds are parsed, NEVER hardcoded. Sources:…, check_config_hashes(), check_convergence(), check_ladder() (+8 more)

### Community 57 - "Controller"
Cohesion: 0.18
Nodes (12): Controller, BAND_ROTATION_PERIOD_MS, gauge_gate_, latched_, limits_, Limits, jam_current_A, jam_minimum_rpm (+4 more)

### Community 58 - "build_system_bom.py"
Cohesion: 0.12
Nodes (14): column_name(), main(), Build the active C2.1 system BOM without mutating the historical C1 BOM., rows(), write_xlsx(), Verify the C2.1 P0-P6 digital package without granting hardware approval., Full incremental procurement coverage. A missing quotation is not zero cost., _canon() (+6 more)

### Community 59 - "PPR C1 CAD Inspection Image"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 60 - "design.py"
Cohesion: 0.13
Nodes (14): box(), cyl(), part(), plate(), PPR C1 dimensional master. Generates a backend-neutral constructive-solid model., ring(), write_all(), chain_center() (+6 more)

### Community 61 - "power_sim.py"
Cohesion: 0.38
Nodes (6): admitted_load(), demand_at(), main(), VP1 Stage 4: virtual duty-cycle power simulation over the nameplate table.…, (demands, stage) at time t_s. loads = {key: W}., Apply the controller's priority allocator and hard modeled budget.

### Community 63 - "ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs)"
Cohesion: 0.15
Nodes (12): ADDENDUM (2026-09-22, VP1 Stage 4, rev B — SUPERSEDES the rev A decision), ADDENDUM 3 (2026-09-23, VP1 Stage 5 활성 오거 — 연결 이송 HOLD), ADDENDUM 4 (2026-09-23, VP1 횡방향 이송과 S2 출력 지지판), ADR-002: VP1 체인 경로 vs 동결된 C1 구조물 릴리프 (chain routing reliefs), REV B 부록 2 (2026-09-22, Isaac 통합 피드백 2건), 검증 경계와 HOLD, 결정 (rev B), 결정 (부품별) (+4 more)

### Community 64 - "Single-Input Reverse-Output S2 Drivetrain"
Cohesion: 0.33
Nodes (6): Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative, Torque and Reaction Path, Unverified Rating and Fabrication Limits

### Community 65 - "build_machine_integration.py"
Cohesion: 0.19
Nodes (15): bbox_overlap(), c21_parts(), collision_audit(), extent(), main(), normalize_step_timestamp(), Build and verify the C2.1 S2 subassembly inside the complete C1 machine. C1 is…, Check the moving S2 rotor against fixed feed metal, not just theta=0. Five-… (+7 more)

### Community 66 - "C2.3-A-R3 리뷰 핸드오프 (판정 요청)"
Cohesion: 0.20
Nodes (9): 1. R3 결과 요약, 2. T1 상세 (5% GATE_MET), 3. T2 BLOCKED 상세 (픽스처 반복 이력), 4. 리뷰어 지시 반영 상태, 5. 미해결 (리뷰어 승인 필요), 6. 실행자 결론 불가, 7. CI 상태 (정확 커밋 a431df75), 8. R4-T2b 추가 반복 (리뷰어 승인 fixture 변경 실행 결과) (+1 more)

### Community 67 - "c2/src/build_cad.py"
Cohesion: 0.23
Nodes (13): box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector(), wire() (+5 more)

### Community 68 - "run_r3.py"
Cohesion: 0.33
Nodes (6): _isaac_child(), main(), R3 runner: staged sustained-contact diagnostics T1/T2/T3. Reviewer-approved…, run_paths(), run_stage_dt(), sha256_file()

### Community 69 - "C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)"
Cohesion: 0.22
Nodes (8): 1. 구현, 2. 실행, 3. 수렴 (주 쌍 0.0025 vs 0.00125), 4. 수렴하지 않은 항목 (정직 기록), 5. overall_numerically_converged = True의 의미, 6. 미해결 (리뷰어 승인 필요), 7. 실행자 결론 불가, C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)

### Community 70 - "hashlib"
Cohesion: 0.12
Nodes (14): Host-build the portable controller core; no target flash or energization., Gate E: 3-level dt sweep on one W1 + one W4 case (thin driver over s1_physx).…, A4 verifier tests (>=8): tamper detection, recompute checks. Forbidden terminal…, deck(), main(), Path, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., reaction_force() (+6 more)

### Community 71 - "engineering.py"
Cohesion: 0.19
Nodes (13): diverse_selection(), equivalent_motor_load(), main(), Path, C2 deterministic engineering study. Numerical assumptions are not test evidence., write_json(), fit_gp(), fit_mlp() (+5 more)

### Community 72 - "render_reviewer_scenes.py"
Cohesion: 0.18
Nodes (17): isaac_capture(), look_at_matrix(), main(), probe_positions(), Path, Reviewer scenes for the PPR VP1 full machine (c2.2 acceptance item 2). Renders…, Use only a connected probe run for this exact STEP and USD., RTX attempt with a disk heartbeat. Kit quirk on this host: exceptions raised… (+9 more)

### Community 73 - "Fixed C2 System Constraints"
Cohesion: 0.40
Nodes (5): PPR C2 Engineering Baseline, 136-Row Cost Review Ledger, Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope

### Community 74 - "Active C2 Baseline"
Cohesion: 0.50
Nodes (4): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Safety-Preserving Cost Reduction Order

### Community 75 - "InvalidMechanism"
Cohesion: 0.18
Nodes (10): main(), screen_candidate(), check_envelope(), get(), InvalidMechanism, ValueError, Zero clearance, bad direction sign, missing baseline, bad envelope., TestEnvelope (+2 more)

### Community 76 - "build_machine_wiring.py"
Cohesion: 0.36
Nodes (6): connector_symbol(), main(), Generate the review-only KiCad machine wiring schematic and pin/net ledger., uid(), write_schematic(), uuid

### Community 77 - "REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)"
Cohesion: 0.25
Nodes (7): 1. 구현 (작성 파일 — 커밋 없음), 2. 실행 (진단별 결과 — 수치), 3. 수렴 (해당 없음 — R0는 진단, 수렴 판정 아님), 4. 미수렴 (해당 없음), 5. 미해결 (리뷰어 승인 필요 — 실행자가 해소 불가), 6. 실행자 결론 불가 항목, REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)

### Community 78 - "test_dynamics.py"
Cohesion: 0.09
Nodes (28): Gate F follow-on: refit surrogate anchors on REAL dynamics data (additive).…, _load(), Gate A-F dynamics contract tests (no SimulationApp: manifest/schema only)., A reused STL path erased the south S1 tread in the executable scene., test_dt_sweep_complete(), test_full_machine_compound_solids_have_distinct_contact_meshes(), test_gap_screen_sweep_complete(), test_s1_runs_real_physics() (+20 more)

### Community 79 - "C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F"
Cohesion: 0.29
Nodes (6): (a) I0–I6 numpy 프록시층 (유지, UNCALIBRATED ordering smoke), (b) C2.2b 실제 headless PhysX 동역학 Gates A–F (Isaac 6.1.0.0, `c2.2/results/dyn_*`), C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F, HOLD / 미해결 (승인 없이 진행 금지), 게이트 테이블, 리비전

### Community 80 - "MissingEvidenceError"
Cohesion: 0.33
Nodes (6): MissingEvidenceError, RuntimeError, Raised when calibrated (measured) strength data is requested. No physical…, Calibrated fracture strength lookup — always fails loudly (no data)., require_calibrated_strength(), TestMissingEvidence

### Community 84 - "build_p6_drawings.py"
Cohesion: 0.27
Nodes (10): dimension(), main(), Export the few C2.1 plate drawings needed for fabrication review. These are…, ring_page(), sha256(), support_page(), datetime, matplotlib_backends_backend_pdf (+2 more)

### Community 85 - "결정 기록 — 저비용 1.75mm 필라멘트 품질 우선 경로"
Cohesion: 0.08
Nodes (23): 1. 사용자 결정과 작업 상태, 2. 조사에서 실제로 확인한 것, 3. 현재의 가성비 유력 기준안과 비교, 4. 간단하지만 제품과 연결된 모델, 5. 품질 측정과 가상시험의 경계, 6. 경제성 및 다음 작업, 7. 공정 모델 시뮬레이션 및 경로 비교 결과 (VP1 Stage 6), 결정 기록 — 저비용 1.75mm 필라멘트 품질 우선 경로 (+15 more)

### Community 87 - "test_waste_gen.py"
Cohesion: 0.22
Nodes (5): strengths_for_class(), I2 waste generator regressions (read-only vs C2.1; stdlib+unittest+numpy).…, TestAnisotropyOrdering, TestMassConservation, TestThermalIndexBounds

### Community 88 - "C2.2 VP1 실행 씬 출처와 증거 경계"
Cohesion: 0.40
Nodes (4): C2.2 VP1 실행 씬 출처와 증거 경계, 디지털 검증과 물리 검증의 구분, 정책, 활성 원본

### Community 96 - "Thermal"
Cohesion: 0.29
Nodes (5): Carry thermal state through batch/fan-fault segments; still uncalibrated., Thermal, thermal_duty_run(), thermal_run(), ThermalTests

### Community 97 - "d1_contact.py"
Cohesion: 0.36
Nodes (6): _isaac_child(), main(), D1 contact units + isolation diagnostic (Goal R0 section 4, D1). Exact…, run_one(), run_paths(), sha256_file()

### Community 98 - "DownstreamGeometryTests"
Cohesion: 0.36
Nodes (3): DownstreamGeometryTests, skipUnless, BRep validity and non-interference for downstream modules.

### Community 99 - "main"
Cohesion: 0.12
Nodes (20): main(), mesh_volume(), Path, FIX B(1): convex-hull fidelity audit for the integrated machine. For every…, Signed volume of a closed triangle mesh via the divergence theorem (mm^3). CAD-…, Sample a centre and 16 rim rays of each Ø3 screen exit in mesh XY., screen_vertical_mesh_paths(), sha256_file() (+12 more)

### Community 140 - "run_r2.py"
Cohesion: 0.29
Nodes (8): R2 Review Handoff Summary, build_case_geometry(), _isaac_child(), main(), R2 runner: per-physics-step contact stream + signed shaft load + boundary work…, run_case_dt(), run_paths(), sha256_file()

### Community 144 - "d0_clock.py"
Cohesion: 0.31
Nodes (7): _isaac_child(), main(), D0 clock + 2.4 s horizon diagnostic (Goal R0 section 4, D0). Minimal scene:…, Child body: runs under the Isaac venv python; one dt only., run_dt(), run_paths(), sha256_file()

### Community 156 - "DiameterGate"
Cohesion: 0.50
Nodes (4): DiameterGate, max_plausible_mm, min_plausible_mm, stale_ms

### Community 158 - "build_release_manifest.py"
Cohesion: 0.60
Nodes (4): load(), main(), Build deterministic P0-P6 + VP1 digital status and artifact manifests., sha256()

### Community 159 - "test_benchmark.py"
Cohesion: 0.15
Nodes (6): I5 end-to-end benchmark regressions (Isaac-independent, numpy-only). Evidence:…, TestBaselinePresent, TestS1Determinism, TestSameInputIdentity, TestSchema, TestTorqueScaling

### Community 163 - "screen_open_area"
Cohesion: 0.50
Nodes (3): Open-area fraction proxy: hole pitch ~ 2x diameter triangular grid. Returns…, screen_open_area(), TestScreenArea

### Community 164 - "json"
Cohesion: 0.08
Nodes (34): argparse, VP1 Stage 4 rev 2: S2 negative-rotation direction audit (Isaac evidence). The…, VP1 Stage 6: unit tests for downstream modules and process model. Verifies: 1.…, VP1 Stage 1: real drivetrain geometry + S1->S2 chute tests. CAD-dependent tests…, I1 asset pipeline: STEP -> decimated collision meshes + traceability sidecars.…, VP1 material choices and bounded mass properties for STEP-derived solids. These…, I4 cheap geometric/kinematic screening (Isaac-independent, numpy LHS). Samples…, FIX A: material-flow localization for the integrated PPR VP1 machine. The last… (+26 more)

### Community 166 - "C2.2 — VP1 전체 기계 Isaac Sim 검증"
Cohesion: 0.50
Nodes (3): C2.2 — VP1 전체 기계 Isaac Sim 검증, 검증 경계, 주요 경로

### Community 167 - "bypass_channel_floor"
Cohesion: 0.22
Nodes (9): assembly_geometry_checks(), imported(), bounds(), Verify that the exported STEP retains the active chute and auger. This is…, bypass_channel_floor(), _guide(), _prism_xy(), Longitudinal U cradle, opened locally into the powered cross pickup. The old… (+1 more)

### Community 168 - "write_json"
Cohesion: 0.67
Nodes (3): _canon(), Path, write_json()

### Community 171 - "_box"
Cohesion: 0.17
Nodes (12): _box(), bypass_wall_north_lower(), bypass_wall_south(), guide_left(), guide_right(), South containment, relieved only at the low-y spur-gear face., North containment ends before the orthogonal screw's west cheek., Central lane wall; transverse screw supplies lateral transport. (+4 more)

### Community 172 - "i6_surrogate.py"
Cohesion: 0.13
Nodes (21): bo_search(), build_pareto(), dominates(), evaluate_on_rows(), features(), load_i5_rows(), main(), pareto_front() (+13 more)

### Community 173 - "auger_shaft"
Cohesion: 0.25
Nodes (11): auger_shaft(), _cross_feed_flight(), cross_feed_shaft(), _helix_z(), _path_frame(), Split shaft with a swept, opposite-hand screw and keyed spur., Point and unit tangent at the initial vertex of a swept helix., Single right-hand helicoid with a 3 mm swept flight face. (+3 more)

### Community 178 - "pan_floor"
Cohesion: 0.25
Nodes (8): _c21_transform(), _obstruction_solid(), pan_floor(), Apply the frozen c2_subassembly_transform to a c2 local-frame part., Frozen S2 jacket solids that pierce the chute floor plane: the…, S1 discharge basin with a recessed, supported belt pocket., Landing ledge over the mouth (x 278.5..310, y 255..295); cut where the frozen…, trough_floor()

### Community 179 - "_feed_gear"
Cohesion: 0.25
Nodes (8): cross_feed_gear(), cross_feed_idler(), _feed_gear(), pdl_feed_gear(), Six-mm, 12T involute spur face, keyed on its +X bore flank., 12T keyed output gear sharing the existing PDL shaft., 12T integral intermediate wheel on its own two supported journals., Equal 12T keyed output wheel; two external meshes restore PDL sign.

### Community 184 - "REFERENCE/UNRATED worm, wheel, shafts, bearings and motor"
Cohesion: 0.67
Nodes (3): Keyed PDL, auger, S2 and jackshaft torque paths, REFERENCE/UNRATED worm, wheel, shafts, bearings and motor, Single 15T/40T helical mesh

### Community 192 - "worm_sleeve"
Cohesion: 0.33
Nodes (6): auger_wheel(), _helix_about_y(), Right-hand helix advancing along +Y with a specified bottom phase., PDL_WORM: right-hand two-start swept threads keyed to the shaft., Sector gear at the auger end, generated against the actual worm. The swept worm…, worm_sleeve()

## Knowledge Gaps
- **219 isolated node(s):** `$schema`, `coordinate_units`, `date`, `included_severities`, `kicad_version` (+214 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 803 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **86 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `S2` connect `S2` to `c2/src/build_cad.py`, `engineering.py`, `run_study.py`, `run_full`, `c2.1/src/build_cad.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `run_one_phase()` connect `run_one_phase` to `json`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `Transmission` connect `Transmission` to `build_machine_integration.py`, `c2.1/src/build_cad.py`, `json`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `$schema`, `coordinate_units`, `date` to the rest of the system?**
  _219 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Transmission` be split into smaller, more focused modules?**
  _Cohesion score 0.11948790896159317 - nodes in this community are weakly interconnected._
- **Should `chute.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10507246376811594 - nodes in this community are weakly interconnected._
- **Should `S2` be split into smaller, more focused modules?**
  _Cohesion score 0.1350806451612903 - nodes in this community are weakly interconnected._