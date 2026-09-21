"""Verified performance ingestion and model gate. Geometry is never a breakage label."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

TARGETS=('target_yield_mass_fraction','throughput_g_h','peak_torque_Nm',
         'rms_torque_Nm','jam_probability','specific_energy_J_g','max_polymer_C')
ALLOWED_EVIDENCE={'CALIBRATED_DEM','PHYSICAL_EXPERIMENT'}

class EvidenceError(ValueError):
    pass


def validate_record(record: dict, evidence_root: Path):
    if record.get('evidence_type') not in ALLOWED_EVIDENCE:
        raise EvidenceError('Kinematics, analytical pseudo-labels and uncalibrated DEM are not qualified performance data')
    if record.get('material') not in ('PLA','PET','TPU'):
        raise EvidenceError('Unknown material')
    for k in ('candidate_id','material_grade','material_lot','feed_distribution_id',
              'calibration_id','cad_revision','raw_data_path','raw_data_sha256'):
        if not record.get(k):
            raise EvidenceError('Missing provenance: '+k)
    if record['evidence_type']=='CALIBRATED_DEM' and not record.get('calibration_validation_id'):
        raise EvidenceError('DEM calibration needs a separate held-out coupon validation record')
    root=evidence_root.resolve()
    path=(root/record['raw_data_path']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise EvidenceError('Missing or out-of-scope raw trace')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record['raw_data_sha256']:
        raise EvidenceError('Raw data hash mismatch')
    outputs=record.get('outputs',{})
    for k in TARGETS:
        v=outputs.get(k)
        if not isinstance(v,(float,int)) or not math.isfinite(v):
            raise EvidenceError('Missing performance target: '+k)
        if k!='max_polymer_C' and v<0:
            raise EvidenceError('Negative performance value')
    for k in ('target_yield_mass_fraction','jam_probability'):
        if not 0<=outputs[k]<=1:
            raise EvidenceError('Probability outside [0,1]')
    if outputs['rms_torque_Nm']>outputs['peak_torque_Nm']:
        raise EvidenceError('RMS torque exceeds peak')
    return record


def training_gate(records: list[dict], evidence_root: Path, minimum_unique_per_material: int = 20):
    valid=[validate_record(r,evidence_root) for r in records]
    counts={m:len({r['candidate_id'] for r in valid if r['material']==m}) for m in ('PLA','PET','TPU')}
    return dict(status='READY_FOR_GROUP_SPLIT' if all(n>=minimum_unique_per_material for n in counts.values())
                else 'BLOCKED_PERFORMANCE_DATA',unique_designs_by_material=counts,
                minimum_unique_per_material_policy=minimum_unique_per_material,
                total_records=len(valid),trained=False,
                split_rule='Hold out whole geometry IDs and material lots; never split time frames from one run')


def nondominated(values: np.ndarray) -> np.ndarray:
    a=np.asarray(values,dtype=float)
    if a.ndim!=2 or not np.isfinite(a).all():
        raise ValueError('Finite objective matrix required')
    return np.array([not np.any(np.all(a<=r,axis=1)&np.any(a<r,axis=1)) for r in a])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--records',type=Path,required=True)
    parser.add_argument('--evidence-root',type=Path,required=True)
    args=parser.parse_args()
    records=json.loads(args.records.read_text())
    print(json.dumps(training_gate(records,args.evidence_root),indent=2))

if __name__=='__main__':
    main()
