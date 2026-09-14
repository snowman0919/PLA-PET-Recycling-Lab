"""Current GGM nominal motion and mounting checks, not operational approval."""
import hashlib
import json
import sys
from pathlib import Path
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[1]

def overlap(a, b):
    x, y = a.BoundBox, b.BoundBox
    if not all(min(getattr(x,k+'Max'),getattr(y,k+'Max')) > max(getattr(x,k+'Min'),getattr(y,k+'Min'))+1e-7 for k in 'XYZ'):
        return 0.0
    return a.common(b).Volume

def check_clear(shape, by, excluded, label):
    for name, fixed in by.items():
        if name not in excluded and overlap(shape, fixed) > 0.01:
            raise ValueError(label+' obstructed by '+name)

def contact_area(left, right):
    if left.distToShape(right)[0] > 1e-6 or overlap(left, right) > 0.01:
        return 0.0
    return sum(a.common(b).Area for a in left.Faces for b in right.Faces)


def major_axis(shape):
    b = shape.BoundBox
    return max(range(3), key=lambda i: (b.XLength,b.YLength,b.ZLength)[i])

def audit(items):
    by = {row['name']:row['shape'] for row in items}
    if len(by) != len(items) or any(s.isNull() or not s.isValid() or not s.Solids for s in by.values()):
        raise ValueError('invalid solid or duplicate assembly identity')
    config = json.loads((ROOT/'cad/parameters/baseline.json').read_text())

    travel = config['spooler']['traverse_mm']
    if major_axis(by['SpoolSpindle']) != 1 or any(major_axis(by[n]) != 1 for n in ('TraverseRodA','TraverseRodB')):
        raise ValueError('traverse must be parallel to the spool spindle Y axis')
    carriage = by['PPR-C10_TraverseCarriage']
    b = carriage.BoundBox
    swept = Part.makeBox(b.XLength,b.YLength+travel,b.ZLength,App.Vector(b.XMin,b.YMin,b.ZMin))
    check_clear(swept, by, {'PPR-C10_TraverseCarriage','TraverseRodA','TraverseRodB'}, 'continuous traverse bounding envelope')
    for offset in range(int(travel)+1):
        shape = carriage.copy();shape.translate(App.Vector(0,offset,0))
        check_clear(shape, by, {'PPR-C10_TraverseCarriage'}, 'traverse '+str(offset))
    contacts = {}
    for side, base in [('Left','FrameBottomCross440'),('Right','FrameBottomCross608')]:
        post, plate = by['FrameTraversePost'+side], by['TraverseEndPlate'+side]
        contacts[side] = {'base_area_mm2':contact_area(post, by[base]), 'plate_area_mm2':contact_area(post, plate)}
        if contacts[side]['base_area_mm2'] < 399.9 or contacts[side]['plate_area_mm2'] < 500:
            raise ValueError('traverse support face missing: '+side)
    dancer = {'DancerArm','DancerEndRoller','DancerEndAxle'}
    for angle in range(-25,26):
        for name in dancer:
            shape=by[name].copy();shape.rotate(App.Vector(188,452,115),App.Vector(0,1,0),angle)
            check_clear(shape,by,dancer,'dancer '+str(angle))

    lid = by['PPR-C01_SlidingLid']; b=lid.BoundBox
    mouth = Part.makeCylinder(98,1,App.Vector(125,395,900))
    if mouth.cut(lid).Volume > 0.01:
        raise ValueError('closed lid does not cover the hopper opening')
    lid_travel=config['input_lid']['service_travel_mm']
    sweep=Part.makeBox(b.XLength+lid_travel,b.YLength,b.ZLength,App.Vector(b.XMin-lid_travel,b.YMin,b.ZMin))
    check_clear(sweep,by,{'PPR-C01_SlidingLid'},'left lid service envelope')
    from validation.shaft_retention_clearance import audit_traverse_retention
    retention = audit_traverse_retention(items, config['spooler']['traverse_layout'])
    return {'status':'GGM_NOMINAL_MOTION_CLEARANCE_PASS',
        'traverse_retention': retention,
        'traverse_axis':'Y_PARALLEL_TO_SPOOL', 'traverse_stroke_mm':travel,
        'continuous_traverse_bounding_envelope_clear':True,'traverse_sample_count':int(travel)+1,
        'dancer_sample_count':51,'support_contacts':contacts,
        'lid_opening_covered':True,'lid_service_direction':'NEGATIVE_X',
        'lid_service_travel_mm':lid_travel,'lid_service_left_extent_mm':b.XMin-lid_travel,
        'physical_validation_state':'NOT_RUN','fabrication_authorized':False,
        'scope':'Nominal solids and service space. Dancer sampled; not a continuous angular proof.',
        'not_qualified':['received collar tightening torque and axial-slip proof','limit actuation and stopping distance','bracket/joint capacity and carriage wear','filament routing, belt drive and winding','lid rails, interlock and tool access']}

def main():
    sys.path[:0]=[str(ROOT),str(ROOT/'cad/freecad/drive_v08')]
    from cad.freecad.final_v08.generate import final_objects
    from cad.freecad.drive_v08.assembly import integrated_objects
    items,_=integrated_objects(final_objects())
    result=audit(items)
    from validation.integrated_assembly_clearance import geometry_source_paths
    sources=geometry_source_paths()+[Path(__file__).resolve(),ROOT/'validation/integrated_assembly_clearance.py', ROOT/'validation/shaft_retention_clearance.py']
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    out=ROOT/'analysis/frame_v08/results/integrated_motion.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],flush=True)

if __name__=='__main__':main()
