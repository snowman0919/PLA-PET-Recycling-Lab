# PPR-C08 — Solid-strand guide axle bracket

- revision: `final-design-fabrication-closure-v0.8`
- quantity: 2
- material: PLA
- nozzle diameter: 0.4 mm
- orientation: L side
- layer height: 0.20 mm
- wall count: 5
- top/bottom layers: 5
- infill: 40%
- support: yes under axle bore
- support-contact region: Ø5.2 axle-bore lower semicircle
- support removal: ream Ø5.2 after support removal
- brim: 5 mm
- designed minimum wall: 2.0 mm
- estimated mass: 40.5 g/ea, 81.0 g total
- estimated print time: 6.7 h at 12 g/h planning rate
- fastener: 2x M5x16 + washer + T-nut
- insert or captured nut: none
- tightening torque: 2.0 N.m
- fastener edge distance: 15 mm hole centre
- physical interfaces: 2x Ø5.5 base holes; Ø5.2 fixed-axle bore
- tolerance: Ø5.2 +0.20/0 printed/reamed axle clearance
- mating part: FM-GA-01 fixed Ø5 axle and profile; 625 bearings are seated in FM-GR-01
- assembly order: 16
- bounding box: 60.0 x 45.0 x 70.0 mm
- FreeCAD Python source: `PPR-C08.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **61.02 g** for released quantity
- PrusaSlicer package time: **4.55 h**
- support extrusion volume: **0.320 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
