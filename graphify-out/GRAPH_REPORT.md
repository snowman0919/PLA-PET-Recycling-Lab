# Graph Report - PPR-c2.1-codex-20260921  (2026-09-21)

## Corpus Check
- 78 files · ~105,949 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 363 nodes · 712 edges · 22 communities (16 shown, 6 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 142 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ee5d9688`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Transmission
- DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD
- S2
- design.py
- ValueError
- EvidenceTests
- c2.1/src/build_cad.py
- DesignContracts
- C2.1 S2 Transmission Schematic
- ControllerTests
- c2/src/build_cad.py
- make_drawings.py
- PPR C1 Dimensioned Engineering Review Package
- run_study.py
- PPR C1 CAD Inspection Image
- Active C2 Baseline
- run_coupon_fe.py
- render_cad.py
- c2.1/src/verify_artifacts.py
- Fail-Closed Control Reference
- validate_step.py
- pre_push.py

## God Nodes (most connected - your core abstractions)
1. `S2` - 31 edges
2. `Transmission` - 26 edges
3. `EvidenceTests` - 20 edges
4. `GeometryTests` - 19 edges
5. `Thermal` - 16 edges
6. `DesignContracts` - 16 edges
7. `thermal_run()` - 14 edges
8. `ControllerTests` - 14 edges
9. `TransmissionContracts` - 13 edges
10. `validate_record()` - 13 edges

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

## Communities (22 total, 6 thin omitted)

### Community 0 - "Transmission"
Cohesion: 0.12
Nodes (23): cad_positive_y_rotation_xz(), coupling(), external_mesh_sign(), ideal_virtual_work(), loaded_contact_sweep(), loaded_contact_takeup(), main(), ndarray (+15 more)

### Community 1 - "DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD"
Cohesion: 0.07
Nodes (36): C1 Digital Contracts, C1 Physical Gate Separation, C2 Engineering Contracts, C2 No-Hardware-Approval Gate, Fixed-Ring Cycloid Selection Rationale, Pin-Window Offset Coupling, Single-Input Reverse-Output S2 Drivetrain, Split Dual-Path Alternative (+28 more)

### Community 2 - "S2"
Cohesion: 0.12
Nodes (19): Any, design_set(), diverse_selection(), equivalent_motor_load(), generalized_torque(), hook_polygon(), kinematics(), main() (+11 more)

### Community 3 - "design.py"
Cohesion: 0.10
Nodes (26): allocate(), clearance_metric(), cooling(), main(), Reproducible C1 engineering screens. No empirical cutting/thermal data is…, Euler-Bernoulli beam with free rotation/simple-support translations; SI…, shaft_beam(), box() (+18 more)

### Community 4 - "ValueError"
Cohesion: 0.13
Nodes (17): fit_gp(), fit_mlp(), grouped_split(), main(), Material-specific GP or deep-ensemble training on verified S2 PERFORMANCE only.…, bbox(), build(), main() (+9 more)

### Community 5 - "EvidenceTests"
Cohesion: 0.12
Nodes (14): candidate_hashes(), canonical_sha256(), evidence_inventory(), EvidenceError, main(), nondominated(), ndarray, Path (+6 more)

### Community 6 - "c2.1/src/build_cad.py"
Cohesion: 0.20
Nodes (25): analytical_bounds(), c2_process_part(), cad_frame_check(), collision_checks(), components(), cylinder(), export_assembly(), extrude_xz() (+17 more)

### Community 9 - "C2.1 S2 Transmission Schematic"
Cohesion: 0.15
Nodes (15): F0 Coordinate Frame: +X Right, +Y Shaft Axis, +Z Up, C2.1 S2 Transmission Schematic, Elastic Sharing, Ratings, and Fabrication HOLD, Fixed q+1 Ring Pins and Reaction, Front Input Support, M1 Input Shaft +ω, Nominal Window Clearance extra0.20mm, Not a Generated CAD Section (+7 more)

### Community 10 - "ControllerTests"
Cohesion: 0.18
Nodes (4): allocate_power(), Controller, Fail-closed control reference. NOT deployable motor/heater firmware., ControllerTests

### Community 11 - "c2/src/build_cad.py"
Cohesion: 0.32
Nodes (11): box(), cylinder(), from_c1(), main(), primitive(), C2 S2 thermal/fixed-shear development module. Not an assembly release. C1…, sector(), wire() (+3 more)

### Community 13 - "make_drawings.py"
Cohesion: 0.40
Nodes (10): dim(), drawshape(), header(), hole_table(), main(), paragraph(), Nominal dimensioned RFQ drawings from the same CSG master; not NC toolpaths., section() (+2 more)

### Community 14 - "PPR C1 Dimensioned Engineering Review Package"
Cohesion: 0.25
Nodes (9): C2 Engineering Baseline, S2 Parameter Search, Small Pin-Ring Feasibility Screen, PPR C1 Dimensioned Engineering Review Package, Drive and Bearing Plate Drawings, Shaft, Screen, Phase, and Fit Schedules, S1 Cutter System Drawings, S2 Cycloidal Guide, Sleeve, and Pin Rings (+1 more)

### Community 15 - "run_study.py"
Cohesion: 0.23
Nodes (10): evaluate(), main(), Full incremental procurement coverage. A missing quotation is not zero cost., Thermal, thermal_matrix(), thermal_run(), verify(), main() (+2 more)

### Community 17 - "PPR C1 CAD Inspection Image"
Cohesion: 0.36
Nodes (8): BRep Mesh Inspection View, Cutting Mechanism, Drive Components, Filament Spools, Hopper and Lid Hidden for Visibility, PPR C1 CAD Inspection Image, PPR C1, Structural Frame

### Community 19 - "Active C2 Baseline"
Cohesion: 0.33
Nodes (6): Active C2 Baseline, Evidence and Safety Boundaries, Fixed System Constraints, Motor Selection Evaluation, Safety-Preserving Cost Reduction Order, Motor and Driver RFQ Evidence

### Community 21 - "run_coupon_fe.py"
Cohesion: 0.47
Nodes (5): deck(), main(), Path, Run small uncalibrated CalculiX coupon sensitivities; never performance labels., reaction_force()

## Knowledge Gaps
- **23 isolated node(s):** `C1 Digital Contracts`, `Split Dual-Path Alternative`, `Torque and Reaction Path`, `Previous 33-Object Independent Review`, `STEP Reproducibility Contract` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `c2/src/build_cad.py` to `S2`, `design.py`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `add()` connect `design.py` to `c2/src/build_cad.py`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Why does `S2` connect `S2` to `c2/src/build_cad.py`, `ValueError`, `c2.1/src/build_cad.py`, `run_study.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `S2` (e.g. with `local_rotor()` and `main()`) actually correct?**
  _`S2` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Transmission` (e.g. with `TransmissionContracts` and `.test_cad_xz_sign_and_quarter_orbit()`) actually correct?**
  _`Transmission` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `ValueError` (e.g. with `external_mesh_sign()` and `ideal_virtual_work()`) actually correct?**
  _`ValueError` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `C1 Digital Contracts`, `Split Dual-Path Alternative`, `Torque and Reaction Path` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._