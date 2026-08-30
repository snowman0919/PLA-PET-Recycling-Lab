# PPR-C11 — Control panel bezel

- revision: `coupled-digital-validation-v0.5`
- quantity: 1
- material: PLA
- nozzle diameter: 0.4 mm
- orientation: front face down
- layer height: 0.20 mm
- wall count: 4
- top/bottom layers: 4
- infill: 20%
- support: no
- support-contact region: none
- support removal: none
- brim: none
- designed minimum wall: 1.6 mm
- estimated mass: 61.5 g/ea, 61.5 g total
- estimated print time: 5.1 h at 12 g/h planning rate
- fastener: 4x M3x10
- insert or captured nut: 4x M3 heat-set insert OD4.2 x L5
- tightening torque: 0.5 N.m
- fastener edge distance: 8 mm boss centre; Ø12 boss
- physical interfaces: 4x Ø4.2 x5 blind insert bores; 145x82 display opening
- tolerance: 0.25 mm TFT
- mating part: metal control panel
- assembly order: 21
- bounding box: 180.0 x 120.0 x 8.0 mm
- FreeCAD Python source: `PPR-C11.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **43.71 g** for released quantity
- PrusaSlicer package time: **4.03 h**
- support extrusion volume: **0.000 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
