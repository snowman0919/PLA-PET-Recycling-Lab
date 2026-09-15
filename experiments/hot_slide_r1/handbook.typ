#set page(width:297mm,height:210mm,margin:12mm,footer:context [HS-R1-S2 | 무가압 시험치구 / 물리 시험 NOT_RUN #h(1fr) #counter(page).display()])
#set text(font:"Noto Sans CJK KR",size:10pt)
#set par(leading:0.65em)
#set heading(numbering:none)
= 고온부 sliding 검증 기반 / HS-R1-S2
*PPR v0.8 · 2026-09-09 · 설계 검토용 시험치구*
#block(fill:rgb("fff0e3"),inset:10pt,width:100%)[실물 시험, 가공·구매·통전과 기계 장착은 승인되지 않았다. 이 문서는 전체 FABRICATION 릴리스를 대체하지 않는다.]
== 기능을 분리한 구조
좁은 원통 끼워맞춤이 반경방향 위치 결정과 축방향 이동을 동시에 맡는 구조를 바꾼다. 세 탄성 슈가 중심을 지지하고 반경 팽창을 받아들이며, 외측의 세 방사형 슬롯은 sheet 자체의 열팽창을 허용한다. 축방향 마찰은 0으로 가정하지 않고 시험에서 측정한다. Carrier마다 3 mm sheet 6장, 총 12장이다. 너트는 shoulder에 걸리며 sheet stack을 누르지 않는다.
#table(columns:(2fr,4fr),inset:5pt,stroke:0.5pt,
[실행 항목],[수치 및 해석 범위],
[선정 형상 C3D10 12회],[3 mesh. 주요 기계 응력 0.55→0.45 mm 변화 최대 3.03%, 변위 최대 0.054%.],
[온도 구배 6회],[반경 구배 응력 최대106.90 MPa. 두께방향 단독 peak는 수렴 완료로 취급하지 않는다.],
[대수 조합 6,144개],[최소 슈 법선력2.073 N, 계산 중심 이동 최대0.04422 mm.],
[설치 예산 포함],[실물에서 달성해야 할0.040 mm를 더하면0.08422 mm. 실측치가 아니다.],
[보어 완화 후보],[기존과 같은48개 자유팽창 부품쌍에서 간섭0. 독립 중심 지지 없이 사용 금지.],
[검사 코드],[합성 입력26개 통과. 실제 부품 시험 성공 수는0.])
균일장 모델의 요구 항복강도는 약839 MPa이다. 구배와 양면10°C 차이의 선형 검토를 합치면 약1,054 MPa이며 잠정 성적서 요구는 실제 사용 온도에서1,100 MPa 이상이다. 재질명17-7PH만으로 이 요구가 충족되지 않는다. 공급 상태·열처리·가공 후 치수와 해당 온도의 성적서가 필요하다. 실제 접촉, 마찰, 피로와 온도장은 미검증이다.
#pagebreak()
#image("drawings/01-flexure.svg",width:100%,height:175mm,fit:"contain")
#pagebreak()
#image("drawings/02-carrier.svg",width:100%,height:175mm,fit:"contain")
#pagebreak()
#image("drawings/03-fixture.svg",width:100%,height:175mm,fit:"contain")
#pagebreak()
#image("drawings/04-pin.svg",width:100%,height:175mm,fit:"contain")
#pagebreak()
= 제작 조건과 부품표
전체 기계 BOM이 아니라 시험치구 부품표다. 상세 사양·상태는 BOM.csv와 STEP을 함께 읽는다. 도면의 나사는 pilot/envelope 표현이다. 완전 나사 길이는 가공 후 검사한다.
#table(columns:(2fr,0.5fr,5fr),inset:5pt,stroke:0.5pt,
[ID],[수량],[가공·검사 요구],
[HS-R1-SHEET],[12],[t3.00±0.03; 자유 슈 R16.860±0.010; web2.00±0.03; profile/fillet은 STEP. 재료·열처리 성적서와 모서리 검사가 필요하다.],
[HS-R1-CARRIER],[2],[금속 일체형 angle 기준. 높이95, plate7, foot90×36×8. 축X0/Z50, pin PCD65.],
[HS-R1-BASE],[1],[금속100×270×10. M6 tap6개. 로컬 좌하단 기준 carrier X18/82, Y39/179; stop X30/70, Y251.],
[HS-R1-MANDREL],[1],[고체봉 OD33.970–34.000×220. 양 끝 Ø32→34/2 mm lead. 끝 M6 drill10/full-thread8 mm 이상.],
[HS-R1-PIN],[6],[Ø4 h6 shoulder27.40±0.02; M3×8; headØ7×2. 사용 온도에 맞는 재료·수령검사 필요.],
[SHIM025 / ADJUST035],[42 / 6],[OD6/ID4.10. 기본t0.25, 조정0.35 nominal. 추가/교환 shim으로 cold endplay0.25–0.35를 직접 확인.],
[HS-R1-STOP-BRACKET],[1],[60×25×65, plate6/foot8. Ø10은 M6 stud를 반경 구속하지 않는 통과공.],
[체결 및 계측],[별도],[M3 washer6/nut12; M6 stud1/stop washer2/standard nut2/jam nut2; M6 mount6sets. ≥500N 교정 gauge, 두 축 indicator, 가열시 ≥5 temperature channels.])

Carrier 기준면 간격은140 mm다. 조립 STEP은 spring 자유 형상을 표시하므로 초기 mandrel 겹침이 있다. 이것은 preload 적용 후의 변형 조립체가 아니다. 강성이 작아서 생기는 변위를 눈으로만 확인하거나, stack을 완전히 조여서 해결하지 않는다.

선택 재질은 spring용17-7PH 계열 후보이지만 가공품의 성적서가 없다. Hamilton Precision Metals와 ATI의 공개 자료는 공급/열처리 상태가 중요함을 보여주는 참고자료이며 이번3 mm 가공품의300°C 보증서가 아니다. Annealed stock을 그대로 사용하는 대체안은 승인하지 않는다. Source URL 및 적용 한계는 sources.md를 따른다.
#pagebreak()
= 실제 시험 절차와 중단 기준
== 냉간 조립 및 이동 시험
Base와 carrier를 고정하고 기준봉/indicator로 정렬한다. Sheet는6장씩 동일 방향으로 놓고 각 pin에 기본shim7개와 조정shim을 사용한다. Washer가 shoulder 끝에 걸리게 하고 냉간 endplay0.25–0.35 mm를 직접 측정한다. Nut를 더 조여 틈을 없애지 않는다. Mandrel은 taper lead를 이용해 force gauge로 천천히 삽입한다. 타격과 과도한 지렛대는 금지한다. 기계식 stop을 먼저 설치한다.
초기 왕복 stroke는 전체2 mm이며 stop은±3 mm 이내다. 시작힘과 유지힘, 두 횡방향 중심 이동을 동시에 기록한다. centre_x/centre_y는 치구 X/Z 횡방향 채널이며 축방향 Y travel과 다르다. 균열, 접촉 소실, 갑작스러운 drag 증가나 영구 변형이 보이면 중단한다.
#table(columns:(2fr,4fr),inset:4pt,stroke:0.5pt,
[판정],[조건],
[각 carrier 반력],[25N 이하. Mandrel 자중·stud와 시험 추를 모두 포함한다.],
[전체 이동힘],[시작/유지힘300N 이하, 불확도 포함. 힘이 커지면 밀어붙이지 않고 원인을 조사한다.],
[중심 이동],[0.10mm 이하, 계측 불확도 포함. 설치 예산0.040mm는 실물 검사 요구다.],
[Stack 여유],[냉간0.25–0.35mm, 열간0.10mm 이상. 마찰/굽힘으로 잠기지 않는지 확인한다.],
[냉각 후 잔류],[Offset0.02mm 이하. 최소10개의 시간·방향·힘·위치 표본을 기록한다.])
추의 무게만 carrier 하중으로 쓰지 않는다. 지지위치y1/y2와 모든 힘Fi의 위치yi로 R1=ΣFi(y2−yi)/(y2−y1), R2=ΣFi−R1을 계산하거나 지지부별 load cell로 측정한다.
== 가열은 별도 승인 후
처음부터300°C로 시작하지 않는다. 독립 과열 차단, 금속 보호판, 교정된 계측, 사용 온도에서의 재료 적격성과 명시적인 승인이 먼저다. 승인된 단계의 ramp는 최대2°C/min으로 기록하고 sheet 양면 온도차는 불확도를 포함해10°C 이내로 제한한다. 뜨거운 mandrel을 차가운 spring에 갑자기 넣지 않는다. 실제 온도장·고온 마찰·열이완 증거가 없는 현재 열간 적격성은 HOLD다.
physical_test_template.json은 NOT_RUN이다. validate_physical_test.py는 기록 검사만 하며 하드웨어를 구동하지 않는다. 전체 기계 적용 전에는 rear datum/shoulder/retainer의 추력 경로, carrier 장착, screw–barrel 중심 정렬과 guard를 함께 재검증해야 한다. 이 치구는6MPa 압력시험이나 회전 시험용이 아니다.
