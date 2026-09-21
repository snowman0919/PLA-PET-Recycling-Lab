# Graph Report - PPR-c2.1-codex-20260921  (2026-09-21)

## Corpus Check
- 19 files · ~112,855 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 432 nodes · 773 edges · 29 communities (18 shown, 11 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 127 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- c2.1/src/build_cad.py
- S2
- C2.1 Integration Sequence P0-P6
- design.py
- performance.py
- DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD
- Thermal
- ControllerTests
- EvidenceTests
- PPR C1 Dimensioned Engineering Review
- C2.1 S2 Transmission Schematic
- DesignContracts
- Fail-Closed Thermal and Jam Control
- make_drawings.py
- c2/src/build_cad.py
- PPR C1 CAD Inspection Image
- src/build_cad.py
- run_coupon_fe.py
- Fixed C2 System Constraints
- Active C2 Baseline
- render_cad.py
- c2.1/src/verify_artifacts.py
- validate_step.py
- pre_push.py
- Material Calibration Evidence
- Motor and Driver RFQ Evidence
- Unsubmitted DEM Job Queue
- C2 Research and CAD Dependencies
- BLOCKED_PERFORMANCE_DATA

## God Nodes (most connected - your core abstractions)
1. `S2` - 31 edges
2. `Transmission` - 26 edges
3. `Thermal` - 19 edges
4. `GeometryTests` - 19 edges
5. `ControllerTests` - 19 edges
6. `EvidenceTests` - 19 edges
7. `DesignContracts` - 16 edges
8. `C2.1 Integration Sequence P0-P6` - 16 edges
9. `thermal_run()` - 15 edges
10. `DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD` - 15 edges

## Surprising Connections (you probably didn't know these)
- `S2 Cycloidal Guide, Sleeve, and Pin Rings` --semantically_similar_to--> `Small Pin-Ring Feasibility Screen`  [INFERRED] [semantically similar]
  drawings/PPR_C1_dimensioned_review.pdf → c2/docs/C2_ENGINEERING_NOTES.md
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `C1 Physical Gate Separation` --semantically_similar_to--> `Purchase Outsourcing Energization Machining and Main Merge Require Separate User Approval`  [INFERRED] [semantically similar]
  .github/workflows/c1-digital.yml → c2.1/docs/PLAN_KO.md
- `Safety-Preserving Cost Reduction Order` --semantically_similar_to--> `Evidence and Safety Boundaries`  [INFERRED] [semantically similar]
  c2/docs/CALIBRATION_AND_RFQ.md → AGENTS.md
- `P5 Digital Sensitivity Complete and Physical Qualification HOLD` --semantically_similar_to--> `P5 Physical Thermal Test Fan Curve Firmware and Energization HOLD`  [INFERRED] [semantically similar]
  .github/workflows/c2-engineering.yml → c2.1/docs/PLAN_KO.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **C1 RFQ-Only Dimensioned Drawing Set** — drawings_ppr_c1_dimensioned_review_drive_and_bearing_plates, drawings_ppr_c1_dimensioned_review_s1_cutter_system, drawings_ppr_c1_dimensioned_review_s2_cycloidal_components, drawings_ppr_c1_dimensioned_review_interface_and_fit_schedules [EXTRACTED 1.00]
- **C2.1 P0-P6 Progress State** — c2_1_docs_plan_ko_p0_evidence_verifier_complete, c2_1_docs_plan_ko_p1_rigid_first_contact_equilibrium_complete, c2_1_docs_plan_ko_p2_cutting_cooling_integration_complete, c2_1_docs_plan_ko_p3_m1_candidate_search_in_progress, c2_1_docs_plan_ko_p4_calculix_coupon_runs_complete, c2_1_docs_plan_ko_p5_digital_thermal_control_complete, c2_1_docs_plan_ko_p6_full_machine_reintegration_in_progress [EXTRACTED 1.00]
- **C2 and C2.1 Numerical Evidence CI Pipeline** — _github_workflows_c2_engineering_c2_numerical_study_step, _github_workflows_c2_engineering_c2_unit_tests_step, _github_workflows_c2_engineering_gp_performance_training_step, _github_workflows_c2_engineering_mlp_performance_training_step, _github_workflows_c2_engineering_c2_artifact_verification_step, _github_workflows_c2_engineering_c2_1_transmission_step, _github_workflows_c2_engineering_c2_1_unit_tests_step, _github_workflows_c2_engineering_c2_1_artifact_verification_step [EXTRACTED 1.00]
- **C2 P5 Thermal and Control Evidence** — c2_docs_c2_engineering_notes_s2_thermal_development_module, c2_docs_c2_engineering_notes_five_node_thermal_circuit, c2_docs_c2_engineering_notes_cad_derived_heat_capacity_bounds, c2_docs_c2_engineering_notes_cooling_fault_sensitivity, c2_docs_c2_engineering_notes_fail_closed_control_reference, c2_docs_c2_engineering_notes_independent_hardware_safety_chain, c2_docs_c2_engineering_notes_p5_digital_thermal_control_boundary [EXTRACTED 1.00]
- **C2 Performance Evidence Gate** — c2_docs_c2_engineering_notes_performance_job_manifest, c2_docs_c2_engineering_notes_qualified_performance_learning_pipeline, c2_docs_c2_engineering_notes_blocked_performance_data, c2_docs_c2_engineering_notes_material_calibration_plan [EXTRACTED 1.00]
- **C2 S2 Geometry Decision Flow** — c2_docs_c2_engineering_notes_s2_parameter_search, c2_docs_c2_engineering_notes_geometry_assembly_screen, c2_docs_c2_engineering_notes_small_pin_ring_feasibility, c2_docs_c2_engineering_notes_split_dual_path_alternative [EXTRACTED 1.00]
- **Digital Evidence Without External Hardware Release** — c2_1_docs_plan_ko_external_action_hold, _github_workflows_c2_engineering_no_hardware_approval_gate, _github_workflows_c2_engineering_dynamic_evidence_count_contract, _github_workflows_c2_engineering_procurement_fabrication_energization_hold_contract [INFERRED 0.95]

## Communities (29 total, 11 thin omitted)

### Community 0 - "c2.1/src/build_cad.py"
Cohesion: 0.08
Nodes (48): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+40 more)

### Community 1 - "S2"
Cohesion: 0.11
Nodes (20): Any, design_set(), diverse_selection(), equivalent_motor_load(), generalized_torque(), hook_polygon(), kinematics(), main() (+12 more)

### Community 2 - "C2.1 Integration Sequence P0-P6"
Cohesion: 0.07
Nodes (36): C1 Digital Contracts, C1 Physical Gate Separation, Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, C2 Engineering Contracts, Run C2 Numerical Study (+28 more)

### Community 3 - "design.py"
Cohesion: 0.10
Nodes (26): allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is…, Euler-Bernoulli beam with free rotation/simple-support translations; SI…, shaft_beam(), box() (+18 more)

### Community 4 - "performance.py"
Cohesion: 0.10
Nodes (29): evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., Path, write_json(), candidate_hashes(), canonical_sha256(), evidence_inventory() (+21 more)

### Community 5 - "DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD"
Cohesion: 0.08
Nodes (32): Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative, Torque and Reaction Path, Unverified Rating and Fabrication Limits, BLOCKED_PERFORMANCE_DATA, C2 Generated Part Integration (+24 more)

### Community 6 - "Thermal"
Cohesion: 0.21
Nodes (10): Carry thermal state through batch/fan-fault segments; still uncalibrated., Lower-bound heat capacities from generated C2 metal volumes, not measured…, Thermal, thermal_capacities_from_cad(), thermal_duty_run(), thermal_matrix(), thermal_run(), main() (+2 more)

### Community 7 - "ControllerTests"
Cohesion: 0.16
Nodes (4): allocate_power(), Controller, Fail-closed control reference. NOT deployable motor/heater firmware., ControllerTests

### Community 9 - "PPR C1 Dimensioned Engineering Review"
Cohesion: 0.12
Nodes (17): BLOCKED_PERFORMANCE_DATA, C1-SEED Comparison Point, Coupled Kinematic Work Model, Eccentric Sleeve Wall Constraint, Geometry and Assembly Screen, PLA PET and TPU Calibration Plan, 144-Job Performance Manifest, Qualified GP and MLP Performance Learning Pipeline (+9 more)

### Community 10 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 12 - "Fail-Closed Thermal and Jam Control"
Cohesion: 0.25
Nodes (11): CAD-Derived Heat-Capacity Lower Bounds, Clean-Air Cooling Path, Clean Filter, Clogged Filter, and Fan-Failure Sensitivity, Fail-Closed Thermal and Jam Control Reference, Five-Node Chamber and Drivetrain Thermal Circuit, Fixed-Shear Sensor Path, Independent Hardware Safety Chain, P5 Digital Thermal and Control Boundary (+3 more)

### Community 13 - "make_drawings.py"
Cohesion: 0.40
Nodes (10): dim(), drawshape(), header(), hole_table(), main(), paragraph(), Nominal dimensioned RFQ drawings from the same CSG master; not NC toolpaths., section() (+2 more)

### Community 14 - "c2/src/build_cad.py"
Cohesion: 0.44
Nodes (9): box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector(), wire() (+1 more)

### Community 15 - "PPR C1 CAD Inspection Image"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 16 - "src/build_cad.py"
Cohesion: 0.48
Nodes (6): bbox(), build(), main(), primitive(), CadQuery/OCP verification backend for the shared constructive-solid master. The…, wire3()

### Community 17 - "run_coupon_fe.py"
Cohesion: 0.47
Nodes (5): deck(), main(), Path, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., reaction_force()

### Community 18 - "Fixed C2 System Constraints"
Cohesion: 0.40
Nodes (5): PPR C2 Engineering Baseline, 136-Row Cost Review Ledger, Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope

### Community 19 - "Active C2 Baseline"
Cohesion: 0.50
Nodes (4): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Safety-Preserving Cost Reduction Order

## Knowledge Gaps
- **45 isolated node(s):** `C1 Digital Contracts`, `Split Dual-Path Alternative`, `Torque and Reaction Path`, `Material Calibration Evidence`, `Unsubmitted DEM Job Queue` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `c2/src/build_cad.py` to `S2`, `design.py`, `performance.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `add()` connect `design.py` to `c2/src/build_cad.py`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `S2` connect `S2` to `c2.1/src/build_cad.py`, `c2/src/build_cad.py`, `Thermal`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `S2` (e.g. with `local_rotor()` and `main()`) actually correct?**
  _`S2` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Transmission` (e.g. with `TransmissionContracts` and `.test_cad_xz_sign_and_quarter_orbit()`) actually correct?**
  _`Transmission` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Thermal` (e.g. with `ThermalTests` and `.test_bulk_can_be_hotter_than_wall()`) actually correct?**
  _`Thermal` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `C1 Digital Contracts`, `Split Dual-Path Alternative`, `Torque and Reaction Path` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._