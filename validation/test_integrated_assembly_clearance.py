"""Live integrated CAD must reject repaired and new interference regressions."""
import sys
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'validation'), str(ROOT), str(ROOT/'cad/freecad/drive_v08')]
from integrated_assembly_clearance import audit
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.drive_v08.assembly import integrated_objects

items, _ = integrated_objects(final_objects())
result = audit(items)
assert result['unexpected_count'] == 0
assert result['physical_validation_state'] == 'NOT_RUN'
assert result['fabrication_authorized'] is False
by = {r['name']: r for r in items}


def rejected(rows):
    try:
        audit(rows)
    except ValueError:
        return
    raise AssertionError('invalid assembly was accepted')


rejected(items + [items[0]])
probe = by['TemperatureProbeT4']['shape'].copy()
probe.translate(App.Vector(-1, 0, 0))
assert probe.common(by['DownDieBody']['shape']).Volume > 0.01
rejected([dict(r, shape=probe) if r['name']=='TemperatureProbeT4' else r for r in items])
obstacle = dict(by['TemperatureProbeRetainerT1'], name='UnapprovedObstacle')
rejected(items + [obstacle])
rejected([dict(r, classification='manufactured_or_stock')
          if r['name']=='Spool' else r for r in items])
from cad.freecad.compact.geometry import mica_band_heater_shape
from cad.freecad.drive_v08.layout import moved
wide = mica_band_heater_shape(width=45)
wide.translate(App.Vector(0, 0, 40))
wide.rotate(App.Vector(), App.Vector(0, 1, 0), -90)
wide.translate(App.Vector(375, 347, 382))
wide = moved(wide, (0, 0, 1), 90, (667, 0, 0))
assert wide.common(by['FeederHousing']['shape']).Volume > 0.01
rejected([dict(r, shape=wide) if r['name']=='BarrelBandHeaterZ1' else r for r in items])
assert abs(by['BarrelBandHeaterZ1']['shape'].BoundBox.YLength - 40) < 1e-6
for zone in (2, 3):
    assert abs(by[f'BarrelBandHeaterZ{zone}']['shape'].BoundBox.YLength - 45) < 1e-6
print('GGM_INTEGRATED_CLEARANCE_TEST_PASS cases=7 physical=NOT_RUN')
