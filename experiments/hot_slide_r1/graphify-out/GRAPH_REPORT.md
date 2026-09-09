# HS-R1-S2 scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - hot_slide_r1  (2026-09-09)

## Corpus Check
- 22 files · ~1,255 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 113 nodes · 232 edges · 18 communities (14 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.95)
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
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15

## God Nodes (most connected - your core abstractions)
1. `BoundaryTests` - 29 edges
2. `fixture()` - 16 edges
3. `main()` - 9 edges
4. `main()` - 9 edges
5. `solve()` - 9 edges
6. `evaluate()` - 8 edges
7. `main()` - 7 edges
8. `resultant_loads()` - 6 edges
9. `supports()` - 5 edges
10. `mesh_step()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `resultant_loads()`  [EXTRACTED]
  solve_sliding_gradients.py → distributing_patch_v08.py
- `main()` --calls--> `mesh_step()`  [EXTRACTED]
  solve_sliding_gradients.py → quadratic_mesh.py
- `main()` --calls--> `read_gmsh_inp()`  [EXTRACTED]
  solve_sliding_gradients.py → quadratic_mesh.py
- `main()` --calls--> `solve()`  [EXTRACTED]
  solve_sliding_gradients.py → solver_kernel.py
- `main()` --calls--> `resultant_loads()`  [EXTRACTED]
  solve_sliding_kinematic.py → distributing_patch_v08.py

## Import Cycles
- None detected.

## Communities (18 total, 4 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.27
Nodes (8): face-gradient-not-converged, Synthetic regression cases for measurement uncertainty and real trace coverage., main(), Synthetic validator regression tests; none are physical test evidence., evaluate(), number(), outcome(), Screen pressureless measurement records; never operate or authorize hardware.

### Community 2 - "Community 2"
Cohesion: 0.30
Nodes (10): cyl(), main(), FreeCAD prototype: replace hard radial fit by three elastic shoes. Not an…, rotor_sheet(), carrier(), circle(), export_one(), local_to_station() (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (6): Three radial slots: constrain tangent/axial means, leave radial motion free., supports(), fields(), main(), Finite-element stiffness/strain screening of a radially compliant shoe sheet., nset()

### Community 5 - "Community 5"
Cohesion: 0.43
Nodes (6): mesh_step(), Quadratic tetrahedral mesh adapter for the isolated flexure prototype., read_gmsh_inp(), fields(), main(), Finite-element stiffness/strain screening of a radially compliant shoe sheet.

### Community 6 - "Community 6"
Cohesion: 0.57
Nodes (6): Path, parse_frd(), Scoped MIT solver adapters copied from PPR; source provenance in manifest., reactions(), run(), solve()

### Community 7 - "Community 7"
Cohesion: 0.60
Nodes (4): cross_matrix(), Work-conjugate weighted rigid-section fit and statically exact surface…, resultant_loads(), rigid_fit_coefficients()

### Community 8 - "Community 8"
Cohesion: 0.60
Nodes (4): main(), page(), projection(), Vector review drawings from the actual STEP edge geometry.

### Community 10 - "Community 10"
Cohesion: 0.67
Nodes (3): main(), Contact-compatible linear screen using actual FE shoe compliance matrix. No…, solve_contact()

### Community 11 - "Community 11"
Cohesion: 0.67
Nodes (3): main(), Package a tested prototype snapshot; no fabrication/energization approval., sha()

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (3): expand(), main(), Hard-bore relief candidate, usable only with independently centred support.…

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (3): main(), Bind solver geometry to the separately exported prototype manufacturing body., sha()

## Knowledge Gaps
- **3 isolated node(s):** `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged`
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoundaryTests` connect `Community 3` to `Community 0`, `Community 9`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **What connects `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._