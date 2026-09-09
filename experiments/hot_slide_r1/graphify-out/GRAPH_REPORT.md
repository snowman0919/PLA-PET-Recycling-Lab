# HS-R1-S2 scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - hot_slide_r1  (2026-09-09)

## Corpus Check
- 20 files · ~861 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 80 nodes · 142 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `main()` - 9 edges
3. `solve()` - 9 edges
4. `main()` - 7 edges
5. `resultant_loads()` - 6 edges
6. `supports()` - 5 edges
7. `mesh_step()` - 5 edges
8. `read_gmsh_inp()` - 5 edges
9. `rotor_sheet()` - 5 edges
10. `nset()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `resultant_loads()`  [EXTRACTED]
  solve_sliding_gradients.py → distributing_patch_v08.py
- `main()` --calls--> `supports()`  [EXTRACTED]
  solve_sliding_gradients.py → pin_supports.py
- `main()` --calls--> `solve()`  [EXTRACTED]
  solve_sliding_gradients.py → solver_kernel.py
- `main()` --calls--> `resultant_loads()`  [EXTRACTED]
  solve_sliding_kinematic.py → distributing_patch_v08.py
- `main()` --calls--> `mesh_step()`  [EXTRACTED]
  solve_sliding_kinematic.py → quadratic_mesh.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.30
Nodes (10): cyl(), main(), FreeCAD prototype: replace hard radial fit by three elastic shoes. Not an…, rotor_sheet(), carrier(), circle(), export_one(), local_to_station() (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.24
Nodes (7): face-gradient-not-converged, main(), Package a tested prototype snapshot; no fabrication/energization approval., sha(), main(), Bind solver geometry to the separately exported prototype manufacturing body., sha()

### Community 2 - "Community 2"
Cohesion: 0.28
Nodes (6): main(), Contact-compatible linear screen using actual FE shoe compliance matrix. No…, solve_contact(), expand(), main(), Hard-bore relief candidate, usable only with independently centred support.…

### Community 3 - "Community 3"
Cohesion: 0.39
Nodes (7): mesh_step(), Quadratic tetrahedral mesh adapter for the isolated flexure prototype., read_gmsh_inp(), fields(), main(), Finite-element stiffness/strain screening of a radially compliant shoe sheet., nset()

### Community 4 - "Community 4"
Cohesion: 0.36
Nodes (5): Three radial slots: constrain tangent/axial means, leave radial motion free., supports(), fields(), main(), Finite-element stiffness/strain screening of a radially compliant shoe sheet.

### Community 5 - "Community 5"
Cohesion: 0.39
Nodes (6): fixture(), main(), Synthetic validator regression tests; none are physical test evidence., evaluate(), number(), Review pressureless test records; never operates or approves the machine.

### Community 6 - "Community 6"
Cohesion: 0.57
Nodes (6): Path, parse_frd(), Scoped MIT solver adapters copied from PPR; source provenance in manifest., reactions(), run(), solve()

### Community 7 - "Community 7"
Cohesion: 0.60
Nodes (4): cross_matrix(), Work-conjugate weighted rigid-section fit and statically exact surface…, resultant_loads(), rigid_fit_coefficients()

### Community 8 - "Community 8"
Cohesion: 0.60
Nodes (4): main(), page(), projection(), Vector review drawings from the actual STEP edge geometry.

## Knowledge Gaps
- **3 isolated node(s):** `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._