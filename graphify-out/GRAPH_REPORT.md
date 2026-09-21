# Graph Report - PPR-c2.1-codex-20260921  (2026-09-21)

## Corpus Check
- 1 files · ~105,948 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 395 nodes · 643 edges · 33 communities (18 shown, 15 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 79 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- S2 Transmission Mechanics
- C2.1 Integration Decisions
- C2 Engineering Pipeline
- Design Analysis Utilities
- Evidence Validation Logic
- Evidence and Cost Tests
- C2.1 CAD Assembly
- C2 Geometry Tests
- C1 Design Contracts
- Transmission Schematic
- Fail-Closed Controller Tests
- C2 CAD Generation
- Actuation and Forming
- Dimensioned Drawing Generator
- C1 S2 Review Package
- C2 Thermal Tests
- Controller IO Map
- C1 CAD Inspection
- CAD Primitive Builders
- C2 Constraints and Safety
- Budget and Procurement
- CalculiX Coupon Solver
- CAD Rendering Evidence
- C2.1 Artifact Verification
- Thermal Control Model
- STEP Topology Validation
- C1 Pre-Push Gate
- Actuation Tach Package
- Cooling Feedback Assembly
- Thermal Protection System
- Mandatory Safety Parts
- Extruder Load Path
- Cooling Fault Scenarios

## God Nodes (most connected - your core abstractions)
1. `Transmission` - 23 edges
2. `EvidenceTests` - 19 edges
3. `GeometryTests` - 18 edges
4. `S2` - 16 edges
5. `DesignContracts` - 16 edges
6. `TransmissionContracts` - 13 edges
7. `ControllerTests` - 13 edges
8. `main()` - 12 edges
9. `C2.1 S2 Transmission Schematic` - 12 edges
10. `main()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `S2 Cycloidal Guide, Sleeve, and Pin Rings` --semantically_similar_to--> `Small Pin-Ring Feasibility Screen`  [INFERRED] [semantically similar]
  drawings/PPR_C1_dimensioned_review.pdf → c2/docs/C2_ENGINEERING_NOTES.md
- `Frozen C1 Baseline` --conceptually_related_to--> `PPR C1 Dimensioned Engineering Review Package`  [INFERRED]
  README.md → drawings/PPR_C1_dimensioned_review.pdf
- `C1 Physical Gate Separation` --semantically_similar_to--> `External Action Hold Boundary`  [INFERRED] [semantically similar]
  .github/workflows/c1-digital.yml → c2.1/docs/PLAN_KO.md
- `C2 No-Hardware-Approval Gate` --semantically_similar_to--> `External Action Hold Boundary`  [INFERRED] [semantically similar]
  .github/workflows/c2-engineering.yml → c2.1/docs/PLAN_KO.md
- `Safety-Preserving Cost Reduction Order` --semantically_similar_to--> `Evidence and Safety Boundaries`  [INFERRED] [semantically similar]
  c2/docs/CALIBRATION_AND_RFQ.md → AGENTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **C1 RFQ-Only Dimensioned Drawing Set** — drawings_ppr_c1_dimensioned_review_drive_and_bearing_plates, drawings_ppr_c1_dimensioned_review_s1_cutter_system, drawings_ppr_c1_dimensioned_review_s2_cycloidal_components, drawings_ppr_c1_dimensioned_review_interface_and_fit_schedules [EXTRACTED 1.00]
- **C2.1 Integrated Digital Evidence** — c2_1_docs_handoff_ko_p0_evidence_verifier, c2_1_docs_handoff_ko_rigid_first_contact_equilibrium, c2_1_docs_handoff_ko_c2_generated_part_integration, c2_1_docs_handoff_ko_collision_verification, c2_1_docs_handoff_ko_calculix_coupon_runs [EXTRACTED 1.00]
- **C2.1 Remaining Rating Performance and Release Holds** — c2_1_docs_handoff_ko_unverified_mechanical_rating, c2_1_docs_handoff_ko_blocked_performance_data, c2_1_docs_handoff_ko_motor_and_cost_hold, c2_1_docs_handoff_ko_external_action_hold [EXTRACTED 1.00]
- **Digital Evidence Without Hardware Release** — _github_workflows_c1_digital_physical_gate_separation, _github_workflows_c2_engineering_no_hardware_approval_gate, c2_1_docs_adr_001_s2_transmission_unverified_rating_limits, c2_1_docs_handoff_ko_digital_integration_pass_rating_and_performance_hold, c2_1_docs_plan_ko_external_action_hold [INFERRED 0.95]

## Communities (33 total, 15 thin omitted)

### Community 0 - "S2 Transmission Mechanics"
Cohesion: 0.11
Nodes (27): cad_positive_y_rotation_xz(), cad_y_degrees_for_xz(), coupling(), external_mesh_sign(), ideal_virtual_work(), loaded_contact_sweep(), loaded_contact_takeup(), main() (+19 more)

### Community 1 - "C2.1 Integration Decisions"
Cohesion: 0.07
Nodes (36): C1 Digital Contracts, C1 Physical Gate Separation, C2 Engineering Contracts, C2 No-Hardware-Approval Gate, Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative (+28 more)

### Community 2 - "C2 Engineering Pipeline"
Cohesion: 0.14
Nodes (28): Any, allocate_power(), Controller, Fail-closed control reference. NOT deployable motor/heater firmware., design_set(), diverse_selection(), equivalent_motor_load(), generalized_torque() (+20 more)

### Community 3 - "Design Analysis Utilities"
Cohesion: 0.10
Nodes (26): allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is…, Euler-Bernoulli beam with free rotation/simple-support translations; SI…, shaft_beam(), box() (+18 more)

### Community 4 - "Evidence Validation Logic"
Cohesion: 0.12
Nodes (24): candidate_hashes(), canonical_sha256(), evidence_inventory(), EvidenceError, main(), nondominated(), ndarray, Path (+16 more)

### Community 5 - "Evidence and Cost Tests"
Cohesion: 0.13
Nodes (4): evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., EvidenceTests

### Community 6 - "C2.1 CAD Assembly"
Cohesion: 0.24
Nodes (21): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+13 more)

### Community 9 - "Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 11 - "C2 CAD Generation"
Cohesion: 0.40
Nodes (10): box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector(), wire() (+2 more)

### Community 12 - "Actuation and Forming"
Cohesion: 0.18
Nodes (11): Forming Requalification Scenarios, Heater Allocator Scenarios, Puller Fault Scenarios, Screw and Purge Scenarios, Spool and Traverse Scenarios, V062ShadowScenarios, ActuationShadowSystem, Forming Fault Cascade (+3 more)

### Community 13 - "Dimensioned Drawing Generator"
Cohesion: 0.40
Nodes (10): dim(), drawshape(), header(), hole_table(), main(), paragraph(), Nominal dimensioned RFQ drawings from the same CSG master; not NC toolpaths., section() (+2 more)

### Community 14 - "C1 S2 Review Package"
Cohesion: 0.25
Nodes (9): C2 Engineering Baseline, S2 Parameter Search, Small Pin-Ring Feasibility Screen, PPR C1 Dimensioned Engineering Review Package, Drive and Bearing Plate Drawings, Shaft, Screen, Phase, and Fit Schedules, S1 Cutter System Drawings, S2 Cycloidal Guide, Sleeve, and Pin Rings (+1 more)

### Community 16 - "Controller IO Map"
Cohesion: 0.28
Nodes (9): Cooling Feedback Signals, Controller IO Schedule, Motion Feedback Signals, De-Energized Safe Outputs, Fail-Safe Safety Inputs, No Timer Conflicts, Runtime Resource Constraints, Tach Interrupt Map (+1 more)

### Community 17 - "C1 CAD Inspection"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 18 - "CAD Primitive Builders"
Cohesion: 0.48
Nodes (6): bbox(), build(), main(), primitive(), CadQuery/OCP verification backend for the shared constructive-solid master. The…, wire3()

### Community 19 - "C2 Constraints and Safety"
Cohesion: 0.33
Nodes (6): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Motor Selection Evaluation, Safety-Preserving Cost Reduction Order, Motor and Driver RFQ Evidence

### Community 20 - "Budget and Procurement"
Cohesion: 0.33
Nodes (6): Absolute Cash Cap With Reserve, Blocked Procurement Allowances, Conditional Cash Target, Conditional Planning Budget, Optional Empirical Validation Cost, Verified Procurement Not Established

### Community 21 - "CalculiX Coupon Solver"
Cohesion: 0.47
Nodes (5): deck(), main(), Path, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., reaction_force()

## Knowledge Gaps
- **38 isolated node(s):** `V062ShadowScenarios`, `Heater Allocator Scenarios`, `Puller Fault Scenarios`, `Screw and Purge Scenarios`, `Spool and Traverse Scenarios` (+33 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `C2 CAD Generation` to `C2 Engineering Pipeline`, `Design Analysis Utilities`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `add()` connect `Design Analysis Utilities` to `C2 CAD Generation`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Why does `GeometryTests` connect `C2 Geometry Tests` to `C2 Engineering Pipeline`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Transmission` (e.g. with `TransmissionContracts` and `.test_cad_xz_sign_and_quarter_orbit()`) actually correct?**
  _`Transmission` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `ValueError` (e.g. with `external_mesh_sign()` and `ideal_virtual_work()`) actually correct?**
  _`ValueError` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `V062ShadowScenarios`, `Heater Allocator Scenarios`, `Puller Fault Scenarios` to the rest of the system?**
  _38 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `S2 Transmission Mechanics` be split into smaller, more focused modules?**
  _Cohesion score 0.11033681765389082 - nodes in this community are weakly interconnected._