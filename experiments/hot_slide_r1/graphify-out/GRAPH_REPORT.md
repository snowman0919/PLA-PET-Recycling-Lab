# HS-R1-S2 scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - hot_slide_r1  (2026-09-09)

## Corpus Check
- 24 files · ~1,444 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 116 nodes · 236 edges · 15 communities (11 shown, 4 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.96)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12

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
- `main()` --calls--> `supports()`  [EXTRACTED]
  solve_sliding_gradients.py → pin_supports.py
- `main()` --calls--> `mesh_step()`  [EXTRACTED]
  solve_sliding_gradients.py → quadratic_mesh.py
- `main()` --calls--> `read_gmsh_inp()`  [EXTRACTED]
  solve_sliding_gradients.py → quadratic_mesh.py
- `main()` --calls--> `nset()`  [EXTRACTED]
  solve_sliding_gradients.py → solver_kernel.py

## Import Cycles
- None detected.

## Communities (15 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (22): cross_matrix(), Work-conjugate weighted rigid-section fit and statically exact surface…, resultant_loads(), rigid_fit_coefficients(), Path, Three radial slots: constrain tangent/axial means, leave radial motion free., supports(), mesh_step() (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.27
Nodes (8): face-gradient-not-converged, Synthetic regression cases for measurement uncertainty and real trace coverage., main(), Synthetic validator regression tests; none are physical test evidence., evaluate(), number(), outcome(), Screen pressureless measurement records; never operate or authorize hardware.

### Community 3 - "Community 3"
Cohesion: 0.30
Nodes (10): cyl(), main(), FreeCAD prototype: replace hard radial fit by three elastic shoes. Not an…, rotor_sheet(), carrier(), circle(), export_one(), local_to_station() (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (4): main(), Package a tested prototype snapshot; no fabrication/energization approval., sha(), Rebuild this experiment's local graph with AST and reviewed document links.

### Community 6 - "Community 6"
Cohesion: 0.60
Nodes (4): main(), page(), projection(), Vector review drawings from the actual STEP edge geometry.

### Community 8 - "Community 8"
Cohesion: 0.67
Nodes (3): main(), Contact-compatible linear screen using actual FE shoe compliance matrix. No…, solve_contact()

### Community 9 - "Community 9"
Cohesion: 0.67
Nodes (3): expand(), main(), Hard-bore relief candidate, usable only with independently centred support.…

### Community 10 - "Community 10"
Cohesion: 0.67
Nodes (3): main(), Bind solver geometry to the separately exported prototype manufacturing body., sha()

## Knowledge Gaps
- **3 isolated node(s):** `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged`
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoundaryTests` connect `Community 4` to `Community 1`, `Community 7`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **What connects `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._