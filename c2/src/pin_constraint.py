"""Profile validity and full-orbit roller clearance for a compact cycloid candidate."""
from __future__ import annotations
import math
import numpy as np
from shapely.geometry import Polygon
import shapely
from engineering import S2, packaging


def profile(R: float, e: float, pins: int, roller_r: float = 8,
            allowance: float = .2, samples: int = 2880):
    u=np.linspace(0,2*np.pi,samples,endpoint=False)
    p=np.c_[R*np.cos(u)-e*np.cos(pins*u),R*np.sin(u)-e*np.sin(pins*u)]
    d=np.c_[-R*np.sin(u)+e*pins*np.sin(pins*u),R*np.cos(u)-e*pins*np.cos(pins*u)]
    norm=np.linalg.norm(d,axis=1)
    if norm.min()<1e-8:
        raise ValueError('Cycloid generating curve is singular')
    return p+(roller_r+allowance)*np.c_[-d[:,1],d[:,0]]/norm[:,None]


def verify(c: S2, positions: int = 721, profile_samples: int = 2880):
    pack=packaging(c)
    R=max(72.,pack['pin_pitch_radius_screen_mm']) if c.candidate_id=='C1-SEED' else pack['pin_pitch_radius_screen_mm']
    N=c.ratio_denominator+1
    pp=profile(R,c.eccentric_mm,N,samples=profile_samples)
    poly=Polygon(pp)
    if not poly.is_valid:
        return dict(candidate_id=c.candidate_id,valid_profile=False,passed=False,
                    reason='OFFSET_PROFILE_SELF_INTERSECTION',pin_R_mm=R)
    a=np.linspace(0,2*np.pi,N,endpoint=False)
    fixed=R*np.c_[np.cos(a),np.sin(a)]
    gap=math.inf
    # q-fold guide and N-fold pin symmetries let one orbit cover unlabeled contact pairs.
    for th in np.linspace(0,2*np.pi,positions):
        p=fixed-c.eccentric_mm*np.array([np.cos(th),np.sin(th)])
        ph=th/c.ratio_denominator
        rot=np.array([[np.cos(ph),-np.sin(ph)],[np.sin(ph),np.cos(ph)]])
        p=p@rot.T
        pts=shapely.points(p)
        d=shapely.distance(pts,poly.exterior)
        d=np.where(shapely.contains(poly,pts),-d,d)-8.
        gap=min(gap,float(d.min()))
    return dict(candidate_id=c.candidate_id,valid_profile=True,passed=gap>=0,
                minimum_sampled_pin_clearance_mm=gap,pin_R_mm=R,
                fixed_pins=N,lobes=N-1,profile_samples=profile_samples,orbit_positions=positions,
                evidence='KINEMATIC_CLEARANCE_NOT_CONTACT_STRESS_OR_WEAR',
                pin_plate_od_mm=2*(R+13),
                backlash_and_contact_capacity='NOT_QUALIFIED')
