# Physical v0.8 scoped graph

AST + host-reviewed literal file/stage anchors for `validation/physical_v08` plus explicitly bound P5 RFQ generator/inspection/inquiry sources. No paid API calls. This is not a full repository semantic extraction.

# Graph Report - physical_v08  (2026-09-10)

## Corpus Check
- 41 files · ~5,770 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 114 nodes · 177 edges · 26 communities (25 shown, 1 thin omitted)
- Extraction: 63% EXTRACTED · 37% INFERRED · 0% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 1.0)
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

## God Nodes (most connected - your core abstractions)
1. `P10 PLA_LOW_FEED` - 9 edges
2. `P3 GGM_DRIVE_BENCH` - 8 edges
3. `P6 COLD_EXTRUDER_ASSEMBLY` - 8 edges
4. `write_extruder_package()` - 7 edges
5. `P8 INSTALLED_MOTOR_DRY_RUN` - 7 edges
6. `export_shape_set()` - 6 edges
7. `main()` - 6 edges
8. `P4 SHREDDER_COUPON` - 6 edges
9. `main()` - 5 edges
10. `num()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `sha()` --references--> `Path`  [EXTRACTED]
  validation/physical_v08/simulation_prerequisite.py →   _Bridges community 4 → community 2_

## Import Cycles
- None detected.

## Communities (26 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (16): export_assembly(), export_shape_set(), main(), Human-readable hardwired motor-energy cut schematic for Gate-1., 가열기·센서의 실제 형상과 구매 전 RFQ 계약을 생성한다., Export every non-shredder stock/fabricated machine family., svg_barrel_drawing(), svg_die_drawing() (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.49
Nodes (13): P0 DIGITAL_TECHNICAL_ENTRY, P1 INVENTORY_AND_RECEIPT, P10 PLA_LOW_FEED, P11 PET_LOW_FEED, P12 FORMING_AND_SPOOL, P2 COLD_FRAME_AND_FIT, P3 GGM_DRIVE_BENCH, P4 SHREDDER_COUPON (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.21
Nodes (5): Path, ExecutionToolsTest, P5ExecutionTest, synthetic_packet(), write_csv()

### Community 3 - "Community 3"
Cohesion: 0.45
Nodes (10): check_capability(), check_certificates(), check_measurements(), hashish(), interval(), main(), maybe(), num() (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.31
Nodes (4): evaluate(), main(), refresh_compliance(), sha()

### Community 6 - "Community 6"
Cohesion: 0.36
Nodes (4): main(), measured(), requirements(), solve()

### Community 7 - "Community 7"
Cohesion: 0.46
Nodes (6): current_fit(), fit_line(), main(), num(), read(), torque()

### Community 8 - "Community 8"
Cohesion: 0.70
Nodes (4): close(), j(), main(), rows()

### Community 9 - "Community 9"
Cohesion: 0.67
Nodes (3): main(), Rebuild physical-v0.8 scoped graph using AST + literal reviewed anchors only., rel()

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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