"""미채택 다이 볼트 금속 spacer 후보. 실제 구매품/예압 qualification 아님."""
import hashlib
import json
import math
import sys
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'cad/freecad/compact'))
from geometry import down_die_body


def main():
    thickness = 2.5
    seat = 5-thickness
    die = down_die_body()
    spacers, bolts = [], []
    for degrees in (45,135,225,315):
        a = math.radians(degrees)
        y,z = 13*math.cos(a),13*math.sin(a)
        axis = App.Vector(1,0,0)
        spacer = Part.makeCylinder(3.75,thickness,App.Vector(seat,y,z),axis).cut(
            Part.makeCylinder(2.15,thickness,App.Vector(seat,y,z),axis))
        bolt = Part.makeCylinder(2,45,App.Vector(seat,y,z),axis).fuse(
            Part.makeCylinder(3.5,4,App.Vector(seat-4,y,z),axis))
        assert spacer.isValid() and len(spacer.Solids)==1
        assert bolt.isValid() and len(bolt.Solids)==1
        assert die.common(spacer).Volume < 1e-6 and die.common(bolt).Volume < 1e-6
        assert spacer.common(bolt).Volume < 1e-6
        spacers.append(spacer); bolts.append(bolt)
    folder = ROOT/'analysis/final_validation/results/v0.8'
    step = folder/'die_bolt_spacer_2p5_candidate.step'
    Part.makeCompound(spacers+bolts).exportStep(str(step))
    restored = Part.read(str(step))
    assert restored.isValid() and len(restored.Solids)==8
    volume = sum(shape.Volume for shape in spacers+bolts)
    assert abs(restored.Volume-volume)/volume < 1e-6
    penetration = [45-(35+gasket+thickness) for gasket in (.53,.25)]
    assert 0 < min(penetration) < max(penetration) < 8
    # Sensitivity only: these radii are not a supplier bolt specification.
    bolt = bolts[0].removeSplitter()
    neck = [edge for edge in bolt.Edges
            if abs(getattr(edge.Curve,'Radius',0)-2)<1e-8
            and abs(edge.CenterOfMass.x-seat)<1e-8]
    assert len(neck)==1
    center = App.Vector(seat,13/math.sqrt(2),13/math.sqrt(2))
    chamfer = .2
    relieved = spacers[0].cut(Part.makeCone(2.15+chamfer,2.15,chamfer,
                                          center,App.Vector(1,0,0)))
    assert relieved.isValid() and len(relieved.Solids)==1
    assert 0 < relieved.Volume < spacers[0].Volume
    relieved_step = folder/'die_bolt_spacer_2p5_chamfer_candidate.step'
    relieved.exportStep(str(relieved_step))
    restored_relief = Part.read(str(relieved_step))
    assert restored_relief.isValid() and len(restored_relief.Solids)==1
    assert abs(restored_relief.Volume-relieved.Volume)/relieved.Volume < 1e-6
    fillet_sensitivity = []
    for radius in (.1,.15,.2,.3):
        rounded = bolt.makeFillet(radius,neck)
        assert rounded.isValid() and len(rounded.Solids)==1
        interference = rounded.common(spacers[0]).Volume
        assert interference < 1e-6 if radius <= .15 else interference > 1e-4
        relieved_interference = rounded.common(relieved).Volume
        assert relieved_interference < 1e-6
        fillet_sensitivity.append({'assumed_radius_mm':radius,
                                   'spacer_interference_mm3':interference,
                                   'chamfered_spacer_interference_mm3':relieved_interference})
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from generate import final_objects
    from check_retainer_tool_access import overlaps
    assembly = {item['name']:item['shape'] for item in final_objects()}
    access = []
    for degrees in (45,135,225,315):
        angle = math.radians(degrees)
        y,z = 347+13*math.cos(angle),382+13*math.sin(angle)
        head_front = 54.5+seat-4
        envelopes = {
            'head':Part.makeCylinder(3.5,4,App.Vector(head_front,y,z),App.Vector(1,0,0)),
            'driver_shaft':Part.makeCylinder(2,50,App.Vector(head_front-50,y,z),App.Vector(1,0,0)),
            'driver_handle':Part.makeCylinder(15,80,App.Vector(head_front-130,y,z),App.Vector(1,0,0))}
        access.append({'angle_deg':degrees,'overlaps':{name:overlaps(shape,assembly) for name,shape in envelopes.items()}})
    result = {'status':'HOLD','physical_validation_state':'NOT_RUN',
              'spacer_candidate_mm':{'od':7.5,'id':4.3,'thickness':thickness,'quantity':4},
              'assumed_bolt_envelope_mm':{'shank_diameter':4,'length':45,'head_diameter':7,'head_height':4},
              'penetration_range_mm':penetration,'head_front_projection_mm':4-seat,
              'unverified_neck_fillet_sensitivity':fillet_sensitivity,
              'chamfer_candidate':{'entrance_chamfer_mm':chamfer,'angle_deg':45,
                  'entrance_diameter_mm':4.3+2*chamfer,
                  'bearing_annulus_assuming_dw_6p53_mm2':math.pi/4*(6.53**2-(4.3+2*chamfer)**2),
                  'same_force_pressure_ratio_vs_unchamfered':(6.53**2-4.3**2)/(6.53**2-(4.3+2*chamfer)**2),
                  'step_sha256':hashlib.sha256(relieved_step.read_bytes()).hexdigest()},
              'assembly_access':access,
              'tool_envelope_mm':{'shaft_diameter':4,'shaft_length':50,'handle_diameter':30,'handle_length':80,'minimum_global_x':head_front-130},
              'scope':'Nominal die-only clearance; ideal bolt envelope not verified purchase. Spacer material/hardness/parallelism, bolt/head/chamfer tolerances, thread runout and tip, hot preload and full assembly/tool access unqualified.',
              'step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (Path(__file__).resolve(),ROOT/'cad/freecad/compact/geometry.py',
                            Path(__file__).with_name('generate.py'),Path(__file__).with_name('check_retainer_tool_access.py'),
                            ROOT/'cad/parameters/final_v08.json')}}
    (folder/'die_bolt_spacer_2p5_candidate.json').write_text(json.dumps(result,indent=2)+'\n')
    print('DIE_BOLT_SPACER_CANDIDATE_HOLD',penetration)


if __name__ == '__main__':
    main()
