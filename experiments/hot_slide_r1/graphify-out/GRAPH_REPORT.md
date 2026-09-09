# HS-R1-S2 scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - hot_slide_r1  (2026-09-09)

## Corpus Check
- 34 files · ~3,074 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 201 nodes · 426 edges · 14 communities (11 shown, 3 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.92)
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
1. `QualificationTests` - 36 edges
2. `BoundaryTests` - 29 edges
3. `fixture()` - 16 edges
4. `friction_summary()` - 16 edges
5. `minimum_yield_floor()` - 15 edges
6. `material_issues()` - 14 edges
7. `FloorTests` - 12 edges
8. `solve()` - 11 edges
9. `main()` - 10 edges
10. `main()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `minimum_yield_floor()`  [EXTRACTED]
  package_review.py → qualification/minimum_requirements.py
- `main()` --calls--> `resultant_loads()`  [EXTRACTED]
  solve_sliding_gradients.py → distributing_patch_v08.py
- `main()` --calls--> `supports()`  [EXTRACTED]
  solve_sliding_gradients.py → pin_supports.py
- `main()` --calls--> `mesh_step()`  [EXTRACTED]
  solve_sliding_gradients.py → quadratic_mesh.py
- `main()` --calls--> `read_gmsh_inp()`  [EXTRACTED]
  solve_sliding_gradients.py → quadratic_mesh.py

## Import Cycles
- None detected.

## Communities (14 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (13): artifact(), EvidenceError, friction_summary(), interval(), material_issues(), number(), Evidence reduction, not certificate authentication or hardware approval., Presence/integrity review cannot authenticate documents or authorize hardware. (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (26): cross_matrix(), Work-conjugate weighted rigid-section fit and statically exact surface…, resultant_loads(), rigid_fit_coefficients(), Path, Three radial slots: constrain tangent/axial means, leave radial motion free., supports(), mesh_step() (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (9): main(), Package a tested prototype snapshot; no fabrication/energization approval., sha(), minimum_yield_floor(), Current provisional strength floor; integrity is not material certification., FloorTests, Reject stale or weakened provisional material requirements; synthetic only., main() (+1 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (16): face-gradient-not-converged, main(), Explicit public-source retrieval; downloaded originals stay outside Git., expand(), main(), Hard-bore relief candidate, usable only with independently centred support.…, Synthetic regression cases for measurement uncertainty and real trace coverage., main() (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.18
Nodes (7): bolt_screen(), drag_budget(), finite(), main(), pressure_force(), Read-only engineering evidence calculations. No equipment control., sha()

### Community 6 - "Community 6"
Cohesion: 0.30
Nodes (10): cyl(), main(), FreeCAD prototype: replace hard radial fit by three elastic shoes. Not an…, rotor_sheet(), carrier(), circle(), export_one(), local_to_station() (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.60
Nodes (4): main(), page(), projection(), Vector review drawings from the actual STEP edge geometry.

### Community 8 - "Community 8"
Cohesion: 0.67
Nodes (3): main(), Contact-compatible linear screen using actual FE shoe compliance matrix. No…, solve_contact()

## Knowledge Gaps
- **3 isolated node(s):** `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged`
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QualificationTests` connect `Community 0` to `Community 5`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `fixture-not-machine-replacement`, `physical-tests-not-run`, `face-gradient-not-converged` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0975609756097561 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.1411764705882353 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.12923076923076923 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._