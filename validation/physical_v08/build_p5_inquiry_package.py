#!/usr/bin/env python3
"""Build a deterministic coupon-only supplier inquiry review ZIP. Never sends or orders anything."""
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'dist/PPR-v0.8-P5-COUPON-CAPABILITY-INQUIRY-REVIEW.zip'
FILES={
 '01_INQUIRY/specialist_hot_zone_inquiry_email_en.txt':ROOT/'docs/final/specialist_hot_zone_inquiry_email_en.txt',
 '01_INQUIRY/specialist_hot_zone_supplier_response.csv':ROOT/'docs/final/specialist_hot_zone_supplier_response.csv',
 '02_REQUIREMENTS/P5_PROCESS_COUPON_KO.md':ROOT/'validation/physical_v08/P5_PROCESS_COUPON_KO.md',
 '02_REQUIREMENTS/p5_supplier_inspection_requirements.csv':ROOT/'validation/physical_v08/p5_supplier_inspection_requirements.csv',
 '03_COUPON_GEOMETRY/EX-CPN-SCR.pdf':ROOT/'exports/final/manufacturing/RFQ/EX-CPN-SCR.pdf',
 '03_COUPON_GEOMETRY/EX-CPN-SCR.step':ROOT/'exports/final/manufacturing/RFQ/EX-CPN-SCR.step',
 '03_COUPON_GEOMETRY/EX-CPN-SCR.dxf':ROOT/'exports/final/manufacturing/RFQ/EX-CPN-SCR.dxf',
 '03_COUPON_GEOMETRY/EX-CPN-BAR.pdf':ROOT/'exports/final/manufacturing/RFQ/EX-CPN-BAR.pdf',
 '03_COUPON_GEOMETRY/EX-CPN-BAR.step':ROOT/'exports/final/manufacturing/RFQ/EX-CPN-BAR.step',
 '03_COUPON_GEOMETRY/EX-CPN-BAR.dxf':ROOT/'exports/final/manufacturing/RFQ/EX-CPN-BAR.dxf',
}
FIXED=(2026,9,10,0,0,0)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    missing=[str(p) for p in FILES.values() if not p.is_file()]
    if missing: raise SystemExit('missing package inputs: '+', '.join(missing))
    # Fail closed if any production-part file sneaks into the allowlist.
    forbidden=('EX-SCR-01','EX-BAR-01','EX-DIE-01','PPR-FULL')
    if any(any(x in arc for x in forbidden) for arc in FILES): raise SystemExit('production file in coupon-only package')
    # Verify coupon geometry copies still equal current manufacturing source geometry.
    for pid in ('EX-CPN-SCR','EX-CPN-BAR'):
        for ext in ('step','dxf'):
            current=ROOT/f'exports/cnc/extruder/parts/{pid}/{pid}.{ext}'
            rfq=ROOT/f'exports/final/manufacturing/RFQ/{pid}.{ext}'
            if sha(current)!=sha(rfq): raise SystemExit(f'stale RFQ geometry: {pid}.{ext}')
    manifest={'status':'REVIEW_ONLY_NOT_SENT','purchase_or_manufacturing_authorized':False,
      'scope':'EX-CPN-SCR and EX-CPN-BAR capability inquiry only; no production parts',
      'controlling_process_requirements':'02_REQUIREMENTS/p5_supplier_inspection_requirements.csv',
      'geometry_note':'PDF title blocks may show an earlier source commit, but packaged STEP/DXF hashes are verified byte-identical to current coupon source geometry. Process/case-depth wording is controlled by the P5 requirements files.',
      'files':{arc:sha(p) for arc,p in sorted(FILES.items())}}
    readme='''# PPR v0.8 P5 coupon capability inquiry - REVIEW ONLY\n\nStatus: NOT SENT. No purchase/manufacturing authorization.\n\nThis package contains only EX-CPN-SCR and EX-CPN-BAR coupon geometry and supplier inquiry/inspection requirements. It intentionally contains no EX-SCR-01, EX-BAR-01, EX-DIE production geometry.\n\nThe controlling process acceptance is `02_REQUIREMENTS/p5_supplier_inspection_requirements.csv`. The coupon PDF title block may contain an earlier source commit; packaged STEP/DXF files are hash-verified against the current coupon source geometry.\n\nA supplier may quote capability and the two coupons, but manufacture/order remains subject to explicit user approval. Full production parts stay HOLD after coupon review until separately approved.\n'''
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for arc,data in [('00_README.md',readme.encode()),('MANIFEST.json',(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())]:
            info=zipfile.ZipInfo(arc,FIXED); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16; z.writestr(info,data)
        for arc,p in sorted(FILES.items()):
            info=zipfile.ZipInfo(arc,FIXED); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16; z.writestr(info,p.read_bytes())
    result={'status':'REVIEW_ONLY_NOT_SENT','path':str(OUT.relative_to(ROOT)),'sha256':sha(OUT),'payload_files':len(FILES)+2,
            'purchase_or_manufacturing_authorized':False}
    (ROOT/'validation/physical_v08/p5_inquiry_package_manifest.json').write_text(json.dumps({**result,'input_sha256':manifest['files']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': main()
