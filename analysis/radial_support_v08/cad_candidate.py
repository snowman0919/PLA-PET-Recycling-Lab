"""Explicit review geometry, separate from canonical manufacturing generators."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'cad/freecad/drive_v08')]
from cad.freecad.final_v08 import generate as final
from cad.freecad.drive_v08.assembly import integrated_objects
from cad.freecad.compact.generate import normalize_step
from validation.integrated_assembly_clearance import audit, geometry_source_paths
from validation.integrated_motion_clearance import contact_area
CONTRACT=Path(__file__).resolve().with_name('contract.json')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def build_candidate():
    spec=json.loads(CONTRACT.read_text())
    original=copy.deepcopy(final.PARAMS); original_plate=final.mount_plate
    x=spec['candidate_front_plate_x_mm']; side=spec['candidate_side_window']
    def guide(xpos, sliding):
        shape=original_plate(xpos,sliding)
        if not sliding: return shape
        shape=shape.fuse(Part.makeBox(8,54,18,App.Vector(xpos,320,398)))
        shape=shape.cut(Part.makeCylinder(spec['candidate_front_bore_mm']/2,8,
                         App.Vector(xpos,347,382),App.Vector(1,0,0)))
        shape=shape.cut(Part.makeBox(8,70,side['height_mm'],
                         App.Vector(xpos,side['y_min_mm'],side['z_min_mm'])))
        return shape.removeSplitter()
    try:
        final.PARAMS=copy.deepcopy(original)
        final.PARAMS['hot_zone_mount'].update(front_sliding_plate_x_mm=x,
            sliding_guide_bore_mm=spec['candidate_front_bore_mm'])
        final.mount_plate=guide
        rows,_=integrated_objects(final.final_objects())
        rail=next(r for r in rows if r['name']=='MidRail320')
        rail['shape']=rail['shape'].copy()
        delta=x-original['hot_zone_mount']['front_sliding_plate_x_mm']
        rail['shape'].translate(App.Vector(0,delta,0))
    finally:
        final.PARAMS=original; final.mount_plate=original_plate
    return rows


def validate_candidate(rows):
    by={r['name']:r['shape'] for r in rows}
    result=audit(rows)
    guide=by['ExtruderFrontSlidingGuide']; rail=by['MidRail320']
    gaps={name:guide.distToShape(by[name])[0] for name in
        ('TemperatureProbeT3','TemperatureProbeRetainerT3','BarrelBandHeaterZ3')}
    minimum={'TemperatureProbeT3':5.,'TemperatureProbeRetainerT3':3.,'BarrelBandHeaterZ3':6.}
    if any(gaps[name]+1e-6<limit for name,limit in minimum.items()):
        raise ValueError('candidate service clearance below declared minimum')
    cooling=rail.distToShape(by['PPR-C05_CoolingDuctUpper'])[0]
    if cooling < 4.-1e-6: raise ValueError('cooling-duct clearance')
    contacts={name:contact_area(rail,by[name]) for name in
              ('FrameTierY320_0','FrameTierY320_450')}
    contacts['guide_to_rail']=contact_area(guide,rail)
    if min(contacts.values()) < 399.9: raise ValueError('floating relocated support')
    for travel in (-1.5,0.,1.5):
        barrel=by['Barrel'].copy(); barrel.translate(App.Vector(0,travel,0))
        if guide.common(barrel).Volume > .01: raise ValueError('axial slide obstructed')
    result.update(cad_stations_mm=dict(barrel_rear_y=by['Barrel'].BoundBox.YMax, barrel_die_y=by['Barrel'].BoundBox.YMin, rear_plate_y=by['ExtruderRearFixedDatum'].BoundBox.Center.y, candidate_front_y=guide.BoundBox.Center.y, rear_lip_top_z=by['ExtruderRearFixedDatum'].BoundBox.ZMax),
        service_gaps_mm=gaps,rail_to_cooling_mm=cooling,
        support_face_contacts_mm2=contacts,axial_slide_mm=[-1.5,1.5],
        design_state='REVIEW_CANDIDATE_NOT_ACTIVE_MACHINE',
        assembly_sequence='Axial insertion before die; heater bands positioned beyond the guide first; TC3 installed through lateral window',
        thermal_alignment_verified=False,load_capacity_verified=False)
    return result


def main():
    paths=geometry_source_paths()+[Path(__file__).resolve(),CONTRACT,
        ROOT/'validation/integrated_assembly_clearance.py',ROOT/'validation/integrated_motion_clearance.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    canonical=sha(ROOT/'cad/parameters/final_v08.json')
    items=build_candidate(); report=validate_candidate(items)
    folder=ROOT/'exports/review/radial_support_v08';folder.mkdir(parents=True,exist_ok=True)
    guide=next(r['shape'] for r in items if r['name']=='ExtruderFrontSlidingGuide')
    step=folder/'RS-FRONT-GUIDE-CANDIDATE.step';guide.exportStep(str(step));normalize_step(step)
    imported=Part.read(str(step))
    if not imported.isValid() or len(imported.Solids)!=1:
        raise ValueError('candidate STEP invalid')
    if max(guide.cut(imported).Volume,imported.cut(guide).Volume)>.01:
        raise ValueError('candidate STEP shape roundtrip mismatch')
    report.update(source_sha256=hashes,step_file=str(step.relative_to(ROOT)),
        step_sha256=sha(step),canonical_params_unchanged=sha(ROOT/'cad/parameters/final_v08.json')==canonical,
        physical_validation_state='NOT_RUN',fabrication_authorized=False,energization_authorized=False)
    if not all(sha(ROOT/p)==value for p,value in hashes.items()):
        raise ValueError('source changed during geometry review')
    output=ROOT/'analysis/radial_support_v08/results/geometry.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('RADIAL_SUPPORT_CANDIDATE_GEOMETRY_PASS',json.dumps({k:report[k] for k in
        ('object_count','unexpected_count','service_gaps_mm','support_face_contacts_mm2','canonical_params_unchanged')}),flush=True)


if __name__=='__main__': main()
