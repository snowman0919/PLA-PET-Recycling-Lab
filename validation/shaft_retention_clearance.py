"""Check nominal traverse axial stops and access; not a holding-force test."""
import math
import FreeCAD as App
import Part


def audit_traverse_retention(items, layout):
    from validation.integrated_motion_clearance import contact_area, check_clear
    by = {row['name']: row['shape'] for row in items}
    if len(by) != len(items):
        raise ValueError('duplicate assembly identity')
    spec = layout['retention']
    names = ['TraverseCollar' + rod + end
             for rod in ('A', 'B') for end in ('Front', 'Rear')]
    if len(names) != spec['quantity'] or not set(names) <= set(by):
        raise ValueError('missing or duplicate-scope traverse axial stops')
    if layout['axis'] != [0, 1, 0]:
        raise ValueError('retention audit requires spool-parallel traverse axis')
    checks = []
    for label in ('A', 'B'):
        rod = by['TraverseRod' + label]
        box = rod.BoundBox
        length = box.YLength
        if abs(length - layout['rod_length_mm']) > 1e-6:
            raise ValueError('guide rod does not match its manufacturing length')
        if abs(rod.Volume - math.pi * 16 * length) > 1e-4:
            raise ValueError('guide rod lost its continuous 8 mm bearing section')
        for end, plate_name in (('Front', 'TraverseEndPlateLeft'),
                                ('Rear', 'TraverseEndPlateRight')):
            name = 'TraverseCollar' + label + end
            collar = by[name]
            cb = collar.BoundBox
            margin = cb.YMin - box.YMin if end == 'Front' else box.YMax - cb.YMax
            face = contact_area(collar, by[plate_name])
            if margin + 1e-6 < spec['rod_end_margin_mm']:
                raise ValueError('insufficient guide rod engagement: ' + name)
            if face < 140.0:
                raise ValueError('axial stop lacks its intended annular support face: ' + name)
            if collar.common(rod).Volume > 0.01:
                raise ValueError('collar/screw reference penetrates guide rod: ' + name)
            x = (box.XMin + box.XMax) / 2
            z = (box.ZMin + box.ZMax) / 2
            y = (cb.YMin + cb.YMax) / 2
            top = z + spec['bore_mm'] / 2 + spec['screw_length_mm']
            tool = Part.makeCylinder(spec['tool_corridor_radius_mm'],
                                     spec['tool_corridor_length_mm'],
                                     App.Vector(x, y, top + 0.1))
            check_clear(tool, by, {name}, 'collar top tool corridor ' + name)
            checks.append({'collar': name, 'plate': plate_name,
                           'annular_contact_area_mm2': face,
                           'rod_end_margin_mm': margin, 'tool_corridor_clear': True})
    return {'status': 'TRAVERSE_AXIAL_STOP_GEOMETRY_PASS', 'checks': checks,
            'guide_rod_length_mm': layout['rod_length_mm'], 'collar_quantity': len(names),
            'physical_validation_state': 'NOT_RUN', 'fabrication_authorized': False,
            'holding_force_verified': False, 'manufacturer_source': spec['manufacturer_source'],
            'limitations': ['received dimensions and screw protrusion',
                            'manufacturer tightening torque and axial slip force',
                            'shaft indentation/burrs outside the carriage stroke',
                            'loaded stroke, wear and limit stopping distance']}
