"""Keep the small shared-path purpose separate from historical hardware reports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((ROOT/name).read_text())

spec=read('analysis/compact_layout_v08/contract.json')
base=read('cad/parameters/baseline.json')
donor=read(spec['current_donor_policy'])
feed=read('analysis/process_feed/feed_parameters.json')
assert read('cad/parameters/final_v08.json')['architecture']=='compact_single_path'
assert sum(base['extruder']['heater_zone_power_w'])+base['extruder']['die_heater_power_w']==spec['process_heater_power_w']==360
assert donor['psu']['controller_continuous_limit_w']==spec['machine_continuous_cap_w']==500
assert donor['psu']['increase_controller_limit'] is False
assert feed['control']['target_feed_g_h']==100
assert donor['donor_printer']['model']=='Anycubic Chiron'
assert spec['historical_cash_target_not_reinstated'] is True
assert all(a<=b for a,b in zip(spec['candidate_envelope_mm'],base['limits']['target_envelope_mm']))
assert all(spec[k] is True for k in ('no_extra_profiles_or_actuators','no_smaller_guard_or_hot_clearance','no_heater_or_psu_upsizing'))
assert all(spec[k] is False for k in ('fabrication_authorized','energization_authorized','canonical_geometry_promoted'))
assert spec['physical_validation_state']=='NOT_RUN'
print('COMPACT_PURPOSE_CONTRACT_PASS same_path no_power_increase nominal_100_stretch_200 review_only')
