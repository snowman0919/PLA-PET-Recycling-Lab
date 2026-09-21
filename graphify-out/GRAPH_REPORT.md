# Graph Report - PPR-c2.1-codex-20260921  (2026-09-21)

## Corpus Check
- 29 files · ~156,283 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 500 nodes · 835 edges · 38 communities (26 shown, 12 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 119 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- C2 CAD and Thermal
- C1 Engineering CAD
- Thermal Control Logic
- Transmission Kinematics
- Firmware Controller Core
- Cost and Evidence
- C2.1 Transmission CAD
- Evidence Contract Tests
- C2 Verification Pipeline
- Performance Research
- Transmission Schematic
- P6 Closure and Safety
- KiCad ERC Evidence
- Thermal Safety Design
- Dimensioned Drawings
- Machine Integration
- C1 Machine Visualization
- Wiring Generator
- C1 CAD Backend
- Cycloid Design Rationale
- System BOM
- Coupon Finite Elements
- Release Manifest
- C2 Research Evidence
- C2 Baseline Boundaries
- Native FreeCAD Assembly
- P6 Artifact Verification
- Firmware Build Evidence
- Runtime Dependencies
- CAD Rendering
- C1 Contract Gates
- STEP Validation
- Pre-Push Gate
- Material Calibration
- Motor RFQ
- DEM Job Queue
- C2 Dependencies
- Performance Blocker

## God Nodes (most connected - your core abstractions)
1. `S2` - 29 edges
2. `Transmission` - 23 edges
3. `Inputs` - 20 edges
4. `GeometryTests` - 19 edges
5. `Thermal` - 19 edges
6. `ControllerTests` - 19 edges
7. `EvidenceTests` - 19 edges
8. `DesignContracts` - 16 edges
9. `thermal_run()` - 15 edges
10. `TransmissionContracts` - 13 edges

## Surprising Connections (you probably didn't know these)
- `S2 Cycloidal Guide, Sleeve, and Pin Rings` --semantically_similar_to--> `Small Pin-Ring Feasibility Screen`  [INFERRED] [semantically similar]
  drawings/PPR_C1_dimensioned_review.pdf → c2/docs/C2_ENGINEERING_NOTES.md
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `Safety-Preserving Cost Reduction Order` --semantically_similar_to--> `Evidence and Safety Boundaries`  [INFERRED] [semantically similar]
  c2/docs/CALIBRATION_AND_RFQ.md → AGENTS.md
- `Nominal Drawing Fabrication Hold` --semantically_similar_to--> `Open Physical Actions Register`  [INFERRED] [semantically similar]
  c2.1/drawings/PPR_C2_1_P6_nominal_plate_review.pdf → c2.1/docs/OPEN_ACTIONS_KO.md
- `Electrical Fabrication and Energization Hold` --semantically_similar_to--> `Open Physical Actions Register`  [INFERRED] [semantically similar]
  c2.1/electrical/PPR_C2_1_machine_wiring.pdf → c2.1/docs/OPEN_ACTIONS_KO.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **C1 RFQ-Only Dimensioned Drawing Set** — drawings_ppr_c1_dimensioned_review_drive_and_bearing_plates, drawings_ppr_c1_dimensioned_review_s1_cutter_system, drawings_ppr_c1_dimensioned_review_s2_cycloidal_components, drawings_ppr_c1_dimensioned_review_interface_and_fit_schedules [EXTRACTED 1.00]
- **C2 and C2.1 Numerical Evidence CI Pipeline** — _github_workflows_c2_engineering_c2_numerical_study_step, _github_workflows_c2_engineering_c2_unit_tests_step, _github_workflows_c2_engineering_gp_performance_training_step, _github_workflows_c2_engineering_mlp_performance_training_step, _github_workflows_c2_engineering_c2_artifact_verification_step, _github_workflows_c2_engineering_c2_1_transmission_step, _github_workflows_c2_engineering_c2_1_unit_tests_step, _github_workflows_c2_engineering_c2_1_artifact_verification_step [EXTRACTED 1.00]
- **C2 P5 Thermal and Control Evidence** — c2_docs_c2_engineering_notes_s2_thermal_development_module, c2_docs_c2_engineering_notes_five_node_thermal_circuit, c2_docs_c2_engineering_notes_cad_derived_heat_capacity_bounds, c2_docs_c2_engineering_notes_cooling_fault_sensitivity, c2_docs_c2_engineering_notes_fail_closed_control_reference, c2_docs_c2_engineering_notes_independent_hardware_safety_chain, c2_docs_c2_engineering_notes_p5_digital_thermal_control_boundary [EXTRACTED 1.00]
- **C2 Performance Evidence Gate** — c2_docs_c2_engineering_notes_performance_job_manifest, c2_docs_c2_engineering_notes_qualified_performance_learning_pipeline, c2_docs_c2_engineering_notes_blocked_performance_data, c2_docs_c2_engineering_notes_material_calibration_plan [EXTRACTED 1.00]
- **C2 S2 Geometry Decision Flow** — c2_docs_c2_engineering_notes_s2_parameter_search, c2_docs_c2_engineering_notes_geometry_assembly_screen, c2_docs_c2_engineering_notes_small_pin_ring_feasibility, c2_docs_c2_engineering_notes_split_dual_path_alternative [EXTRACTED 1.00]
- **Digital Evidence Without External Hardware Release** — _github_workflows_c2_engineering_no_hardware_approval_gate, _github_workflows_c2_engineering_dynamic_evidence_count_contract, _github_workflows_c2_engineering_procurement_fabrication_energization_hold_contract [INFERRED 0.95]

## Communities (38 total, 12 thin omitted)

### Community 0 - "C2 CAD and Thermal"
Cohesion: 0.09
Nodes (31): Any, box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector() (+23 more)

### Community 1 - "C1 Engineering CAD"
Cohesion: 0.06
Nodes (27): allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is…, Euler-Bernoulli beam with free rotation/simple-support translations; SI…, shaft_beam(), box() (+19 more)

### Community 2 - "Thermal Control Logic"
Cohesion: 0.09
Nodes (14): allocate_power(), Controller, Fail-closed control reference. NOT deployable motor/heater firmware., Carry thermal state through batch/fan-fault segments; still uncalibrated., Lower-bound heat capacities from generated C2 metal volumes, not measured…, Thermal, thermal_capacities_from_cad(), thermal_duty_run() (+6 more)

### Community 3 - "Transmission Kinematics"
Cohesion: 0.11
Nodes (27): cad_positive_y_rotation_xz(), cad_y_degrees_for_xz(), coupling(), external_mesh_sign(), ideal_virtual_work(), loaded_contact_sweep(), loaded_contact_takeup(), main() (+19 more)

### Community 4 - "Firmware Controller Core"
Cohesion: 0.07
Nodes (35): array, Controller, latched_, limits_, Inputs, buffer_full, estop_closed, fan_required (+27 more)

### Community 5 - "Cost and Evidence"
Cohesion: 0.11
Nodes (27): evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., candidate_hashes(), canonical_sha256(), evidence_inventory(), EvidenceError, main() (+19 more)

### Community 6 - "C2.1 Transmission CAD"
Cohesion: 0.17
Nodes (28): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+20 more)

### Community 8 - "C2 Verification Pipeline"
Cohesion: 0.11
Nodes (18): Run C2.1 Artifact Verification, Run C2.1 Transmission Analysis, Run C2.1 Unit Tests, Run C2 Artifact Verification, C2 Engineering Contracts, Run C2 Numerical Study, Run C2 Unit Tests, Actual Run Counts Must Equal Dynamic Evidence Inventory Counts (+10 more)

### Community 9 - "Performance Research"
Cohesion: 0.12
Nodes (17): BLOCKED_PERFORMANCE_DATA, C1-SEED Comparison Point, Coupled Kinematic Work Model, Eccentric Sleeve Wall Constraint, Geometry and Assembly Screen, PLA PET and TPU Calibration Plan, 144-Job Performance Manifest, Qualified GP and MLP Performance Learning Pipeline (+9 more)

### Community 10 - "Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 11 - "P6 Closure and Safety"
Cohesion: 0.17
Nodes (12): C2.1 Digital Assembly Service and Test Package, Lockout and Staged Physical Test, DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD, P6 Full Machine Digital Integration, Remaining Rating and Performance Holds, Motor Floor Exceeds System Soft Budget, Open Physical Actions Register, C2.1 P0-P6 Integration Plan (+4 more)

### Community 12 - "KiCad ERC Evidence"
Cohesion: 0.18
Nodes (10): coordinate_units, date, included_severities, kicad_version, $schema, sheets, source, error (+2 more)

### Community 13 - "Thermal Safety Design"
Cohesion: 0.25
Nodes (11): CAD-Derived Heat-Capacity Lower Bounds, Clean-Air Cooling Path, Clean Filter, Clogged Filter, and Fan-Failure Sensitivity, Fail-Closed Thermal and Jam Control Reference, Five-Node Chamber and Drivetrain Thermal Circuit, Fixed-Shear Sensor Path, Independent Hardware Safety Chain, P5 Digital Thermal and Control Boundary (+3 more)

### Community 14 - "Dimensioned Drawings"
Cohesion: 0.40
Nodes (10): dim(), drawshape(), header(), hole_table(), main(), paragraph(), Nominal dimensioned RFQ drawings from the same CSG master; not NC toolpaths., section() (+2 more)

### Community 15 - "Machine Integration"
Cohesion: 0.36
Nodes (9): bbox_overlap(), bounds(), c21_parts(), collision_audit(), extent(), legacy_parts(), main(), normalize_step_timestamp() (+1 more)

### Community 16 - "C1 Machine Visualization"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 17 - "Wiring Generator"
Cohesion: 0.43
Nodes (5): connector_symbol(), main(), Generate the review-only KiCad machine wiring schematic and pin/net ledger., uid(), write_schematic()

### Community 18 - "C1 CAD Backend"
Cohesion: 0.48
Nodes (6): bbox(), build(), main(), primitive(), CadQuery/OCP verification backend for the shared constructive-solid master. The…, wire3()

### Community 19 - "Cycloid Design Rationale"
Cohesion: 0.33
Nodes (6): Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative, Torque and Reaction Path, Unverified Rating and Fabrication Limits

### Community 20 - "System BOM"
Cohesion: 0.53
Nodes (5): column_name(), main(), Build the active C2.1 system BOM without mutating the historical C1 BOM., rows(), write_xlsx()

### Community 21 - "Coupon Finite Elements"
Cohesion: 0.47
Nodes (5): deck(), main(), Path, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., reaction_force()

### Community 22 - "Release Manifest"
Cohesion: 0.60
Nodes (4): load(), main(), Build deterministic P0-P6 status and artifact manifests., sha256()

### Community 23 - "C2 Research Evidence"
Cohesion: 0.40
Nodes (5): PPR C2 Engineering Baseline, 136-Row Cost Review Ledger, Fixed C2 System Constraints, JSS57BLY Motor Candidate Evidence, Shared-Motor Load Envelope

### Community 24 - "C2 Baseline Boundaries"
Cohesion: 0.50
Nodes (4): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Safety-Preserving Cost Reduction Order

### Community 25 - "Native FreeCAD Assembly"
Cohesion: 0.67
Nodes (3): main(), Create the native FreeCAD C2.1 machine assembly from checked STEP parts., read_shape()

### Community 28 - "Runtime Dependencies"
Cohesion: 0.67
Nodes (3): C2.1 Active Digital Iteration, Base Runtime and CAD Dependencies, MLP Dependency Layer

## Knowledge Gaps
- **77 isolated node(s):** `Fixed q+1 Ring Pins and Reaction`, `Front Input Support`, `M1 Input Shaft +ω`, `Rear Output Support`, `Rotor Motion: Orbit e and Self-Rotation −ω/q` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `C2 CAD and Thermal` to `C1 Engineering CAD`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `add()` connect `C1 Engineering CAD` to `C2 CAD and Thermal`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `S2` connect `C2 CAD and Thermal` to `Thermal Control Logic`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `S2` (e.g. with `verify()` and `GeometryTests`) actually correct?**
  _`S2` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Transmission` (e.g. with `TransmissionContracts` and `.test_cad_xz_sign_and_quarter_orbit()`) actually correct?**
  _`Transmission` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Thermal` (e.g. with `ThermalTests` and `.test_bulk_can_be_hotter_than_wall()`) actually correct?**
  _`Thermal` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Fixed q+1 Ring Pins and Reaction`, `Front Input Support`, `M1 Input Shaft +ω` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._