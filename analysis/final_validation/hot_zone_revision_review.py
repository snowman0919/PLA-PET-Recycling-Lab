#!/usr/bin/env python3
"""Geometry-bound hot-zone delta screens; not physical qualification."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/final_validation/results/v0.8/hot_zone_revision_review.json'
SOURCES = ['cad/parameters/baseline.json', 'cad/parameters/final_v08.json',
           'cad/freecad/compact/geometry.py', 'cad/freecad/final_v08/generate.py',
           'cad/freecad/drive_v08/assembly.py']
import sys
sys.path.insert(0,str(ROOT))
from analysis.thermal_revision_v08.model import ASSUMPTIONS, thermal_screen


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_geometry():
    base = json.loads((ROOT / SOURCES[0]).read_text())['extruder']
    mount = json.loads((ROOT / SOURCES[1]).read_text())['hot_zone_mount']
    return base, mount


def beam_screen(supports_m, od_m, id_m, elements=56, tip_force_n=25.0):
    length = ASSUMPTIONS['barrel_length_mm'] / 1000
    if not (0 < id_m < od_m and elements >= 4 and len(supports_m)==2 and 0 <= supports_m[0] < supports_m[1] <= length):
        raise ValueError("Invalid annular beam or support geometry")
    xs = np.unique(np.r_[np.linspace(0, length, elements+1), supports_m])
    area = math.pi * (od_m**2-id_m**2)/4
    inertia = math.pi * (od_m**4-id_m**4)/64
    rho, young = ASSUMPTIONS['steel_density_kg_m3'], ASSUMPTIONS['young_pa']
    size = 2*len(xs)
    stiffness, mass, load = np.zeros((size,size)), np.zeros((size,size)), np.zeros(size)
    for i, ell in enumerate(np.diff(xs)):
        dof = np.arange(2*i, 2*i+4)
        ke = young*inertia/ell**3*np.array([[12,6*ell,-12,6*ell],
            [6*ell,4*ell**2,-6*ell,2*ell**2],[-12,-6*ell,12,-6*ell],
            [6*ell,2*ell**2,-6*ell,4*ell**2]])
        me = rho*area*ell/420*np.array([[156,22*ell,54,-13*ell],
            [22*ell,4*ell**2,13*ell,-3*ell**2],[54,13*ell,156,-22*ell],
            [-13*ell,-3*ell**2,-22*ell,4*ell**2]])
        stiffness[np.ix_(dof,dof)] += ke
        mass[np.ix_(dof,dof)] += me
        load[dof] -= rho*area*9.80665*ell/2*np.array([1,ell/6,1,-ell/6])
    load[-2] -= tip_force_n
    fixed = [2*int(np.argmin(abs(xs-s))) for s in supports_m]
    free = np.setdiff1d(np.arange(size), fixed)
    k, m = stiffness[np.ix_(free,free)], mass[np.ix_(free,free)]
    displacement = np.zeros(size)
    displacement[free] = np.linalg.solve(k, load[free])
    reaction = stiffness@displacement-load
    chol = np.linalg.cholesky(m)
    reduced = np.linalg.solve(chol, k)
    reduced = np.linalg.solve(chol, reduced.T).T
    eigen = np.linalg.eigvalsh((reduced+reduced.T)/2)
    if eigen[0] <= 0:
        raise ValueError('Unconstrained or nonpositive beam mode')
    force_residual = float(sum(reaction[fixed])+sum(load[::2]))
    moment_residual = float(sum(reaction[fixed]*xs[np.array(fixed)//2])
                            +sum(load[::2]*xs)+sum(load[1::2]))
    a, b = supports_m
    distributed = rho*area*9.80665
    rb = (distributed*length*(length/2-a)+tip_force_n*(length-a))/(b-a)
    ra = distributed*length+tip_force_n-rb
    reactions_exact = np.array([ra, rb])
    reaction_error = float(max(abs(reaction[fixed]-reactions_exact)))
    return dict(supports_mm=[s*1000 for s in supports_m], elements=len(xs)-1,
        max_deflection_mm=float(max(abs(displacement[::2]))*1000),
        first_bending_hz=float(math.sqrt(eigen[0])/(2*math.pi)),
        reactions_n=[float(reaction[i]) for i in fixed],
        reaction_error_n=reaction_error, force_residual_n=force_residual,
        moment_residual_nm=moment_residual, tip_force_n=tip_force_n)


def main():
    from analysis.thermal_revision_v08.compare import run
    run(beam_screen)

if __name__ == '__main__': main()
