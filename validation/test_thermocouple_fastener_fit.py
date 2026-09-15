"""Nominal thread-bottom screen; not fastener strength or assembly approval."""
import json
from pathlib import Path
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[1]
path = ROOT/'exports/final/drive_ggm_v08/GGM-FULL-ASM.FCStd'
doc = App.openDocument(str(path))
objects = {o.Name: o.Shape for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()}
checked = 0
for zone in range(1, 5):
    plate = objects[f'TemperatureProbeRetainerT{zone}']
    body = objects['Barrel' if zone < 4 else 'DownDieBody']
    bounds = plate.BoundBox
    yc = (bounds.YMin + bounds.YMax) / 2
    zc = (bounds.ZMin + bounds.ZMax) / 2
    direction = App.Vector(1 if zone < 4 else -1, 0, 0)
    for washer in (0.2, 0.5, 0.8):
        x = bounds.XMin - washer if zone < 4 else bounds.XMax + washer
        for offset in (-5, 5):
            start = App.Vector(x, yc + offset if zone < 4 else yc,
                               zc if zone < 4 else zc + offset)
            short = Part.makeCylinder(1.2, 6, start, direction)
            long = Part.makeCylinder(1.2, 8, start, direction)
            assert plate.common(short).Volume < 1e-6, (zone, offset, 'plate hole')
            assert body.common(short).Volume < 1e-6, (zone, offset, 'M3x6 bottom')
            assert body.common(long).Volume > 0.1, (zone, offset, 'M3x8 must fail')
            checked += 1
App.closeDocument(doc.Name)
assert checked == 24
print('THERMOCOUPLE_FASTENER_GEOMETRY_PASS cases=24 M3x6_clear M3x8_bottoms physical=NOT_RUN')
