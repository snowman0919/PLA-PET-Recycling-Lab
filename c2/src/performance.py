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
RAW_EVIDENCE=ALLOWED_EVIDENCE|{'UNCALIBRATED_DEM'}

class EvidenceError(ValueError):
    pass


def canonical_sha256(value) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def candidate_hashes(candidates: list[dict]) -> dict[str,str]:
    return {row['design']['candidate_id']:canonical_sha256(row['design']) for row in candidates}


def validate_evidence_record(record: dict, evidence_root: Path,
                             geometry_hashes: dict[str,str]|None=None,
                             expected_cad_revision: str|None=None):
    evidence_type=record.get('evidence_type')
    if evidence_type not in RAW_EVIDENCE:
        raise EvidenceError('Unknown or non-executed evidence type')
    if record.get('material') not in ('PLA','PET','TPU'):
        raise EvidenceError('Unknown material')
    for k in ('candidate_id','material_grade','material_lot','feed_distribution_id',
              'cad_revision','geometry_sha256','raw_data_path','raw_data_sha256'):
        if not record.get(k):
            raise EvidenceError('Missing provenance: '+k)
    if expected_cad_revision and record['cad_revision']!=expected_cad_revision:
        raise EvidenceError('Result CAD revision does not match active revision')
    if geometry_hashes is not None:
        expected=geometry_hashes.get(record['candidate_id'])
        if expected is None or record['geometry_sha256']!=expected:
            raise EvidenceError('Result geometry hash does not match active candidate')
    if evidence_type.endswith('_DEM'):
        for k in ('solver','solver_version','input_deck_path','input_deck_sha256'):
            if not record.get(k):
                raise EvidenceError('Missing solver provenance: '+k)
        deck=(evidence_root.resolve()/record['input_deck_path']).resolve()
        if not deck.is_relative_to(evidence_root.resolve()) or not deck.is_file():
            raise EvidenceError('Missing or out-of-scope solver input deck')
        if hashlib.sha256(deck.read_bytes()).hexdigest()!=record['input_deck_sha256']:
            raise EvidenceError('Solver input hash mismatch')
    if evidence_type=='CALIBRATED_DEM':
        if not record.get('calibration_id') or not record.get('calibration_validation_id'):
            raise EvidenceError('DEM calibration needs a separate held-out coupon validation record')
    if evidence_type=='PHYSICAL_EXPERIMENT':
        for k in ('physical_test_id','specimen_id','procedure_revision','instrument_ids'):
            if not record.get(k):
                raise EvidenceError('Physical label lacks test provenance: '+k)
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


def validate_record(record: dict, evidence_root: Path,
                    geometry_hashes: dict[str,str]|None=None,
                    expected_cad_revision: str|None=None):
    validate_evidence_record(record,evidence_root,geometry_hashes,expected_cad_revision)
    if record['evidence_type'] not in ALLOWED_EVIDENCE:
        raise EvidenceError('Uncalibrated DEM is exploratory evidence, not qualified performance data')
    return record


def evidence_inventory(records: list[dict], evidence_root: Path,
                       geometry_hashes: dict[str,str]|None=None,
                       expected_cad_revision: str|None=None):
    actual=[r for r in records if r.get('fixture_scope')!='SYNTHETIC_TEST_ONLY']
    valid=[validate_evidence_record(r,evidence_root,geometry_hashes,expected_cad_revision) for r in actual]
    return dict(
        actual_dem_runs=sum(r['evidence_type'].endswith('_DEM') for r in valid),
        uncalibrated_dem_runs=sum(r['evidence_type']=='UNCALIBRATED_DEM' for r in valid),
        calibrated_dem_runs=sum(r['evidence_type']=='CALIBRATED_DEM' for r in valid),
        actual_physical_tests=sum(r['evidence_type']=='PHYSICAL_EXPERIMENT' for r in valid),
        qualified_records=sum(r['evidence_type'] in ALLOWED_EVIDENCE for r in valid),
        synthetic_fixture_records_excluded=len(records)-len(actual))


def training_gate(records: list[dict], evidence_root: Path, minimum_unique_per_material: int = 20,
                  geometry_hashes: dict[str,str]|None=None,
                  expected_cad_revision: str|None=None):
    valid=[validate_record(r,evidence_root,geometry_hashes,expected_cad_revision) for r in records
           if r.get('fixture_scope')!='SYNTHETIC_TEST_ONLY']
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
