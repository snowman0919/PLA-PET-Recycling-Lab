# PPR-C05 — Cooling duct segment

- revision: `solid-manifold-openmodelica-v0.4`
- quantity: 2
- material: ABS
- nozzle diameter: 0.4 mm
- orientation: end face down
- layer height: 0.24 mm
- wall count: 4
- top/bottom layers: 4
- infill: 15%
- support: no
- support-contact region: none
- support removal: none
- brim: 5 mm
- designed minimum wall: 1.6 mm
- estimated mass: 79.7 g/ea, 159.5 g total
- estimated print time: 13.3 h at 12 g/h planning rate
- fastener: 8x M4x12 + washer + nyloc
- insert or captured nut: none
- tightening torque: 1.2 N.m
- fastener edge distance: 5 mm hole centre
- physical interfaces: 8x Ø4.5 flange holes; 60x55 clear air opening
- tolerance: 0.30 mm flange registration
- mating part: 80 mm fan and next duct
- assembly order: 13
- bounding box: 80.0 x 75.0 x 100.0 mm
- FreeCAD Python source: `PPR-C05.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **89.52 g** for released quantity
- PrusaSlicer package time: **6.76 h**
- support extrusion volume: **0.000 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
