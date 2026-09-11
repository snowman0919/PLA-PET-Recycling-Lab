# Physical execution scoped graph

P0-P12 execution contracts only. AST + literal reviewed anchors; no paid API calls; not a full-repository semantic graph.

# Graph Report - physical_v08  (2026-09-11)

## Corpus Check
- 84 files · ~11,347 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 290 nodes · 613 edges · 32 communities
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 130 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
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
- Community 19
- Community 21
- Community 25
- Community 26

## God Nodes (most connected - your core abstractions)
1. `evaluate()` - 12 edges
2. `evaluate()` - 12 edges
3. `evaluate()` - 11 edges
4. `evaluate()` - 11 edges
5. `evaluate_records()` - 10 edges
6. `evaluate()` - 9 edges
7. `evaluate()` - 8 edges
8. `evaluate()` - 8 edges
9. `evaluate()` - 8 edges
10. `check_cold()` - 8 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (32 total, 0 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.32
Nodes (19): boolean(), build_result(), canonical(), check_p3(), chip(), evaluate_records(), evidence(), interval_pass() (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.31
Nodes (15): authenticate(), bool_value(), design_limits(), evaluate(), load(), main(), member_file(), number() (+7 more)

### Community 3 - "Community 3"
Cohesion: 0.35
Nodes (14): datetime, authenticate_run_context(), authenticate_sample(), evaluate(), load(), main(), number(), profile_targets() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.41
Nodes (14): evaluate(), evaluate_measurements(), interval_pass(), load(), main(), number(), Path, read_rows() (+6 more)

### Community 5 - "Community 5"
Cohesion: 0.30
Nodes (14): authenticate(), check_capability(), check_certificates(), check_measurements(), evaluate(), hashish(), interval(), main() (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.31
Nodes (14): authenticate(), bool_value(), evaluate(), limit_ok(), load(), main(), number(), profile_contract() (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (13): P0 DIGITAL_TECHNICAL_ENTRY, P1 INVENTORY_AND_RECEIPT, P10 PLA_LOW_FEED, P11 PET_LOW_FEED, P12 FORMING_AND_SPOOL, P2 COLD_FRAME_AND_FIT, P3 GGM_DRIVE_BENCH, P4 SHREDDER_COUPON (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.53
Nodes (11): evaluate(), load_module(), main(), p0_digest(), Path, rows(), runtime_p0(), sha() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.45
Nodes (11): authenticate(), check_cold(), check_receipt(), evaluate(), limit_ok(), load_validator(), main(), number() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.39
Nodes (11): boolean(), evaluate(), evidence(), load(), main(), metric_ok(), number(), Path (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.42
Nodes (10): evaluate(), expected_inventory(), load_inspection(), main(), Path, read_csv(), require_time(), sha() (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.33
Nodes (9): add_file(), main(), Path, sha(), main(), Path, require_registry_payload(), validate_package() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.33
Nodes (9): axis_compatibility(), bolt_pattern_mismatch_mm(), evaluate(), _interval(), _load_inspection(), main(), Path, Worst bolt-centre mismatch after translating the gearbox to align its output… (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.42
Nodes (9): auth(), boolean(), evaluate(), main(), num(), Path, rows(), sha() (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.47
Nodes (8): authenticate(), evaluate(), limit_ok(), main(), number(), Path, read_rows(), sha()

### Community 16 - "Community 16"
Cohesion: 0.47
Nodes (8): authenticate(), bool_value(), evaluate(), main(), number(), Path, read_rows(), sha()

### Community 19 - "Community 19"
Cohesion: 0.57
Nodes (6): current_fit(), fit_line(), main(), num(), read(), torque()

### Community 21 - "Community 21"
Cohesion: 0.53
Nodes (5): evaluate(), main(), Path, refresh_compliance(), sha()

### Community 25 - "Community 25"
Cohesion: 0.67
Nodes (3): main(), Build a no-paid-API graph for the physical execution contracts only., rel()

### Community 26 - "Community 26"
Cohesion: 0.83
Nodes (3): main(), req(), resolve()

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11688311688311688 - nodes in this community are weakly interconnected._
- **Should `Community 7` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._