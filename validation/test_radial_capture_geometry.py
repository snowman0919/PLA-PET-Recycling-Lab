"""Check the actual C-saddle lip; this is not a contact-strength qualification."""
import json
import math
from pathlib import Path
import sys
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cad.freecad.final_v08.generate import mount_plate, PARAMS


def capture(plate, x, bore_radius, rod_radius):
    height = plate.BoundBox.ZMax - 382.0
    if not 0 < height < bore_radius or not 0 < rod_radius < bore_radius:
        raise ValueError('invalid C-saddle geometry')
    half_throat = math.sqrt(bore_radius**2-height**2)
    if rod_radius <= half_throat:
        raise ValueError('rod fits through the open throat')
    predicted = height-math.sqrt(rod_radius**2-half_throat**2)
    def overlap(lift):
        rod = Part.makeCylinder(rod_radius, 8, App.Vector(x,347,382+lift), App.Vector(1,0,0))
        return plate.common(rod).Volume
    if overlap(0) > 1e-6 or overlap(1) < 1e-3:
        raise ValueError('nominal interference or no retaining contact')
    lo, hi = 0.0, 1.0
    for _ in range(28):
        mid = (lo+hi)/2
        if overlap(mid) > 1e-6:
            hi = mid
        else:
            lo = mid
    if abs(hi-predicted) > 5e-5:
        raise ValueError('CAD and independent circle-intersection solution disagree')
    return dict(throat_width_mm=2*half_throat, analytical_lift_mm=predicted,
                cad_first_interference_mm=hi, volume_at_0p5_mm=overlap(.5))


mount = PARAMS['hot_zone_mount']
x = mount['rear_fixed_plate_x_mm']
plate = mount_plate(x, False)
base = json.loads((ROOT/'cad/parameters/baseline.json').read_text())
radius = base['extruder']['barrel_od_mm']/2
bore = mount['fixed_collar_bore_mm']/2
result = capture(plate, x, bore, radius)
assert result['throat_width_mm'] < 2*radius
assert .12 < result['cad_first_interference_mm'] < .15
opened = plate.cut(Part.makeBox(8,70,40,App.Vector(x,312,382)))
for shape, claimed_bore, rod in ((opened,bore,radius), (plate,bore,6.0),
                                 (plate,bore+.5,radius)):
    try:
        capture(shape,x,claimed_bore,rod)
    except ValueError:
        pass
    else:
        raise AssertionError('missing lip, undersize rod or mismatched bore accepted')
result.update(status='REAR_C_SADDLE_CAPTURE_GEOMETRY_PASS', cases=4,
              physical_validation_state='NOT_RUN', fabrication_authorized=False,
              load_capacity_verified=False, thermal_alignment_verified=False,
              scope='Rigid geometry at nominal dimensions, not contact pressure or load capacity')
print(json.dumps(result), flush=True)
