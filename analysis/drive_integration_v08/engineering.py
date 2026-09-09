"""Bounded drive load calculations; no material/gearbox acceptance inferred."""
from pathlib import Path
import json,math,hashlib
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def calculate(c):
    sh=c['shredder']; p=c['protection']; t=p['mechanical_release_acceptance_nm'][1]
    radius=sh['chain_pitch_mm']/1000/(2*math.sin(math.pi/12))
    force=t/radius+2*sh['slack_side_tension_assumption_n']
    span=(sh['bearing_centres_mm'][1]-sh['bearing_centres_mm'][0])/1000
    a=(sh['pinion_midplane_mm']-sh['bearing_centres_mm'][0])/1000; b=span-a
    ra=force*b/span; rb=force*a/span; moment=force*a*b/span
    d=.012; bending=32*moment/(math.pi*d**3)/1e6; shear=16*t/(math.pi*d**3)/1e6
    vm=math.sqrt(bending*bending+3*shear*shear); kt=1.8
    keys=[{'engagement_mm':l,'shear_mpa':2*t/(.012*.004*(l/1000))/1e6,
           'bearing_mpa':4*t/(.012*.004*(l/1000))/1e6} for l in (15,17,20,22)]
    necks=[math.sqrt(4*tq/(math.pi*.016*120e6))*1000 for tq in p['mechanical_release_acceptance_nm']]
    drive=c['power']; peak=24*drive['main_drive_reserve_a']+drive['driver_loss_reserve_w']+drive['auxiliary_reserve_w']+drive['running_heater_cap_w']
    I=math.pi*d**4/64; deflection=force*a*a*b*b/(3*200e9*I*span)*1000
    rail_a=.133; rail_b=.297; rail_L=.430
    rail_values={str(Icm4):force*rail_a**2*rail_b**2/(3*69e9*Icm4*1e-8*rail_L)*1000 for Icm4 in (.87,5.41)}
    return {'rail_deflection_reference_mm':rail_values,'rail_load_bound_n':force,'reference_plane':'gearbox output before2.5 chain; screw direct',
      'pinion_radius_mm':radius*1000,'chain_radial_load_n':force,'bearing_reactions_n':[ra,rb],
      'jackshaft_moment_nm':moment,'jackshaft_vm_mpa':vm,'screened_local_vm_mpa':kt*vm,
      'required_room_temp_yield_mpa_at_factor2':2*kt*vm,'jackshaft_deflection_mm':deflection,
      'assumed_shaft_yield_mpa':300,'conditional_shaft_factor':300/(kt*vm),
      'key_checks':keys,'pin_neck_screen_mm':necks,'pin_shear_strength_assumption_mpa':120,
      'pin_blank_installable':False,'bearing_static_capacity_reference_n':3050,
      'bearing_static_load_ratio_reference':3050/max(ra,rb),'bearing_reference_not_alternate_brand_approval':True,
      'peak_dc_power_w':peak,'power_margin_w':drive['control_cap_w']-peak,
      'protection_order_pass':p['command_limit_gearbox_nm']+p['assumed_calibration_error_nm']<p['mechanical_release_acceptance_nm'][0]<t<c['motor']['gearbox_limit_nm'],
      'physical_validation':'NOT_RUN','calibration_and_release_coupon_required':True}

def main():
    path=ROOT/'control/ggm_drive_contract.json'; c=json.loads(path.read_text()); r=calculate(c)
    r['assumptions']=['S45C room-temperature yield300MPa must match supplied condition','Kt1.8 is a screening factor, not a notch FEA result','Chain slack tension20N per side is an assembly bound to check','NSK6201 reference rating is not approval of any unmarked donor bearing','Pin release range is an acceptance target, not a proven property of a3mm blank']
    r['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),path)}
    r['status']='DIGITAL_SCREEN_PASS_WITH_COMMISSIONING_REQUIRED' if r['conditional_shaft_factor']>=2 and r['power_margin_w']>=0 and r['protection_order_pass'] else 'FAIL'
    (HERE/'engineering.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
if __name__=='__main__': main()
