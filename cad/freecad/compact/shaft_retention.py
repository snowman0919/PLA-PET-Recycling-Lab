"""Purchased collar reference geometry, not a machining master or load rating."""
import FreeCAD as App
import Part


def collar_shape(center_x, start_y, center_z, spec):
    origin = App.Vector(center_x, start_y, center_z)
    axis = App.Vector(0, 1, 0)
    bore = spec['bore_mm'] / 2
    outer = spec['outer_diameter_mm'] / 2
    width = spec['width_mm']
    screw_radius = spec['screw_major_diameter_mm'] / 2
    screw_length = spec['screw_length_mm']
    tip_length = spec['screw_tip_envelope_length_mm']
    ring = Part.makeCylinder(outer, width, origin, axis)
    ring = ring.cut(Part.makeCylinder(bore, width, origin, axis))
    tip = App.Vector(center_x, start_y + width / 2, center_z + bore)
    ring = ring.cut(Part.makeCylinder(screw_radius, screw_length + 1, tip))
    screw = Part.makeCone(0, screw_radius, tip_length, tip)
    body = Part.makeCylinder(screw_radius, screw_length - tip_length,
                             tip + App.Vector(0, 0, tip_length))
    screw = screw.fuse(body).removeSplitter()
    result = Part.makeCompound([ring.removeSplitter(), screw])
    if not result.isValid() or len(result.Solids) != 2:
        raise ValueError('invalid collar reference assembly')
    return result


def traverse_collar_rows(layout):
    spec = layout['retention']
    thickness = layout['plate_thickness_mm']
    front = layout['plate_origins_mm'][0][1] - spec['width_mm']
    rear = layout['plate_origins_mm'][1][1] + thickness
    for label, origin in zip(('A', 'B'), layout['rod_origins_mm']):
        x, _, z = origin
        for end, y in (('Front', front), ('Rear', rear)):
            yield {
                'name': 'TraverseCollar' + label + end,
                'shape': collar_shape(x, y, z, spec),
                'material': 'SP-SC-08 GN 705-8-E reference; 8x16x8 with M4x6',
                'classification': 'purchased_reference_lod',
                'evidence': spec['manufacturer_source'],
                'group': 'spooler',
            }
