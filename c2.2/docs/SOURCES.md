# C2.2 inherited sources (read-only citations, retrieved 2026-09-21)

Worktree: `/home/monad/develop/PPR-c2.1-codex-20260921`, branch `codex/c2.1-s2-transmission-20260921`, HEAD `d42f32f915555f00d5ac97021f97ecfb1a6fbb98`, PR #5 OPEN (base `redesign/c2-20260921`). PPR-main (`/home/monad/develop/PPR`) consulted read-only, never modified.

## C2.1 handoff docs (all under `c2.1/docs/` in clean clone)

- `c2.1/docs/HANDOFF_KO.md` — S2 single-input reverse-output handoff; 1 DOF, no S2 motor; P0–P6 evidence; package state DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD; STEP SHAs (below); 41-solid subassembly; 196-solid machine; BOM 135 rows (11 known / 124 unknown); KiCad 43 devices / 174 pins / 67 nets, ERC 0, MPN coverage 0%.
- `c2.1/docs/OPEN_ACTIONS_KO.md` — 6 physical/user HOLDs (labels+drawings+measurements; landed quote; bearing/load/life/tolerance; safety selection; approved assembly test; PLA/PET/TPU calibration). Purchase/machining/energize HOLD until cleared.
- `c2.1/docs/ASSEMBLY_SERVICE_KO.md` — digital assembly/service/test procedure; S2 local frame Z-180° + translate (308.569, 299, 280) mm; process zone machine-Y 255..295 mm; input shaft coaxial ANSI35-12T @ X308.569/Z280; 7 physical test stages all DID_NOT_RUN.
- `c2.1/docs/ADR-001-S2-TRANSMISSION.md` — mechanism decision: fixed-ring cycloid + output pin/roller, fused rotor envelope (bolts/retention HOLD), rigid first-contact numbers only, split dual-path fallback condition.

## Policy entry point (NOT in clean clone)

- `docs/final/release_notes_v1.0.0-rc1_ko.md` — location PPR-main only (`/home/monad/develop/PPR/docs/final/`), per PPR-main AGENTS.md:17. v1.0.0-rc1 FABRICATION_CANDIDATE / FINAL_DESIGN_FROZEN snapshot / prerelease-publication-only approval. Different revision line; NOT the C2.1 contract.

## STEP SHAs (from HANDOFF_KO.md; verify before use)

- Machine integration: `c2.1/cad/PPR_C2_1_machine_integration.step` sha256 `e1756cac72a5426bc24bcdba21e919d9355be8d8eddaa61a69a516eabe38cb12` (196 solids reimported).
- S2 assembly: `c2.1/cad/PPR_C2_1_S2_transmission.step` sha256 `fbba8932ab7a132d67eeafeba519bd368a78bf564a22e4d8ea59e5df94f5a42b` (41 solids).
- S2 exploded: `c2.1/cad/PPR_C2_1_S2_transmission_exploded.step` sha256 `f05277f3ac60b25e1945cfb12bca37f06f900dc115a073afd4140f39d49470db` (41 solids).
- FreeCAD: `c2.1/cad/PPR_C2_1_machine_integration.FCStd` sha256 `b0041499c5c0f72e8e1ab6f000a940beab5314f40cfe5a4c0cef7c73df41a2d3` (156 valid objects, FreeCAD 0.21.2).

## Envelopes + S2 nominal

- Body 630×408×508 mm (limit 700×420×520, PASS). Operating 839×408×508 mm (target 850×450×510, PASS).
- S2: q=8, e=7 mm, rotor tip dia 110 mm, chamber dia 125.6 mm, process width 40 mm, input +120 rpm / output −15 rpm (φ=−θ/q), diametral stroke 14 mm, roller R5 / window R12.2 / clearance 0.2 mm (NON-INTERFERENCE ONLY, NOT loaded engagement).
- Power: PSU 24 V 800 W / 500 W op cap. Motors: shared shredder M1 ×1 UNSELECTED, extruder M2 ×1. Budget soft limit 100,000 KRW all-remaining-cost; known 200 W motor floor 110,200 KRW exceeds it.
- Parametric truth: `c2/src/engineering.py` (S2 class, hook_polygon), `c2/src/pin_constraint.py` (cycloid profile/verify), `c2.1/src/transmission.py`, `c2.1/src/build_cad.py`, `c2/src/build_cad.py`; params `design/parameters.json`, `design/assembly.json`, `c2/design/*`, `c2.1/design/*`.

## Evidence caveats (binding on C2.2)

- ALL material/fracture params: ASSUMPTION / UNCALIBRATED_DIGITAL_SENSITIVITY. CalculiX coupons used uncalibrated linear-elastic PLA/PET + Neo-Hooke TPU — NOT fracture/tear/throughput labels.
- Performance gate: BLOCKED_PERFORMANCE_DATA. Zero physical shredding tests; DEM uncalibrated; no torque/throughput/yield/jam/residence/energy measurements.
- Collision: sampled BRep only (static 820 pairs; dynamic 33 poses / 11,360 pairs), NOT continuous-BRep or full-machine proof. Bearings/rollers are envelopes (no MPN/L10). Guard is section envelope (not containment). Screen attachment, sensor wiring/response, thermal UA all HOLD.

## C2.2 I2–I6 artifacts (this workstream, UNCALIBRATED_DIGITAL_SENSITIVITY)

- I2: `sim/generators/waste_gen.py` + `sim/generators/bonds.py`, tests `tests/test_waste_gen.py` (15).
- I3: `sim/fracture/bond_manager.py`, `sim/experiments/i3_coupon.py`, `results/i3_summary.json` + `results/i3_coupons/` (12), tests `tests/test_fracture.py` (12).
- I4: `sim/mechanisms/architectures.py` (7 archs, S2-B baseline), `sim/experiments/i4_screen.py`, `results/i4_screen.json` (300→259), tests `tests/test_architectures.py` (15).
- I5: `sim/experiments/i5_benchmark.py`, `results/i5_benchmark.json` (324 runs) + `results/s1_fragments/` (84 sets), tests `tests/test_benchmark.py` (13).
- I6: `sim/optimization/i6_surrogate.py`, `results/i6_surrogate.json` + `results/pareto_candidates.json` (front 11, 81-sample robustness ×5 picks), tests `tests/test_surrogate.py` (10).
- Handoff: `docs/HANDOFF_KO.md` (Korean), `results/validation_summary.json` (I0–I6 gates), `results/architecture_comparison.json` (per-arch means), `results/open_actions.json` (7 blockers), `results/run_manifest.json` (file+SHA inventory).
- SOURCES.md itself extended by this section; no C2.1 file modified.

## C2.2b real headless PhysX dynamics Gates A–F (this workstream, UNCALIBRATED real-physics sensitivity)

- Gate A USD: `sim/assets/emit_usd.py` → `sim/assets/usd/machine.usda` + `machine.sidecar.json` (`dyn_usd_manifest/1` PASS, mm/F0); `sim/bootstrap/load_machine.py` → `results/dyn_usd_load.json` PASS (24 prims, 8 meshes, 584 verts, 10 steps). pxr confirmed present in `$HOME/env_isaacsim-c22` (Isaac 6.1.0.0).
- Gate B S1 PhysX: `sim/dynamics/s1_physx.py` (S1-A twin-shaft + per-fragment `IsaacContactSensor` + in-loop bond-break, impulse_scale 0.02 N·s ASSUMPTION_UNCALIBRATED) → `results/dyn_s1/` (14 runs JSONL + summary: W1/W4/P0, contacts >230 steps, breaks 42–46, mass error 0).
- Gate C transfer: `sim/dynamics/transfer.py` → `results/dyn_transfer.json` PASS (DERIVED S1_DISCHARGE/CHUTE/S2_ENTRY/S2_EXIT boxes; C2.1 CAD unmutated; identical S1 states to S2-A/B).
- Gate D screen: `sim/dynamics/s2_screen.py` (real hole geometry, proxy-free) → `results/dyn_s2/` (17 runs: S2-A pass 0.42–0.50 vs S2-B 0.17–0.29 across holes 3.0/4.0/5.5; 45° yaw ≥ 0°).
- Gate E dt sweep: `sim/dynamics/dt_sweep.py` → `results/dyn_dt_sweep.json` PASS (W1s7 + W4s11 × dt 0.0025/0.005/0.01; breaks stable, torque-impulse scales with dt — flagged).
- Gate F sweep + refit: `sim/dynamics/gap_screen_sweep.py` → `results/dyn_gap_screen_sweep.json` PASS (gap axis = shaft-center engagement 59.2/60.0/60.8 mm, NOT literal 0.4–1.2 mm clearance — unrepresentable with rigid r=40 mm cylinders at 60 mm centers; 6 S1 + 12 S2 all PASS); `sim/dynamics/retrain_surrogate.py` → `results/dyn_surrogate.json` PASS (additive; `i6_surrogate.py` untouched, `i5_benchmark.py` proxy intact).
- Contract tests: `tests/test_dynamics.py` (8 tests, manifest/schema evidence-level only, no SimulationApp).
- SOURCES.md itself extended by this section; no C2.1 file modified.
