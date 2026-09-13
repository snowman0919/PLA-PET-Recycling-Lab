# Physical execution scoped graph

P0-P12 execution contracts plus scoped integrated geometry and R1 dependencies. AST + literal reviewed anchors; no paid API calls; not a full-repository semantic graph.

# Graph Report - physical_v08  (2026-09-13)

## Corpus Check
- 101 files · ~12,948 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 479 nodes · 1013 edges · 47 communities (43 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 133 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
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
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 26
- Community 27
- Community 28
- Community 31
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40

## God Nodes (most connected - your core abstractions)
1. `assembly_objects()` - 48 edges
2. `one_solid()` - 43 edges
3. `machine_fabrication_parts()` - 27 edges
4. `evaluate()` - 12 edges
5. `evaluate()` - 12 edges
6. `validate()` - 12 edges
7. `joined()` - 12 edges
8. `evaluate()` - 11 edges
9. `evaluate()` - 11 edges
10. `evaluate_records()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `integrated_objects()`  [EXTRACTED]
  validation/integrated_assembly_clearance.py → cad/freecad/drive_v08/assembly.py
- `main()` --calls--> `integrated_objects()`  [EXTRACTED]
  validation/integrated_motion_clearance.py → cad/freecad/drive_v08/assembly.py
- `main()` --calls--> `integrated_objects()`  [EXTRACTED]
  analysis/frame_v08/audit_geometry.py → cad/freecad/drive_v08/assembly.py
- `main()` --calls--> `apply_revision()`  [EXTRACTED]
  analysis/frame_v08/audit_geometry.py → cad/freecad/drive_v08/frame_revision.py
- `main()` --calls--> `steel_tie()`  [EXTRACTED]
  analysis/frame_v08/audit_geometry.py → cad/freecad/drive_v08/frame_revision.py

## Import Cycles
- None detected.

## Communities (47 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (32): contacts(), main(), native_id(), profiles(), Audit the small frame delta using actual FreeCAD solids and contact distances., sha(), identity(), main() (+24 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (25): chain_sprocket_shape(), down_die_body(), down_die_breaker_plate(), down_die_copper_gasket(), down_die_insert(), down_die_relief_retainer(), hot_shield_shape(), mica_band_heater_shape() (+17 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (22): beam_checks(), check_hashes(), checked(), finite(), R1: bind integrated CAD, comparative evidence and cut demand; no cut permission., sha(), validate(), checked_file() (+14 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (19): bearing_retainer_plate(), bearing_side_plate(), cutter_shaft(), _cycloidal_ease(), cycloidal_hook_profile_points(), motor_mount_plate(), Closed-solid source geometry for the compact v0.5 machine. Review keep-outs are…, Unit cycloid displacement, with zero slope at both ends. (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (20): cylindrical_hopper(), dancer_support_plate_shape(), feed_hopper_gasket_shape(), feeder_drive_coupling_shape(), guide_roller_retainer_shape(), machine_fabrication_parts(), puller_eccentric_bushing_shape(), puller_plate_shape() (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.32
Nodes (19): boolean(), build_result(), canonical(), check_p3(), chip(), evaluate_records(), evidence(), interval_pass() (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (17): assembly_objects(), box(), cyl(), die_cartridge_heater_shape(), flake_bin_sheet_shape(), hook_disc(), motor_adapter_gmp60_shape(), print_parts() (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (16): dancer_arm_shape(), feeder_auger_shape(), feeder_drive_mount_shape(), feeder_housing_shape(), feeder_reference_drive_shape(), gmp60_60127_reference_shape(), joined(), k_type_probe_shape() (+8 more)

### Community 9 - "Community 9"
Cohesion: 0.31
Nodes (15): authenticate(), bool_value(), design_limits(), evaluate(), load(), main(), member_file(), number() (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.35
Nodes (14): datetime, authenticate_run_context(), authenticate_sample(), evaluate(), load(), main(), number(), profile_targets() (+6 more)

### Community 11 - "Community 11"
Cohesion: 0.42
Nodes (14): evaluate(), evaluate_measurements(), interval_pass(), load(), main(), number(), Path, read_rows() (+6 more)

### Community 12 - "Community 12"
Cohesion: 0.30
Nodes (14): authenticate(), check_capability(), check_certificates(), check_measurements(), evaluate(), hashish(), interval(), main() (+6 more)

### Community 13 - "Community 13"
Cohesion: 0.31
Nodes (14): authenticate(), bool_value(), evaluate(), limit_ok(), load(), main(), number(), profile_contract() (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (13): P0 DIGITAL_TECHNICAL_ENTRY, P1 INVENTORY_AND_RECEIPT, P10 PLA_LOW_FEED, P11 PET_LOW_FEED, P12 FORMING_AND_SPOOL, P2 COLD_FRAME_AND_FIT, P3 GGM_DRIVE_BENCH, P4 SHREDDER_COUPON (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.53
Nodes (11): evaluate(), load_module(), main(), p0_digest(), Path, rows(), runtime_p0(), sha() (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.45
Nodes (11): authenticate(), check_cold(), check_receipt(), evaluate(), limit_ok(), load_validator(), main(), number() (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.39
Nodes (11): boolean(), evaluate(), evidence(), load(), main(), metric_ok(), number(), Path (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.42
Nodes (10): evaluate(), expected_inventory(), load_inspection(), main(), Path, read_csv(), require_time(), sha() (+2 more)

### Community 20 - "Community 20"
Cohesion: 0.33
Nodes (9): add_file(), main(), Path, sha(), main(), Path, require_registry_payload(), validate_package() (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.33
Nodes (9): axis_compatibility(), bolt_pattern_mismatch_mm(), evaluate(), _interval(), _load_inspection(), main(), Path, Worst bolt-centre mismatch after translating the gearbox to align its output… (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.42
Nodes (9): auth(), boolean(), evaluate(), main(), num(), Path, rows(), sha() (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.47
Nodes (8): authenticate(), evaluate(), limit_ok(), main(), number(), Path, read_rows(), sha()

### Community 24 - "Community 24"
Cohesion: 0.47
Nodes (8): authenticate(), bool_value(), evaluate(), main(), number(), Path, read_rows(), sha()

### Community 26 - "Community 26"
Cohesion: 0.52
Nodes (6): benchmark(), closest(), main(), model(), Conditional 3D Euler-Bernoulli comparison, not assembled-joint qualification., stiffness()

### Community 27 - "Community 27"
Cohesion: 0.57
Nodes (6): current_fit(), fit_line(), main(), num(), read(), torque()

### Community 28 - "Community 28"
Cohesion: 0.53
Nodes (5): evaluate(), main(), Path, refresh_compliance(), sha()

### Community 31 - "Community 31"
Cohesion: 0.60
Nodes (4): csvfile(), main(), Generate the authoritative integrated-frame schedule from verified native CAD., sha()

### Community 34 - "Community 34"
Cohesion: 0.67
Nodes (3): main(), Build a no-paid-API graph for the physical execution contracts only., rel()

### Community 35 - "Community 35"
Cohesion: 0.83
Nodes (3): main(), req(), resolve()

### Community 36 - "Community 36"
Cohesion: 0.67
Nodes (3): drive_guard_shape(), open_front_sheet_shell(), Five-sided sheet enclosure, open on local Y=0 service/front face.

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `machine_fabrication_parts()` connect `Community 5` to `Community 1`, `Community 36`, `Community 37`, `Community 38`, `Community 7`, `Community 8`, `Community 39`, `Community 40`, `Community 4`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10241820768136557 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.10869565217391304 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Community 8` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._