"""Explicit free-body/contact screens; no physical or full-machine approval."""
from __future__ import annotations
import math


def finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not math.isfinite(value):
        raise ValueError('finite '+name+' required')
    return float(value)


def reactions(length_mm, rear_mm, front_mm, uniform_weight_n, tip_force_n):
    values = [finite(v,n) for v,n in zip(
        (length_mm,rear_mm,front_mm,uniform_weight_n,tip_force_n),
        ('length','rear','front','weight','tip load'))]
    length, rear, front, weight, tip = values
    if not 0 <= rear < front <= length or weight < 0 or tip < 0:
        raise ValueError('invalid support/load domain')
    forward = (weight*(length/2-rear)+tip*(length-rear))/(front-rear)
    backward = weight+tip-forward
    return dict(rear_n=backward, front_n=forward,
        force_residual_n=backward+forward-weight-tip,
        moment_residual_nmm=forward*(front-rear)-weight*(length/2-rear)-tip*(length-rear))


def capture_lift(bore_radius_mm, shaft_radius_mm, lip_height_mm):
    radius, shaft, height = [finite(v,'capture geometry') for v in
                            (bore_radius_mm,shaft_radius_mm,lip_height_mm)]
    if not 0 < height < radius or not 0 < shaft < radius:
        raise ValueError('invalid C-saddle dimensions')
    half_opening = math.sqrt(radius*radius-height*height)
    if shaft <= half_opening:
        raise ValueError('shaft can escape through throat')
    return height-math.sqrt(shaft*shaft-half_opening*half_opening)


def axis_at(x_mm, rear_mm, front_mm, rear_offset_mm, front_offset_mm):
    values = [finite(v,'axis input') for v in
              (x_mm,rear_mm,front_mm,rear_offset_mm,front_offset_mm)]
    x, rear, front, dz_rear, dz_front = values
    if front <= rear: raise ValueError('zero or reversed support span')
    return dz_rear+(dz_front-dz_rear)*(x-rear)/(front-rear)


def concave_hertz(force_n, contact_length_mm, shaft_radius_mm, bore_radius_mm,
                  young_pa=190e9, poisson=0.30):
    force, length, shaft, bore, young, nu = [finite(v,'contact input') for v in
        (force_n,contact_length_mm,shaft_radius_mm,bore_radius_mm,young_pa,poisson)]
    if min(force,length,shaft,young) <= 0 or bore <= shaft or not 0 <= nu < .5:
        raise ValueError('invalid compressive cylinder contact')
    effective_radius_m = 1/(1/(shaft/1000)-1/(bore/1000))
    effective_modulus = young/(2*(1-nu*nu))
    half_width_m = math.sqrt(4*force*effective_radius_m/(math.pi*(length/1000)*effective_modulus))
    peak_pa = 2*force/(math.pi*half_width_m*(length/1000))
    return dict(effective_radius_mm=effective_radius_m*1000,
        half_width_mm=half_width_m*1000, peak_pressure_mpa=peak_pa/1e6,
        scope='Smooth elastic line contact, not the sharp existing C-lip')


def seated_thermal_shift(centre_height_mm, bore_radius_mm, shaft_radius_mm,
                         support_c, shaft_c, support_alpha, shaft_alpha):
    h, bore, shaft, ts, tb, als, alb = [finite(v,'thermal seat input') for v in
        (centre_height_mm,bore_radius_mm,shaft_radius_mm,support_c,shaft_c,support_alpha,shaft_alpha)]
    if not 0 < shaft < bore < h or min(als,alb) < 0 or min(ts,tb) < 20:
        raise ValueError('invalid thermal seating domain')
    support_shift = (h-bore)*als*(ts-20)
    shaft_growth = shaft*alb*(tb-20)
    return support_shift+shaft_growth
