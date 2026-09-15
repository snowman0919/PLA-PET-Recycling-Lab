"""Generate the authoritative integrated-frame schedule from verified native CAD."""
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cad.freecad.compact.generate import normalize_step, normalize_dxf, normalize_zip_container, _projection_polylines
OUT=ROOT/'exports/final/frame_v08'
CUTLIST=ROOT/'exports/fabrication/frame_cut_list.csv'
FIELDS=['part_id','stock','cut_length_mm','quantity','end_condition','length_tolerance_mm','source','release_state',
 'cad_object','profile_type','axis','section_orientation','mounting_reference','reuse_state']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def csvfile(path,fields,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    parameter=ROOT/'cad/parameters/ggm_frame_revision.json'; spec=json.loads(parameter.read_text())
    audit_path=ROOT/'analysis/frame_v08/results/geometry.json'; audit=json.loads(audit_path.read_text())
    beam_path=ROOT/'analysis/frame_v08/results/beam_comparison.json'; beam=json.loads(beam_path.read_text())
    assert audit['status']=='FRAME_DELTA_GEOMETRY_PASS' and beam['status']=='FRAME_COMPARATIVE_SCREEN_PASS'
    ggm=ROOT/'exports/final/drive_ggm_v08/manifest.json'; model=json.loads(ggm.read_text())
    for evidence in (audit,beam,model):
        for rel,digest in evidence['source_sha256'].items(): assert sha(ROOT/rel)==digest,rel
    whole=next(r for r in model['exports'] if r['file']=='GGM-FULL-ASM.step')
    native=ggm.parent/whole['fcstd']; step=ggm.parent/whole['file']
    assert sha(native)==whole['fcstd_sha256'] and sha(step)==whole['sha256']
    doc=App.openDocument(str(native)); objects={o.Name:o.Shape for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    rows=[]; connections=[]
    for member in audit['after']:
        name=member['id']
        if 'section_mm' not in member: continue
        shape=objects[name]; b=shape.BoundBox; dims=[b.XLength,b.YLength,b.ZLength]
        assert abs(max(dims)-member['length_mm'])<1e-6
        assert abs(shape.Volume-dims[0]*dims[1]*dims[2])<1e-4
        profile='2020' if member['section_mm']==[20.,20.] else '2040'
        peers=';'.join(c['id'] for c in member['contacts'])
        end='square/square; deburr; inspect assembled datum with metal shims'
        if name.startswith('GGM_SH_Post_'): end+='; M5 end tap per GGM R2; verify extrusion core and thread engagement'
        rows.append(dict(zip(FIELDS,['FRM-'+name,('20x20' if profile=='2020' else '20x40')+' aluminum profile',
          f"{member['length_mm']:.3f}",'1',end,'+/-0.5',str(native.relative_to(ROOT))+'#'+name,
          'MEASURE_STOCK_NESTING_AND_P2_APPROVAL_REQUIRED',name,profile,'XYZ'[member['axis']],
          '40 mm side vertical' if profile=='2040' else '20x20',peers or 'FREE_END_CHECK_REQUIRED',
          'STOCK_BAR_ID_ALLOCATION_REQUIRED_NO_DOUBLE_COUNTING'])))
        for c in member['contacts']:
            if c['id']>name or not c['profile']:
                connections.append({'member':name,'mate':c['id'],'gap_mm':f"{c['gap_mm']:.6f}",
                 'scope':'CAD_CONTACT_ONLY_NOT_A_FASTENER_OR_JOINT_STRENGTH_APPROVAL'})
    assert len(rows)==40 and set(spec['remove_profiles']).isdisjoint(objects)
    csvfile(CUTLIST,FIELDS,rows); csvfile(OUT/'frame_members.csv',FIELDS,rows)
    csvfile(OUT/'frame_connections.csv',list(connections[0]),connections)
    tie=objects[spec['tie']['object']]; td=App.newDocument('FrameTie')
    feature=td.addObject('PartDesign::Feature','FR_TIE_01');feature.Shape=tie;td.recompute()
    tp=OUT/'FR-TIE-01.step';Part.export([feature],str(tp));normalize_step(tp)
    np=OUT/'FR-TIE-01.FCStd';np.unlink(missing_ok=True);td.saveAs(str(np));normalize_zip_container(np,True)
    import importDXF
    dp=OUT/'FR-TIE-01.dxf';importDXF.export([feature],str(dp));normalize_dxf(dp)
    App.closeDocument(td.Name);App.closeDocument(doc.Name)
    imported=Part.read(str(tp)); assert imported.isValid() and abs(imported.Volume-tie.Volume)<1e-5
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="780" viewBox="0 0 1000 780">',
      '<rect width="1000" height="780" fill="white"/><g font-family="sans-serif" fill="#172533">',
      '<text x="35" y="40" font-size="23">FR-TIE-01 / S275JR / finished formed section</text>',
      _projection_polylines(tie,('x','y'),(35,70,930,180)),
      _projection_polylines(tie,('x','z'),(35,270,930,140)),
      _projection_polylines(tie,('y','z'),(35,440,450,220)),
      '<text x="520" y="470" font-size="18">L470 +/-0.5; W40 x H20 +/-0.3; t3</text>',
      '<text x="520" y="505" font-size="18">Inside bend R3; outside R6</text>',
      '<text x="520" y="540" font-size="18">4 x diameter 5.5 +0.2/0</text>',
      '<text x="520" y="575" font-size="18">Hole X: 10, 460; local Y: 12, 28</text>',
      '<text x="520" y="610" font-size="18">Hole centres +/-0.2 from end/side datum</text>',
      '<text x="35" y="710" font-size="16">Finished shape controls. Flat blank development: verify bend-tool allowance.</text>',
      '<text x="35" y="745" font-size="16">4 x M5x10 + washer + matching T-nut. Receipt/thread engagement and physical test HOLD.</text></g></svg>']
    (OUT/'FR-TIE-01.svg').write_text('\n'.join(svg))
    body=['#set page(paper: "a4", margin: 15mm)','#set text(font: "Noto Sans CJK KR", size: 9pt)',
      '= GGM 프레임 절단·조립 기준 / R1',
      '2020: 36개 / 15,078 mm. 2040: 4개 / 2,180 mm. 총 40개 / 17,258 mm.',
      '기존 통합 CAD 대비 2020 2개 / 489 mm 감소. FR-TIE-01 강판 연결재 1개 추가. 경량화 주장이 아니다.',
      '아래는 명목 완성 길이이며 절단 손실·끝단 정리·가공 여유와 실제 bar별 배치는 포함하지 않는다. P1 실측 및 P2 nesting/승인 전 절단 금지.',
      '접촉 목록은 체결품·슬립·실물 강성의 인증이 아니다. 기존 GGM R2 연결 상세와 수령 프로파일/T-nut를 대조한다.']
    cells=['[Member]','[단면]','[완성 길이 mm]','[수량]']
    for row in rows:
        cells += ['['+row['cad_object'].replace('_','\\_')+']','['+row['profile_type']+']',
                  '['+row['cut_length_mm']+']','[1]']
    body.append('#table(columns: (1fr, 17mm, 23mm, 12mm), inset: 3pt, '+','.join(cells)+')')
    body += ['#pagebreak()','= FR-TIE-01 / 대체 강판 연결재',
      '#image("FR-TIE-01.svg", width: 100%)',
      '설치 위치: X0..470, Y265..305, Z20..40 mm. 하부 좌우 2020 rail 위에 놓고 네 M5 조인트로 고정한다.',
      '판 두께3 mm, 내부 굽힘 R3 기준의 완성 단면이다. 평판 전개는 실제 금형의 굽힘 여유를 확인한 후 확정한다.',
      'M5x10 class8.8 + washer + 해당 슬롯용 T-nut 4조. 5.0 N.m는 기존 M5 기준값이며 제조사 허용 토크 및 나사 물림 확인 전 체결 승인값이 아니다.',
      '비교 beam screen은 가정된 재료·단면·지지 조건의 강성비다. 볼트 슬립·실제 부재 강도·피로·진동·안전 인증은 NOT_RUN이다.']
    typ=OUT/'FRAME_CUT_AND_TIE_KO.typ';typ.write_text('\n\n'.join(body)+'\n')
    pdf=OUT/'FRAME_CUT_AND_TIE_KO.pdf'
    subprocess.run(['typst','compile','--root',str(ROOT),str(typ),str(pdf)],check=True,
                   env=dict(os.environ,SOURCE_DATE_EPOCH='946684800'))
    note='# GGM frame R1\n\n2020 36 pieces / 15078 mm; 2040 4 pieces / 2180 mm.\n\n'
    note+='FrameBottomCross275 L430 is replaced by FR-TIE-01 formed steel; SpoolTopSegment290 L59 is removed.\n'
    note+='Keep every 2040 and the motor, bearing, hot-zone, thrust and feeder supports.\n\n'
    note+='frame_members.csv maps each physical profile once; frame_connections.csv is contact evidence, not a complete certified joint design.\n'
    note+='P1 records each actual bar. P2 requires current CAD binding, measured-minus-U95 usable lengths, conservative kerf and cut allowance, and explicit fabrication approval.\n'
    note+='Actual stock adequacy, supplier section properties, joint slip/strength and physical operation remain NOT_RUN.\n'
    (OUT/'README.md').write_text(note)
    outputs=[CUTLIST,*[p for p in OUT.iterdir() if p.is_file() and p.name!='frame_release.json' and p.suffix!='.FCStd1']]
    sources=[Path(__file__).resolve(),parameter,audit_path,beam_path,ggm,native,step]
    report={'status':'FRAME_CUTLIST_GEOMETRY_MATCH','revision':spec['revision'],'members':rows,'totals':audit['totals'],
      'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},
      'output_sha256':{str(p.relative_to(ROOT)):sha(p) for p in outputs},
      'physical_validation_state':'NOT_RUN','cut_authorization':False,'stock_nesting':'ACTUAL_RECORDS_REQUIRED'}
    (OUT/'frame_release.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FRAME_RELEASE_GENERATED',report['totals'])

if __name__=='__main__': main()
