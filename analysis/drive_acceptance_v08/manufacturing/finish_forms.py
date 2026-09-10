"""Empty receiving and calibration packets, never fabricated measurement data."""
from pathlib import Path
import json,csv,hashlib
import inspection as I
H=Path(__file__).resolve().parent;R=H.parents[2]
OUT=R/'exports/final/drive_ggm_v08/manufacturing_r2'
def empty_meta():
    return dict(performed=False,kind='PHYSICAL_MEASUREMENT',operator=None,part_serial=None,
        instrument_id=None,instrument_calibration_ref=None,measured_at=None,raw_files={})
def readings(ranges):return {key:dict(value=None,u95=None,unit=u,design_min=a,design_max=b) for key,(a,b,u) in ranges.items()}
prereq=R/'validation/physical_v08/simulation_prerequisite.py'
packet={'record_status':'NOT_RUN','all_physical_actions_authorized':False,
  'simulation_prerequisite':{'source':'validation/physical_v08/simulation_prerequisite.py','required_status':'PASS',
    'runtime_status':'RUNTIME_CHECK_REQUIRED','source_sha256':hashlib.sha256(prereq.read_bytes()).hexdigest(),
    'note':'Runtime P0 status and snapshot hash are evaluated at the physical-stage check; the reusable template is not HEAD-bound.'},
  'design_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'control/ggm_drive_contract.json',H/'drawing_contract.json')}}
receipt={}
for axis,gear in (('SH','K9G75C'),('EX','K9G150C')):
    r=empty_meta();r.update(motor_model='K9DG60N2',gear_model=gear,readings=readings(I.RECEIPT));receipt[axis]=r
packet['receipt']={'performed':False,'data':receipt}
r=empty_meta();r.update(assembly_revision='GGM-MFG-v0.8-r2',readings=readings(I.ALIGN))
packet['alignment']={'performed':False,'data':r}
r=empty_meta();r['samples']=[];packet['protection_pin']={'performed':False,'data':r}
curr={}
for axis in ('SH','EX'):
    r=empty_meta();r.update(current_location='motor_lead',units={'current':'A','torque':'N.m','speed':'rpm','adc':'count'},
        adc_samples=[],no_load_a=[],torque_samples=[]);curr[axis]=r
packet['current_calibration']={'performed':False,'data':curr}
(H/'inspection_packet_template.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
report=I.inspect(packet)
(H/'physical_record_status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('ACTUAL_MEASUREMENT_STATE',{k:v['status'] for k,v in report['domains'].items()})
