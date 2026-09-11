#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'control/thermal_barrier_tape_contract.json'
def validate(path:Path=DEFAULT)->dict:
    d=json.loads(path.read_text(encoding='utf-8'))
    if d.get('part_id')!='TH-INS-01' or d.get('safety_role')!='NONE': raise ValueError('TH-INS-01 identity/safety-role drift')
    if d.get('state')!='RECEIVED_IDENTITY_CLAIM_RECORDED_S4_PENDING': raise ValueError('received tape identity state drift')
    rp=d.get('received_product',{}); basis=d.get('design_basis',{})
    if rp.get('width_mm')!=25.0 or rp.get('roll_length_m')!=30.0: raise ValueError('received tape dimension claim drift')
    if rp.get('claimed_long_term_temperature_range_c')!=[220.0,280.0] or rp.get('claimed_short_term_temperature_c')!=300.0: raise ValueError('received tape temperature claim drift')
    if rp.get('adhesive_chemistry')!='NOT_SPECIFIED_BY_LISTING': raise ValueError('tape adhesive evidence drift')
    if basis.get('continuous_service_rating_c')!=220.0 or basis.get('required_operating_margin_c')!=30.0 or basis.get('max_interface_peak_plus_u95_c')!=190.0: raise ValueError('tape conservative design basis drift')
    place=d.get('placement',{}); forbidden=' '.join(place.get('forbidden',[]))
    for token in ('heater band','barrel or die','TF-BARREL','T1-T5','electrical terminals','ventilation'):
        if token not in forbidden: raise ValueError('missing forbidden placement: '+token)
    p9=d.get('installed_p9_acceptance',{})
    if p9.get('continuous_rating_margin_c')!=30.0 or p9.get('edge_lift_after_cooldown_max_mm')!=2.0: raise ValueError('tape P9 limit drift')
    a=d.get('authorization',{})
    if a.get('installation_authorized') is not False or a.get('heater_energization_authorized') is not False or a.get('machine_release')!='HOLD': raise ValueError('tape contract authorization drift')
    if d.get('coupon_smoke',{}).get('required_before_final_hot_zone_use') is not True: raise ValueError('coupon smoke must remain required')
    return {'status':'THERMAL_BARRIER_TAPE_CONTRACT_PASS','part_id':'TH-INS-01','safety_role':'NONE','installation_authorized':False,'machine_release':'HOLD'}
def main(): print(json.dumps(validate(),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
