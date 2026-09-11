#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'control/thermal_barrier_tape_contract.json'
def validate(path:Path=DEFAULT)->dict:
    d=json.loads(path.read_text(encoding='utf-8'))
    if d.get('part_id')!='TH-INS-01' or d.get('safety_role')!='NONE': raise ValueError('TH-INS-01 identity/safety-role drift')
    if d.get('state')!='RECEIVED_UNQUALIFIED': raise ValueError('received tape must remain unqualified until evidence passes')
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
