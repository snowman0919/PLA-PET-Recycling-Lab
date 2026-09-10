# Physical v0.8 scoped graph

AST + host-reviewed literal file/stage anchors only. No paid API calls. This is not a full semantic extraction of the repository.

# Graph Report - physical_v08  (2026-09-10)

## Corpus Check
- 29 files · ~4,167 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 67 nodes · 101 edges · 18 communities (16 shown, 2 thin omitted)
- Extraction: 40% EXTRACTED · 60% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6

## God Nodes (most connected - your core abstractions)
1. `P10 PLA_LOW_FEED` - 9 edges
2. `P3 GGM_DRIVE_BENCH` - 8 edges
3. `P6 COLD_EXTRUDER_ASSEMBLY` - 8 edges
4. `P8 INSTALLED_MOTOR_DRY_RUN` - 7 edges
5. `P4 SHREDDER_COUPON` - 6 edges
6. `main()` - 5 edges
7. `P0 DIGITAL_TECHNICAL_ENTRY` - 5 edges
8. `P1 INVENTORY_AND_RECEIPT` - 5 edges
9. `P2 COLD_FRAME_AND_FIT` - 5 edges
10. `P5 SCREW_BARREL_PROCESS_COUPON` - 5 edges

## Surprising Connections (you probably didn't know these)
- `sha()` --references--> `Path`  [EXTRACTED]
  simulation_prerequisite.py →   _Bridges community 1 → community 4_

## Import Cycles
- None detected.

## Communities (18 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.49
Nodes (13): P0 DIGITAL_TECHNICAL_ENTRY, P1 INVENTORY_AND_RECEIPT, P10 PLA_LOW_FEED, P11 PET_LOW_FEED, P12 FORMING_AND_SPOOL, P2 COLD_FRAME_AND_FIT, P3 GGM_DRIVE_BENCH, P4 SHREDDER_COUPON (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.24
Nodes (4): evaluate(), main(), refresh_compliance(), sha()

### Community 2 - "Community 2"
Cohesion: 0.46
Nodes (6): current_fit(), fit_line(), main(), num(), read(), torque()

### Community 3 - "Community 3"
Cohesion: 0.36
Nodes (4): main(), measured(), requirements(), solve()

### Community 5 - "Community 5"
Cohesion: 0.70
Nodes (4): close(), j(), main(), rows()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 5 inferred relationships involving `P10 PLA_LOW_FEED` (e.g. with `P11 PET_LOW_FEED` and `P4 SHREDDER_COUPON`) actually correct?**
  _`P10 PLA_LOW_FEED` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `P3 GGM_DRIVE_BENCH` (e.g. with `P0 DIGITAL_TECHNICAL_ENTRY` and `P4 SHREDDER_COUPON`) actually correct?**
  _`P3 GGM_DRIVE_BENCH` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `P6 COLD_EXTRUDER_ASSEMBLY` (e.g. with `P3 GGM_DRIVE_BENCH` and `P5 SCREW_BARREL_PROCESS_COUPON`) actually correct?**
  _`P6 COLD_EXTRUDER_ASSEMBLY` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `P8 INSTALLED_MOTOR_DRY_RUN` (e.g. with `P3 GGM_DRIVE_BENCH` and `P6 COLD_EXTRUDER_ASSEMBLY`) actually correct?**
  _`P8 INSTALLED_MOTOR_DRY_RUN` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `P4 SHREDDER_COUPON` (e.g. with `P3 GGM_DRIVE_BENCH` and `P5 SCREW_BARREL_PROCESS_COUPON`) actually correct?**
  _`P4 SHREDDER_COUPON` has 3 INFERRED edges - model-reasoned connections that need verification._