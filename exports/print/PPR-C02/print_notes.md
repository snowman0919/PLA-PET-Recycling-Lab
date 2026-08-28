# PPR-C02 — Anti-reach baffle chute

- revision: `solid-manifold-openmodelica-v0.4`
- quantity: 1
- material: PLA
- nozzle diameter: 0.4 mm
- orientation: outlet down
- layer height: 0.24 mm
- wall count: 5
- top/bottom layers: 5
- infill: 25%
- support: ledge undersides only
- support-contact region: two staggered ledge undersides
- support removal: needle-nose pliers through 100x50 outlet
- brim: none
- designed minimum wall: 2.0 mm
- estimated mass: 247.5 g/ea, 247.5 g total
- estimated print time: 20.6 h at 12 g/h planning rate
- fastener: 4x M4x12 + washer; 2x chamber M6 tie bolts through clearance holes
- insert or captured nut: 4x M4 nyloc nuts on metal side
- tightening torque: M4 1.2 N.m; M6 6 N.m
- fastener edge distance: 8 mm boss centre; Ø14 boss
- physical interfaces: 4x Ø4.5 mount; 2x Ø6.6 tie-bolt; 100x50 outlet; staggered 72 mm ledges
- tolerance: 0.40 mm flake path
- mating part: hopper and metal cutter chamber
- assembly order: 4
- bounding box: 190.0 x 120.0 x 90.0 mm
- FreeCAD Python source: `PPR-C02.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **243.32 g** for released quantity
- PrusaSlicer package time: **21.71 h**
- support extrusion volume: **4.651 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
