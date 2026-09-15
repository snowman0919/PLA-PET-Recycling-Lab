# Physical v0.8 scoped graph

AST + host-reviewed literal file/stage anchors for `validation/physical_v08` plus explicitly bound P5 RFQ sources and current SYS-04/hot-mount source/test contracts. No paid API calls. This is not a full repository semantic extraction.

# Graph Report - physical_v08  (2026-09-10)

## Corpus Check
- 46 files · ~6,120 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 159 nodes · 280 edges · 30 communities (29 shown, 1 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 63 edges (avg confidence: 1.0)
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

## God Nodes (most connected - your core abstractions)
1. `main()` - 12 edges
2. `read_csv()` - 10 edges
3. `root_rows()` - 9 edges
4. `P10 PLA_LOW_FEED` - 9 edges
5. `P3 GGM_DRIVE_BENCH` - 8 edges
6. `P6 COLD_EXTRUDER_ASSEMBLY` - 8 edges
7. `write_extruder_package()` - 7 edges
8. `P8 INSTALLED_MOTOR_DRY_RUN` - 7 edges
9. `export_shape_set()` - 6 edges
10. `main()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `assembly_rows()` --calls--> `assembly_step_number()`  [EXTRACTED]
  release/build_final_documents.py → release/build_bom_release.py
- `assembly_rows()` --calls--> `fastener_step_number()`  [EXTRACTED]
  release/build_final_documents.py → release/build_bom_release.py
- `assembly_rows()` --calls--> `fasteners()`  [EXTRACTED]
  release/build_final_documents.py → release/build_bom_release.py

## Import Cycles
- None detected.

## Communities (30 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.18
Nodes (25): active_reference_rows(), assembly_step(), assembly_step_number(), auxiliary(), category(), critical(), drawing(), enrich_final_manufacturing() (+17 more)

### Community 1 - "Community 1"
Cohesion: 0.20
Nodes (12): check_capability(), check_certificates(), check_measurements(), hashish(), interval(), main(), maybe(), num() (+4 more)

### Community 2 - "Community 2"
Cohesion: 0.24
Nodes (16): export_assembly(), export_shape_set(), main(), Human-readable hardwired motor-energy cut schematic for Gate-1., 가열기·센서의 실제 형상과 구매 전 RFQ 계약을 생성한다., Export every non-shredder stock/fabricated machine family., svg_barrel_drawing(), svg_die_drawing() (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.49
Nodes (13): P0 DIGITAL_TECHNICAL_ENTRY, P1 INVENTORY_AND_RECEIPT, P10 PLA_LOW_FEED, P11 PET_LOW_FEED, P12 FORMING_AND_SPOOL, P2 COLD_FRAME_AND_FIT, P3 GGM_DRIVE_BENCH, P4 SHREDDER_COUPON (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.36
Nodes (10): commissioning(), compile_typ(), drawing_set(), electrical(), main(), manuals(), Path, typ() (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (5): evaluate(), main(), Path, refresh_compliance(), sha()

### Community 6 - "Community 6"
Cohesion: 0.36
Nodes (4): main(), measured(), requirements(), solve()

### Community 7 - "Community 7"
Cohesion: 0.46
Nodes (6): current_fit(), fit_line(), main(), num(), read(), torque()

### Community 8 - "Community 8"
Cohesion: 0.48
Nodes (3): P5ExecutionTest, synthetic_packet(), write_csv()

### Community 10 - "Community 10"
Cohesion: 0.70
Nodes (4): close(), j(), main(), rows()

### Community 11 - "Community 11"
Cohesion: 0.67
Nodes (3): main(), Rebuild physical-v0.8 scoped graph using AST + literal reviewed anchors only., rel()

### Community 12 - "Community 12"
Cohesion: 0.83
Nodes (3): main(), require(), text()

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 5 inferred relationships involving `P10 PLA_LOW_FEED` (e.g. with `P11 PET_LOW_FEED` and `P4 SHREDDER_COUPON`) actually correct?**
  _`P10 PLA_LOW_FEED` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `P3 GGM_DRIVE_BENCH` (e.g. with `P0 DIGITAL_TECHNICAL_ENTRY` and `P4 SHREDDER_COUPON`) actually correct?**
  _`P3 GGM_DRIVE_BENCH` has 3 INFERRED edges - model-reasoned connections that need verification._