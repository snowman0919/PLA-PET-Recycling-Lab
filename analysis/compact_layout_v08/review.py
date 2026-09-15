"""Reuse current solids; review compact placement without changing fabrication CAD."""
import hashlib
import json
from pathlib import Path
import sys
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'cad/freecad/drive_v08')]
from validation.integrated_assembly_clearance import audit, geometry_source_paths
from validation.integrated_motion_clearance import contact_area, check_clear
CONTRACT = Path(__file__).resolve().with_name('contract.json')


def by_name(rows):
    out = {r['name']: r['shape'] for r in rows}
    if len(out) != len(rows):
        raise ValueError('duplicate object identity')
    return out


def dimensions(rows):
    boxes = [r['shape'].BoundBox for r in rows]
    return [max(getattr(b, a+'Max') for b in boxes) -
            min(getattr(b, a+'Min') for b in boxes) for a in 'XYZ']


def placement(rows, upper=(-18,29,0), support=(0,29,0)):
    out, transforms = [], {}
    for row in rows:
        delta = None
        if row['group'] in ('shredder', 'input'):
            delta = upper
        elif row['name'] in ('FlakeBin','MidRail500','GGM_ShredRail') or row['name'].startswith('PPR-C03_'):
            delta = support
        shape = row['shape'].copy()
        if delta is not None:
            shape.translate(App.Vector(*delta)); transforms[row['name']] = list(delta)
        out.append(dict(row, shape=shape))
    return out, transforms


def check_preserved(base, candidate, transforms):
    before, after = by_name(base), by_name(candidate)
    if set(before) != set(after):
        raise ValueError('component addition or omission')
    for row, other in zip(base, candidate):
        if any(row[k] != other[k] for k in ('name','material','classification','group')):
            raise ValueError('component definition changed')
        original = before[row['name']].copy()
        original.translate(App.Vector(*transforms.get(row['name'],(0,0,0))))
        actual = after[row['name']]
        if max(original.cut(actual).Volume, actual.cut(original).Volume) > 0.01:
            raise ValueError('not a rigid placement: '+row['name'])
    return len(before)


def check_supports(base, candidate):
    old, new = by_name(base), by_name(candidate); contacts = {}
    pairs = [(rail, side) for rail in ('GGM_ShredRail','MidRail500')
             for side in ('FrameTierY500_0','FrameTierY500_450')]
    pairs += [(f'GGM_SH_Spacer_{x}_{y}', rail) for x in (90,220)
              for y,rail in ((100,'GGM_ShredRail'),(280,'MidRail500'))]
    for left, right in pairs:
        original, actual = contact_area(old[left],old[right]), contact_area(new[left],new[right])
        if original < 1 or actual < original-0.01:
            raise ValueError('lost support face: '+left+'/'+right)
        contacts[left+'/'+right] = {'before_mm2':original,'after_mm2':actual}
    return contacts


def check_collection(candidate, minimum=5.0):
    shapes = by_name(candidate)
    screen, tray = (shapes[n].BoundBox for n in ('Screen','FlakeBin'))
    margins = [screen.XMin-tray.XMin-2, tray.XMax-screen.XMax-2,
               screen.YMin-tray.YMin-2, tray.YMax-screen.YMax-2]
    if min(margins) < minimum-1e-6 or screen.ZMin < tray.ZMax:
        raise ValueError('screen no longer projects inside collector')
    return {'inward_margins_mm':margins,'vertical_gap_mm':screen.ZMin-tray.ZMax,
            'scope':'Vertical projection only; particle rebound not modeled'}


def check_lid(candidate, spec):
    by = by_name(candidate); lid = by['PPR-C01_SlidingLid']; b = lid.BoundBox
    dx,dy,dz = spec['upper_translation_mm']
    mouth = Part.makeCylinder(spec['lid_mouth_radius_mm'],1,App.Vector(125+dx,395+dy,900+dz))
    if mouth.cut(lid).Volume > 0.01:
        raise ValueError('lid does not cover unchanged mouth')
    config = json.loads((ROOT/'cad/parameters/baseline.json').read_text())
    travel = config['input_lid']['service_travel_mm']
    sweep = Part.makeBox(b.XLength+travel,b.YLength,b.ZLength,App.Vector(b.XMin-travel,b.YMin,b.ZMin))
    check_clear(sweep,by,{'PPR-C01_SlidingLid'},'compact lid service sweep')
    return {'travel_mm':travel,'left_extent_mm':b.XMin-travel,
            'workspace_width_mm':470-(b.XMin-travel),'closed_mouth_covered':True}


def check_lower_motion(candidate):
    by=by_name(candidate)
    config=json.loads((ROOT/'cad/parameters/baseline.json').read_text())['spooler']
    carriage=by['PPR-C10_TraverseCarriage']; b=carriage.BoundBox; travel=config['traverse_mm']
    sweep=Part.makeBox(b.XLength,b.YLength+travel,b.ZLength,App.Vector(b.XMin,b.YMin,b.ZMin))
    check_clear(sweep,by,{'PPR-C10_TraverseCarriage','TraverseRodA','TraverseRodB'},'traverse sweep')
    from cad.freecad.compact.dancer_revision import moving_names
    names=moving_names()
    for angle in range(-25,26):
        for name in names:
            shape=by[name].copy()
            shape.rotate(App.Vector(*config['dancer_layout']['pivot_mm']),App.Vector(0,1,0),angle)
            check_clear(shape,by,names,'dancer sample')
    return {'continuous_traverse_envelope':True,'dancer_samples':51}


def compare_solids(left, right):
    remaining=list(right); missing_total=0.0; added_total=0.0
    if len(left)!=len(right):
        raise ValueError('STEP solid count differs')
    for solid in left:
        for index, other in enumerate(remaining):
            if (solid.CenterOfMass-other.CenterOfMass).Length>1e-5:
                continue
            missing,added=solid.cut(other),other.cut(solid)
            if not all(s.isNull() or s.isValid() for s in (missing,added)):
                continue
            if max(missing.Volume,added.Volume)<=0.01:
                missing_total+=missing.Volume; added_total+=added.Volume
                remaining.pop(index); break
        else:
            raise ValueError('STEP solid geometry differs')
    if remaining or max(missing_total,added_total)>0.01:
        raise ValueError('STEP accumulated geometry difference')
    return {'solids':len(left),'missing_total_mm3':missing_total,'added_total_mm3':added_total}


def main():
    from cad.freecad.final_v08.generate import final_objects
    from cad.freecad.drive_v08.assembly import integrated_objects
    from cad.freecad.compact.generate import normalize_step
    paths=geometry_source_paths()+[Path(__file__).resolve(),CONTRACT,
        ROOT/'validation/integrated_assembly_clearance.py',ROOT/'validation/integrated_motion_clearance.py']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    spec=json.loads(CONTRACT.read_text()); base,_=integrated_objects(final_objects())
    candidate, transforms=placement(base,tuple(spec['upper_translation_mm']),tuple(spec['support_and_collection_translation_mm']))
    before,after=dimensions(base),dimensions(candidate)
    if any(abs(a-b)>1e-5 for a,b in zip(before,spec['reference_envelope_mm'])):
        raise ValueError('reference layout drift')
    if any(abs(a-b)>1e-5 for a,b in zip(after,spec['candidate_envelope_mm'])):
        raise ValueError('candidate exceeds declared envelope')
    count=check_preserved(base,candidate,transforms)
    result={'status':'COMPACT_PLACEMENT_GEOMETRY_REVIEW_PASS','before_mm':before,'after_mm':after,
        'preserved_objects':count,'translations_mm':transforms,'static':audit(candidate),
        'supports':check_supports(base,candidate),'collection':check_collection(candidate,spec['screen_capture_margin_mm']),
        'lid':check_lid(candidate,spec),'lower_motion':check_lower_motion(candidate)}
    rejected,_=placement(base,(0,10,0),(0,10,0)); bad=by_name(rejected)
    result['rejected_simple_inset']={'translation_mm':[0,10,0],
        'pair':['SealedFeedHopper','GGM_SH_Post_238_313'],
        'overlap_mm3':bad['SealedFeedHopper'].common(bad['GGM_SH_Post_238_313']).Volume}
    folder=ROOT/'exports/review/compact_layout_v08'; folder.mkdir(parents=True,exist_ok=True)
    step=folder/'PPR-COMPACT-PLACEMENT-REVIEW.step'
    compound=Part.makeCompound([r['shape'] for r in candidate]); compound.exportStep(str(step)); normalize_step(step)
    imported=Part.read(str(step))
    if not imported.isValid() or len(imported.Solids)!=len(compound.Solids):
        raise ValueError('review STEP invalid')
    result['step_geometry_equivalence']=compare_solids(compound.Solids,imported.Solids)
    doc=App.newDocument('CompactPlacementReview')
    for row in candidate:
        feature=doc.addObject('PartDesign::Feature',row['name']); feature.Shape=row['shape']; feature.Label=row['name']
    doc.recompute(); native=folder/'PPR-COMPACT-PLACEMENT-REVIEW.FCStd'; doc.saveAs(str(native)); App.closeDocument(doc.Name)
    result.update(source_sha256=hashes,step_file=str(step.relative_to(ROOT)),
        step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),
        native_file=str(native.relative_to(ROOT)),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
        step_solids=len(imported.Solids),physical_validation_state='NOT_RUN',
        fabrication_authorized=False,energization_authorized=False,canonical_geometry_promoted=False,
        limitations=['Layout review only; final stations, BOM placement and release not promoted.',
        'No new parts or smaller clearances; footprint reduction is not a stiffness or safety certificate.',
        'Moved load attachment points require frame response and complete provenance regeneration before promotion.',
        'Collector projection does not prove fragment containment; lid rails/interlock details still open.',
        'Heat-transfer and radial-support problems are unchanged, not solved by this relocation.'])
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
        raise ValueError('source changed during review')
    output=Path(__file__).parent/'results/review.json'; output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['status'],json.dumps({k:result[k] for k in
        ('before_mm','after_mm','preserved_objects','collection','lid','step_solids')}),flush=True)


if __name__=='__main__': main()
