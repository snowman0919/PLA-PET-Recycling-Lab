# PPR-C09 — Spool cone adapter

- revision: `implementation-crosssolver-v0.6`
- quantity: 2
- material: PLA
- nozzle diameter: 0.4 mm
- orientation: large face down
- layer height: 0.20 mm
- wall count: 5
- top/bottom layers: 5
- infill: 35%
- support: no
- support-contact region: none
- support removal: ream Ø12.2 spindle bore
- brim: none
- designed minimum wall: 2.0 mm
- estimated mass: 30.2 g/ea, 60.3 g total
- estimated print time: 5.0 h at 12 g/h planning rate
- fastener: 1x M6x30 through clamp + washer + nyloc
- insert or captured nut: none; metal shaft collar carries axial load
- tightening torque: 2.5 N.m
- fastener edge distance: radial cross-hole at z=10
- physical interfaces: Ø12.2 axial bore; Ø6.6 radial through hole
- tolerance: 0.30 mm spool core
- mating part: 12 mm metal spindle and metal collar
- assembly order: 18
- bounding box: 70.0 x 70.0 x 35.0 mm
- FreeCAD Python source: `PPR-C09.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **30.28 g** for released quantity
- PrusaSlicer package time: **2.10 h**
- support extrusion volume: **0.000 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
