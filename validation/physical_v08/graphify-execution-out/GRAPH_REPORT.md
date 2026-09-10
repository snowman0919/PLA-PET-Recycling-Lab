# Physical execution scoped graph

P0-P12 execution contracts only. AST + literal reviewed anchors; no paid API calls; not a full-repository semantic graph.

# Graph Report - physical_v08  (2026-09-10)

## Corpus Check
- 58 files · ~6,218 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 132 nodes · 195 edges · 26 communities
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 89 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 1
- Community 2
- Community 4
- Community 5
- Community 6
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
1. `main()` - 6 edges
2. `main()` - 5 edges
3. `num()` - 5 edges
4. `check_measurements()` - 5 edges
5. `check_certificates()` - 5 edges
6. `main()` - 5 edges
7. `main()` - 4 edges
8. `current_fit()` - 4 edges
9. `maybe()` - 4 edges
10. `hashish()` - 4 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (26 total, 0 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (13): P0 DIGITAL_TECHNICAL_ENTRY, P1 INVENTORY_AND_RECEIPT, P10 PLA_LOW_FEED, P11 PET_LOW_FEED, P12 FORMING_AND_SPOOL, P2 COLD_FRAME_AND_FIT, P3 GGM_DRIVE_BENCH, P4 SHREDDER_COUPON (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.45
Nodes (10): check_capability(), check_certificates(), check_measurements(), hashish(), interval(), main(), maybe(), num() (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.43
Nodes (7): check_p3(), main(), no(), num(), Path, read_csv(), yes()

### Community 5 - "Community 5"
Cohesion: 0.57
Nodes (6): current_fit(), fit_line(), main(), num(), read(), torque()

### Community 6 - "Community 6"
Cohesion: 0.53
Nodes (5): evaluate(), main(), Path, refresh_compliance(), sha()

### Community 8 - "Community 8"
Cohesion: 0.60
Nodes (4): main(), n(), prov(), Path

### Community 9 - "Community 9"
Cohesion: 0.60
Nodes (4): main(), n(), provenance(), Path

### Community 10 - "Community 10"
Cohesion: 0.83
Nodes (3): main(), n(), yes()

### Community 11 - "Community 11"
Cohesion: 0.67
Nodes (3): main(), num(), Path

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (3): main(), n(), Path

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (3): main(), n(), Path

### Community 14 - "Community 14"
Cohesion: 0.83
Nodes (3): main(), n(), prov()

### Community 15 - "Community 15"
Cohesion: 0.83
Nodes (3): add_file(), main(), sha()

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (3): main(), Build a no-paid-API graph for the physical execution contracts only., rel()

### Community 17 - "Community 17"
Cohesion: 0.83
Nodes (3): main(), req(), resolve()

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._