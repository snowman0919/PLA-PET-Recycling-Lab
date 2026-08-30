# PPR-C06 — Gauge enclosure half

- revision: `coupled-digital-validation-v0.5`
- quantity: 2
- material: ABS
- nozzle diameter: 0.4 mm
- orientation: outer face down
- layer height: 0.20 mm
- wall count: 4
- top/bottom layers: 4
- infill: 25%
- support: slot bridge only
- support-contact region: 8x70 optical slot roof
- support removal: break bridge strands from open housing side
- brim: none
- designed minimum wall: 1.6 mm
- estimated mass: 33.2 g/ea, 66.3 g total
- estimated print time: 5.5 h at 12 g/h planning rate
- fastener: 4x M3x12
- insert or captured nut: 4x M3 heat-set insert OD4.6 x L5
- tightening torque: 0.5 N.m
- fastener edge distance: 7 mm boss centre; Ø12 boss
- physical interfaces: 4x Ø4.6 x5 blind insert bores; 8 mm optical slot
- tolerance: 0.20 mm optical slit
- mating part: LED/photodiode cross frame and opposite half
- assembly order: 14
- bounding box: 95.0 x 70.0 x 28.0 mm
- FreeCAD Python source: `PPR-C06.py` -> `cad/freecad/compact/geometry.py`
- dimension sheet: `dimension_sheet.svg`

Slicer 질량·시간은 `print_manifest.csv`와 `total_material_report.md`의 PrusaSlicer 결과가 지배한다.

<!-- SLICER_EVIDENCE_BEGIN -->
- PrusaSlicer package mass: **38.59 g** for released quantity
- PrusaSlicer package time: **3.74 h**
- support extrusion volume: **0.000 cm³** (G-code role integration; included in package mass)
<!-- SLICER_EVIDENCE_END -->
