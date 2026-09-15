"""Candidate-only linear solid guide screen, not a contact or machine approval."""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'analysis/final_validation')]
from run_calculix_v08 import mesh_step, read_gmsh_inp, nset, solve, printed_reactions
CONTRACT = Path(__file__).with_name('contract.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exterior_faces(elements):
    faces = defaultdict(list)
    for line in elements:
        v = [int(x) for x in line.split(',')]
        if len(v) != 5 or len(set(v[1:])) != 4:
            raise ValueError('nondegenerate C3D4 connectivity required')
        tet = v[1:]
        for local in ((0,1,2),(0,3,1),(1,3,2),(2,3,0)):
            face = tuple(tet[i] for i in local)
            faces[tuple(sorted(face))].append(face)
    if any(len(v) > 2 for v in faces.values()):
        raise ValueError('nonmanifold tetrahedral mesh')
    return [v[0] for v in faces.values() if len(v) == 1]


def load_patch(nodes, elements, spec, direction=-1):
    force = spec['proof_load_n']
    angle = spec['contact_patch_half_angle_deg']
    if direction not in (-1,1) or isinstance(force,bool) or not math.isfinite(force) or force <= 0:
        raise ValueError('invalid proof load')
    if not math.isfinite(angle) or not 0 < angle < 90:
        raise ValueError('invalid bore patch angle')
    radius = spec['candidate_front_bore_mm']/2
    centre = spec['candidate_front_plate_x_mm'] + 4
    fixed = [n for n,(x,y,z) in nodes.items() if 340-1e-6 <= z <= 348+1e-6
        and min(abs(math.hypot(x-x0,y-centre)-3.3) for x0 in (257.,387.)) < .08]
    weights = defaultdict(float)
    for face in exterior_faces(elements):
        pts = np.asarray([nodes[n] for n in face]); cross = np.cross(pts[1]-pts[0],pts[2]-pts[0])
        area = float(np.linalg.norm(cross))/2
        if not math.isfinite(area) or area <= 1e-12:
            raise ValueError('zero-area boundary facet')
        if abs(cross[1])/(2*area) > .1:
            continue
        if max(abs(math.hypot(p[0]-320,p[2]-382)-radius) for p in pts) > .08:
            continue
        if direction*(float(pts[:,2].mean())-382) < radius*math.cos(math.radians(angle)):
            continue
        for node in face:
            weights[node] += area/3
    if len(fixed) < 12 or len(weights) < 6:
        raise ValueError('insufficient bore or fixing-surface mesh selection')
    total = sum(weights.values())
    forces = {n:direction*force*w/total for n,w in weights.items()}
    xyz = {n:tuple(v/1000 for v in p) for n,p in nodes.items()}
    applied = np.array([0.,0.,sum(forces.values())])
    moment = sum((np.cross(xyz[n],[0.,0.,f]) for n,f in forces.items()),np.zeros(3))
    return fixed,forces,xyz,dict(force_n=applied.tolist(),moment_nm=moment.tolist(),
        patch_area_mm2=total,loaded_nodes=len(weights),fixed_nodes=len(fixed),
        direction=direction,load_scope='area-weighted vertical bore resultant; not contact pressure')


def make_deck(nodes,elements,spec,direction=-1):
    fixed,forces,xyz,applied = load_patch(nodes,elements,spec,direction)
    deck = ['*HEADING','PPR isolated candidate guide, SI m N Pa',
        '*NODE',*(f'{n},{x:.12g},{y:.12g},{z:.12g}' for n,(x,y,z) in xyz.items()),
        '*ELEMENT,TYPE=C3D4,ELSET=ALL',*elements,*nset('REACTION',fixed),
        '*SOLID SECTION,ELSET=ALL,MATERIAL=STEEL','', '*MATERIAL,NAME=STEEL',
        '*ELASTIC',f"{spec['young_pa']:.12g},{spec['poisson']}",
        '*BOUNDARY','REACTION,1,3,0','*STEP','*STATIC','0.1,1.0','*CLOAD',
        *(f'{n},3,{f:.12g}' for n,f in forces.items()),
        '*NODE PRINT,NSET=REACTION','RF','*NODE FILE','U,RF','*EL FILE','S','*END STEP','']
    return '\n'.join(deck),applied,{n:xyz[n] for n in fixed}


def equilibrium(applied,reaction):
    force = np.asarray(applied['force_n']) + reaction['force_n']
    moment = np.asarray(applied['moment_nm']) + reaction['moment_about_origin_nm']
    return dict(force_residual_n=force.tolist(),moment_residual_nm=moment.tolist(),
        passed=bool(max(abs(force))<.002 and max(abs(moment))<.002))


def main():
    spec = json.loads(CONTRACT.read_text())
    gp = ROOT/'analysis/radial_support_v08/results/geometry.json'
    geometry = json.loads(gp.read_text())
    if geometry.get('unexpected_count') != 0 or not geometry.get('canonical_params_unchanged'):
        raise ValueError('unverified candidate geometry')
    hashes = dict(geometry['source_sha256'])
    for p in (CONTRACT,gp,Path(__file__).resolve(),ROOT/'analysis/final_validation/run_calculix_v08.py',
              ROOT/'analysis/structural/run_load_checks.py'):
        hashes[str(p.relative_to(ROOT))] = sha(p)
    step = ROOT/geometry['step_file']
    hashes[geometry['step_file']] = geometry['step_sha256']
    if not all((ROOT/p).is_file() and sha(ROOT/p)==d for p,d in hashes.items()):
        raise ValueError('candidate input hash mismatch')
    out = ROOT/'.build/pr-digital-continuation-20260915/plate-raw'
    out.mkdir(parents=True,exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix='run-',dir=out))
    rows = []
    for size in spec['fea_mesh_mm']:
        folder = run_dir/f'mesh-{size:g}'; folder.mkdir()
        mesh = mesh_step(step,folder,size)
        nodes,elements = read_gmsh_inp(mesh)
        for direction in (-1,1):
            case = folder/f'load-{direction}'; case.mkdir()
            deck,applied,coords = make_deck(nodes,elements,spec,direction)
            result = solve(case,deck)
            reaction = printed_reactions(case/'model.dat',coords)
            balance = equilibrium(applied,reaction)
            row = dict(mesh_mm=size,direction=direction,nodes=len(nodes),elements=len(elements),
                applied=applied,result=result,reaction=reaction,equilibrium=balance,
                raw_dir=str(case.relative_to(ROOT)),raw_sha256={p.name:sha(p) for p in
                (case/'model.inp',case/'model.dat',case/'model.frd',case/'ccx.log')})
            rows.append(row)
            print('GUIDE_SOLID_CASE',size,direction,result,balance,flush=True)
    refinements = []
    for direction in (-1,1):
        selected = [r for r in rows if r['direction']==direction]
        medium,fine = selected[-2:]
        ratio = abs(fine['result']['max_displacement_mm']-medium['result']['max_displacement_mm'])/fine['result']['max_displacement_mm']
        stress_ratio = abs(fine['result']['max_von_mises_mpa']-medium['result']['max_von_mises_mpa'])/fine['result']['max_von_mises_mpa']
        refinements.append(dict(direction=direction,displacement_relative_change=ratio,
            peak_stress_relative_change=stress_ratio,
            displacement_converged=ratio<=spec['displacement_convergence_fraction']))
    checks = dict(six_solve_cases=len(rows)==6,all_equilibrium=all(r['equilibrium']['passed'] for r in rows),
        stiffness_convergence=all(r['displacement_converged'] for r in refinements),
        sources_unchanged=all(sha(ROOT/p)==d for p,d in hashes.items()))
    peak = max(r['result']['max_von_mises_mpa'] for r in rows)
    report = dict(status='GUIDE_SOLID_NUMERICAL_REVIEW_PASS' if all(checks.values()) else 'FAIL',
        checks=checks,meshes=rows,refinement=refinements,source_sha256=hashes,
        conditional_peak_sf=spec['conditional_yield_mpa']/peak,
        strength_qualified=False,contact_qualified=False,canonical_geometry_promoted=False,
        physical_validation_state='NOT_RUN',fabrication_authorized=False,energization_authorized=False,
        limitations=['Linear C3D4, ideal fixed hole surfaces and imposed distributed bore load.',
            'Peak nodal stress includes fixed-edge and sharp-corner singularities; not a strength qualification.',
            'No barrel contact, bolt preload, rail compliance, thermal alignment, fatigue or full machine dynamics.'])
    result_path = ROOT/'analysis/radial_support_v08/results/plate_fea.json'
    result_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(report['status'],checks,flush=True)
    if not all(checks.values()): raise SystemExit(1)


if __name__ == '__main__':
    main()
