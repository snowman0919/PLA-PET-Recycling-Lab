# PPR-C07 — Puller pinch guard

- revision: `solid-manifold-openmodelica-v0.4`
- quantity: 1
- material: ABS
- nozzle diameter: 0.4 mm
- orientation: outer face down
- layer height: 0.24 mm
- wall count: 5
- top/bottom layers: 5
- infill: 20%
- support: window bridge only
- support-contact region: 100x32 inspection-window upper edge
- support removal: deburr from open guard interior
- brim: none
- designed minimum wall: 2.0 mm
- estimated mass: 85.4 g/ea, 85.4 g total
- estimated print time: 7.1 h at 12 g/h planning rate
- fastener: 4x M4 captive screws
- insert or captured nut: 4x M4 rivnuts in metal puller plate
- tightening torque: 1.2 N.m
- fastener edge distance: 8 mm boss centre; Ø14 boss
- physical interfaces: 4x Ø4.5 through; 100x32 guarded window
- tolerance: 0.40 mm guard gap
- mating part: metal puller plate
- assembly order: 15
- bounding box: 150.0 x 100.0 x 65.0 mm
- FreeCAD Python source: `PPR-C07.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **99.40 g** for released quantity
- PrusaSlicer package time: **9.07 h**
- support extrusion volume: **0.000 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
