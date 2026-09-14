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


def audit_dancer_retention(items, layout, parts):
    from validation.integrated_motion_clearance import contact_area, check_clear
    by = {r['name']: r['shape'] for r in items}
    manufactured = {r['id']: r for r in parts}
    required = {'DancerArm', 'DancerEndRoller', 'DancerSupportPlate'}
    for label, count in (('Pivot', 2), ('End', 3)):
        required |= {'Dancer'+label+'Axle', 'Dancer'+label+'CollarFront',
                     'Dancer'+label+'CollarRear'}
        required |= {'Dancer'+label+'Washer'+str(i) for i in range(count)}
    if len(by) != len(items) or not required <= set(by):
        raise ValueError('incomplete dancer retention assembly')
    result = []
    for key, label in (('pivot_axle', 'Pivot'), ('end_axle', 'End')):
        spec = layout[key]
        rod = by['Dancer'+label+'Axle']
        rb = rod.BoundBox
        part = manufactured[spec['part_id']]
        if part['qty'] != 1 or abs(part['shape'].BoundBox.ZLength-rb.YLength)>1e-6:
            raise ValueError('dancer axle manufacturing/assembly length mismatch')
        made = part['shape'].copy()
        made.rotate(App.Vector(), App.Vector(1, 0, 0), -90)
        made.translate(App.Vector(*spec['origin_mm']))
        if max(made.cut(rod).Volume, rod.cut(made).Volume) > 1e-4:
            raise ValueError('dancer axle manufacturing section or datum mismatch')
        if abs(rb.YLength-spec['length_mm'])>1e-6 or abs(rod.Volume-math.pi*16*rb.YLength)>1e-4:
            raise ValueError('dancer axle section or length mismatch')
        x, y, z = spec['origin_mm']
        if (abs(rb.YMin-y)>1e-6 or abs((rb.XMin+rb.XMax)/2-x)>1e-6
                or abs((rb.ZMin+rb.ZMax)/2-z)>1e-6):
            raise ValueError('dancer axle datum mismatch')
        for end in ('Front', 'Rear'):
            name = 'Dancer'+label+'Collar'+end
            collar = by[name]
            cb = collar.BoundBox
            margin = cb.YMin-rb.YMin if end=='Front' else rb.YMax-cb.YMax
            if margin+1e-6 < layout['minimum_shaft_end_margin_mm']:
                raise ValueError('under-engaged dancer collar: '+name)
            target = ('DancerSupportPlate' if label=='Pivot' and end=='Front'
                      else 'Dancer'+label+'Washer'+('0' if end=='Front' else
                           str(len(spec['washer_start_y_mm'])-1)))
            if contact_area(collar, by[target]) < 130:
                raise ValueError('dancer collar not seated: '+name)
            if collar.common(rod).Volume > 0.01:
                raise ValueError('dancer collar penetrates shaft')
            tool = Part.makeCylinder(3, 30, App.Vector(x,(cb.YMin+cb.YMax)/2,z+10.1))
            check_clear(tool, by, {name}, 'dancer collar tool '+name)
            result.append({'collar':name, 'shaft_end_margin_mm':margin,
                           'seated_on':target, 'tool_corridor_clear':True})
    arm = by['DancerArm'].BoundBox
    pivot_endplay = (by['DancerPivotWasher1'].BoundBox.YMin -
                     by['DancerPivotWasher0'].BoundBox.YMax - arm.YLength)
    roller_endplay = (by['DancerEndWasher1'].BoundBox.YMin -
                      by['DancerEndWasher0'].BoundBox.YMax -
                      by['DancerEndRoller'].BoundBox.YLength)
    low, high = layout['assembly_endplay_limits_mm']
    if not all(low <= gap <= high for gap in (pivot_endplay, roller_endplay)):
        raise ValueError('dancer endplay outside assembly window')
    washer = manufactured[layout['washer']['part_id']]
    if washer['qty'] != 5:
        raise ValueError('dancer washer BOM mismatch')
    for name in required:
        if 'Washer' in name and abs(washer['shape'].Volume-by[name].Volume)>1e-5:
            raise ValueError('dancer washer manufacturing mismatch')
    return {'status':'DANCER_RETENTION_GEOMETRY_PASS', 'collars':result,
            'manufacturing_lengths_mm':[layout[k]['length_mm'] for k in ('pivot_axle','end_axle')],
            'nominal_pivot_endplay_mm':pivot_endplay, 'nominal_roller_endplay_mm':roller_endplay,
            'washer_quantity':5, 'physical_validation_state':'NOT_RUN',
            'holding_force_verified':False, 'fabrication_authorized':False}
