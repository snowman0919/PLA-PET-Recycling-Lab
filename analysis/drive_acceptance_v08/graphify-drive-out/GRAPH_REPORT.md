# Drive closeout review scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - PPR  (2026-09-10)

## Corpus Check
- 41 files · ~1,126 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 252 nodes · 409 edges · 19 communities (12 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.96)
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
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17

## God Nodes (most connected - your core abstractions)
1. `Tests` - 30 edges
2. `integrated_objects()` - 17 edges
3. `Tests` - 16 edges
4. `GgmInput` - 16 edges
5. `current_records()` - 12 edges
6. `Tests` - 11 edges
7. `calculate()` - 10 edges
8. `GgmDriveGuard` - 10 edges
9. `reading()` - 8 edges
10. `receipts()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `gather()` --calls--> `bound_path()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py
- `gather()` --calls--> `check_bindings()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py
- `gather()` --calls--> `sha()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py
- `encoded_manifest()` --calls--> `sha()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py
- `main()` --calls--> `sha()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py

## Import Cycles
- None detected.

## Communities (19 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (30): GgmDriveGuard, direction_, latched_, wait_start_, waiting_, GgmInput, feedback_ms, feedback_valid (+22 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (7): current_records(), meta(), pin_record(), Synthetic records test rejection rules, not real components or measurements., reading(), receipts(), Tests

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (31): box(), integrated_objects(), Motor integration: lengthwise direct extrusion and supported shredder shaft., ring(), details(), Explicit local support and attachment details for the GGM drive package., audit(), drawing() (+23 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (9): Check actual R2 bearing relief and cover mounting in the exported CAD., Pre/post rear-relief local plate screen; rigid bolt bores, room-temperature…, Author explicit machining requirements; nominal geometry remains CAD-owned., Empty receiving and calibration packets, never fabricated measurement data., bind(), Verify scoped manufacturing outputs and distinguish numerical checks from…, sha(), Rebuild only the selected drive package with explicit success evidence. (+1 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (6): calculate(), main(), Bounded drive load calculations; no material/gearbox acceptance inferred., Geometry evidence and drive arithmetic regressions; not physical tests., Tests, verify()

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (10): main(), Read the exported assembly and independently inspect functional bearing lands., sha(), main(), Compare actual drive setpoints to conditional demand, without raising limits., sha(), main(), Drive-only object register from the exported native assembly, not purchase… (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.37
Nodes (12): dimh(), dimv(), line(), main(), matrix_for(), projection(), Produce dimensioned vector sheets from actual CAD, with HLR projections., sha() (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.41
Nodes (10): encoded_manifest(), gather(), main(), Package the current GGM drive snapshot; never label it a machine release., write_zip(), bound_path(), check_bindings(), main() (+2 more)

### Community 9 - "Community 9"
Cohesion: 0.44
Nodes (10): alignment(), currents(), evidence(), fit_line(), inspect(), interval(), number(), pins() (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.38
Nodes (4): Pre/post rear-relief local plate screen; rigid bolt bores, room-temperature…, mesh_step(), Quadratic tetrahedral refinement for the scoped thrust-plate comparison., read_gmsh_inp()

### Community 11 - "Community 11"
Cohesion: 0.70
Nodes (4): check_bindings(), main(), Package only verified drive manufacturing data; no physical authorization., sha()

## Knowledge Gaps
- **20 isolated node(s):** `now_ms`, `feedback_ms`, `shredder`, `screw`, `motor_current_a` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `now_ms`, `feedback_ms`, `shredder` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06747638326585695 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.1021021021021021 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.13213213213213212 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.1383399209486166 - nodes in this community are weakly interconnected._