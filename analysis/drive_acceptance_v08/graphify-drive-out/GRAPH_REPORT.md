# Drive closeout review scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - PPR  (2026-09-10)

## Corpus Check
- 25 files · ~810 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 152 nodes · 239 edges · 14 communities (8 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.96)
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

## God Nodes (most connected - your core abstractions)
1. `integrated_objects()` - 17 edges
2. `Tests` - 16 edges
3. `GgmInput` - 16 edges
4. `Tests` - 11 edges
5. `calculate()` - 10 edges
6. `GgmDriveGuard` - 10 edges
7. `layout()` - 8 edges
8. `sha()` - 7 edges
9. `main()` - 7 edges
10. `check_bindings()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `integrated_objects()`  [EXTRACTED]
  cad/freecad/drive_v08/generate.py → cad/freecad/drive_v08/assembly.py
- `good()` --references--> `GgmInput`  [EXTRACTED]
  firmware/ggm_drive_v08/test_guard.cpp → firmware/arduino_mega/src/ggm_drive_guard.h
- `gather()` --calls--> `bound_path()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py
- `gather()` --calls--> `check_bindings()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py
- `gather()` --calls--> `sha()`  [EXTRACTED]
  analysis/drive_acceptance_v08/package_review.py → analysis/drive_acceptance_v08/verify_snapshot.py

## Import Cycles
- None detected.

## Communities (14 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.18
Nodes (23): box(), integrated_objects(), Motor integration: lengthwise direct extrusion and supported shredder shaft., ring(), details(), Explicit local support and attachment details for the GGM drive package., ggm_local(), item() (+15 more)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (6): calculate(), main(), Bounded drive load calculations; no material/gearbox acceptance inferred., Geometry evidence and drive arithmetic regressions; not physical tests., Tests, verify()

### Community 2 - "Community 2"
Cohesion: 0.14
Nodes (12): GgmDriveGuard, direction_, latched_, wait_start_, waiting_, GgmOutput, fault, screw (+4 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (11): main(), Read the exported assembly and independently inspect functional bearing lands., sha(), main(), Compare actual drive setpoints to conditional demand, without raising limits., sha(), main(), Drive-only object register from the exported native assembly, not purchase… (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (14): GgmInput, feedback_ms, feedback_valid, gearbox_nm_per_amp, motor_current_a, no_load_current_a, now_ms, profile_verified (+6 more)

### Community 5 - "Community 5"
Cohesion: 0.41
Nodes (10): encoded_manifest(), gather(), main(), Package the current GGM drive snapshot; never label it a machine release., write_zip(), bound_path(), check_bindings(), main() (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.46
Nodes (7): audit(), drawing(), export(), main(), Generate hash-bound GGM drive assets without replacing historical releases., sha(), load_base()

### Community 8 - "Community 8"
Cohesion: 0.60
Nodes (4): main(), Build an isolated GGM sketch from current source, retaining source hashes., replace_once(), sha()

## Knowledge Gaps
- **20 isolated node(s):** `now_ms`, `feedback_ms`, `shredder`, `screw`, `motor_current_a` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `now_ms`, `feedback_ms`, `shredder` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.1383399209486166 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.14210526315789473 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.13071895424836602 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._