# C2.2 — Headless Isaac Sim Multi-Shredder Fracture Benchmark (foundation scaffold)

Status: `SCAFFOLD_ONLY_NO_RESULTS`. No simulation run, no USD conversion, no fabrication/purchase/energize/merge authorization.

## Layout

- `docs/SOURCES.md` — inherited C2.1 design citations, STEP SHAs, envelope + S2 params, evidence caveats.
- `results/environment_manifest.json` — machine-readable host/toolchain snapshot (retrieved 2026-09-21).
- `sim/` — future pipeline packages: `bootstrap` (env/isaac checks), `assets` (STEP→USD conversion inputs/outputs), `generators` (parametric S1/S2 geometry variants), `fracture` (fracture/DEM models), `mechanisms` (cycloid/transmission kinematics), `experiments` (S1/S2 architecture search runs), `metrics` (yield/throughput/torque/jam/energy), `optimization` (search policy), `thermal` (5-node model port).
- `configs/` — run configs (I1 asset pipeline first).
- `tests/` — c2.2 regression tests (none yet; existing C2.1 suite stays in `c2.1/tests` unmodified).
- `scripts/` — operator scripts. `logs/` — run logs (git-ignored content expected).

## Inheritance (summary)

C2.1 package state `DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD`. Whole-machine STEP 196 solids (reimported 196), FreeCAD 156 valid objects, body 630×408×508 mm, operating 839×408×508 mm. S2 nominal q=8, e=7 mm, input +120 rpm / output −15 rpm, 1 independent DOF, shared M1 (UNSELECTED), separate M2. PSU 24 V 800 W / 500 W cap. BOM 135 rows, 124 cost-unknown. All material/fracture params are ASSUMPTION / UNCALIBRATED_DIGITAL_SENSITIVITY. Zero physical shredding tests. Details in `docs/SOURCES.md`.

## Gates

Physical release HOLD. Budget 100,000 KRW soft limit (known 200 W motor floor 110,200 KRW already exceeds it). M1 NOT SELECTED. I1 = USD asset pipeline from parametric Python + STEP sources; blocked on USD tooling (`pxr` absent — see manifest).
