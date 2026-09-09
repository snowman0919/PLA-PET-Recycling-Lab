#set page(paper:"a4",margin:(x:18mm,y:16mm),footer:context [#align(right)[PPR GGM-MFG-r2 · #counter(page).display()]])
#set text(font:"Noto Sans CJK KR",size:11pt,lang:"ko")
#set par(justify:false,leading:0.65em)
#set heading(numbering:"1.")
#show heading.where(level:1): set text(size:20pt)
= GGM 구동부 제조·수령·교정 기준
*GGM-MFG-v0.8-r2 / 디지털 검토본 / 전체 기계 미승인*

이 문서는 선택 모터가 적용된 구동부의 제조도면을 읽고, 이후 수령·조립·교정 기록을 검토하기 위한 기준이다. 현재 모터는 미구매로 기록돼 있으며 수령 치수, 정렬 실측, 전단핀 해제 시험, 전류–토크 교정의 실제 자료는 없다. 모든 실물 항목은 NOT_RUN이다.

*본체 가공·조립·통전·모터 회전·전단핀 시험을 이번 작업에서 승인하지 않는다.* 사용자가 요청한 디지털 검증 종료와 별도 단계 승인이 있어야 실물 단계로 넘어간다. 계산·해석이 정의한 사례를 만족해도 실제 측정이나 안전 인증을 대체하지 않는다.

== 확정된 참조와 검증 범위
#table(columns:(1fr,2fr),inset:6pt,stroke:0.5pt,
 [분쇄기],[K9DG60N2 + K9G75C, 24 V, 체인12T:30T, cutter16 rpm],
 [압출기],[K9DG60N2 + K9G150C, 24 V, 직결, 정방향만],
 [구동 제어],[기존 BTS7960 두 개와 Mega. 출력은 commissioning 미완료 상태에서 금지],
 [산출물],[A3 도면23쪽·21종, DXF 투영21개,39개 제조 객체 대응. screw·thrust plate는 변경도],
 [표현 제한],[모터/스프로킷 STEP은 구매품 외형 참조. 치형 가공 원본이 아니다.])

도면의 원통면 표는 부품 bbox 최소점을 원점으로 삼고, 축 열이 원통 축이다. U/V 열은 표에 표시된 두 좌표축이다. ID/OD를 구분하고, 탭드릴 직경은 주기에 지정된 완성 나사로 가공한다. 키홈과 용접은 우측 주기가 통제한다.

도면 치수의 nominal은 현재 CAD에서 추출했다. 별도 수령 한계와 제조 공차는 프로젝트가 정한 요구값이며, 제조사 성적서나 측정값이 아니다. 제조업체가 다른 공차를 제시하면 임의로 대체하지 말고 간극·정렬에 미치는 영향을 검토한다.

#pagebreak()
= 기계 제작 및 조립 순서
금속 하중 경로를 유지한다. 하우징 출력물이나 연질 spacer가 모터·체인·추력의 주요 지지를 맡지 않는다. 신규 모터가 추가됐다는 이유로 전체 프레임을 대형화하지 않는다.

#enum(
 [D01 바닥판, D02/D03 장착판, D04/D04R 베어링판을 판재에서 준비한다. 위치 확인 후 드릴·보링하며, 일반 평판을 블록에서 CNC 밀링할 필요는 없다.],
 [분쇄 모터판과 D12 angle은 지그에서 조립해 용접한다. 용접 전후 평면과 축 위치를 확인한다. 굽은 판을 볼트 토크로 강제로 펴지 않는다.],
 [두2040 횡부재에 D13 동일 높이4개를 두고 구동대를 체결한다. 2020 지지기둥과 bearing판 두 장을 설치한다.],
 [D05 중간축,6201 두 개, 내륜 spacer·키·12T pinion을 조립한다. 캡은 외륜만 유지하고 내륜을 눌러 마찰을 만들지 않는다.],
 [30T와12T의 중심평면을 맞춘다. 중심거리86.167 mm,40피치는 nominal이다. cold lockout 상태에서 전체 구동대를 동일 shim 높이로 조절하며 축을 기울여 장력을 만들지 않는다.],
 [Screw 후방 변경키홈과 반경6201, 기존51102와thrust plate를 별도 역할로 조립한다. 압출 추력은 모터 기어박스가 아닌 기존 thrust 경로가 받는다.],
 [입출력 hub의 축방향 gap0.40 mm를 유지한다. 전단핀 blank는 교정 전 설치하지 않는다. 두 half-cover와 chain cover를 장착하고 실제 interlock 경로를 확인한다.])

== R2에서 바로잡은 사항
압출 radial cap의 중앙 ID18을 ID27.4로 넓혔다. thrust plate 후면에도D27.4 깊이0.30 relief를 넣어 외륜 환형부가 접촉하도록 했다. NSK6201 공개 지지치수(Da 최대28 mm)는 비교 근거이며 실제 sealed bearing의 씰면은 수령 후 확인한다.

분쇄/압출 coupling cover는 분할 seam과4개M3 flange 체결을 추가했다. chain cover에는2개mounting tab을 추가했다. 앞 bearing판은 이2개M3 때문에 뒷판과 구분한다.
#pagebreak()
= 실제 수령과 정렬 검사
*현재 검사 결과가 아니라, 나중에 사용할 검사항목이다.* 측정자·측정시각·계측기·교정정보·원시기록과 부품 serial을 남긴다. 수치를 사진이나 카탈로그에서 복사해 실측란에 넣지 않는다.

#table(columns:(1.4fr,1fr,1.5fr),inset:5pt,stroke:.5pt,
 [항목],[프로젝트 수령범위],[방법·해석],
 [모터·감속기],[N2/75C, N2/150C],[명판사진·serial·주문내역 일치],
 [출력축],[11.982–12.000 mm],[micrometer로2방향×3위치],
 [축 돌출],[31.80–32.20 mm],[기준은 gearhead 장착면],
 [bolt PCD],[103.90–104.10 mm],[4개 center를 좌표로 기록],
 [출력 편심],[17.90–18.10 mm],[case/grid중앙과 출력축 구분],
 [case 폭],[89–91 mm],[간섭 envelope 확인],
 [장착면 뒤 길이],[208–210 mm],[배선 돌출은 별도 기록])

파일의 요구범위는 부품 교환성 검토 한계다. 범위를 벗어나면 즉시 폐기하는 대신, 실제 승인도면과 국부 장착판 수정의 영향을 검토한다. 6201은12×32×10 참조규격이며 브랜드·씰·내부 clearance·정격을 각인으로 확인한다.

#table(columns:(1.5fr,1fr,1.5fr),inset:5pt,stroke:.5pt,
 [조립 검사항목],[목표],[필수 구분],
 [커플링 중심 offset],[≤0.030 mm],[측정 불확도까지 포함],
 [커플링 각도차],[≤0.050 deg],[rad 또는mrad와 혼용 금지],
 [sprocket 중심평면차],[≤0.250 mm],[root envelope가 아닌 실제 tooth 기준],
 [축/스프로킷 TIR],[0.030/0.100 mm],[기준축과측정지점 기록],
 [flange gap],[0.30–0.50 mm],[전단면에 축방향 clamp 금지],
 [bearing endplay],[0.05–0.20 mm],[inner/outer clamp 경로 구분])

형상검사에서 원형 land와 명목 간섭이 합격했어도 이 정렬값이 측정된 것은 아니다. 실제 spacer 높이차, bolt 조임, profile 단면과 변형은 별도 확인해야 한다.
#pagebreak()
= 전단핀과 전류 교정 계획
현재 구조는 software8.0 N·m, 교정오차±0.4, pin목표8.8–9.3, gearbox한계9.80665 N·m의 순서를 사용한다. 목경2.416–2.483 mm는 가정한 황동 전단강도120 MPa의 단일전단 계산값일 뿐이며 최종가공값이 아니다.

*전단핀 확인은 본체 구동이나 모터 stall로 수행하지 않는다.* 디지털 검토 종료 후 승인된 별도 고정·차폐 coupon 치구와 교정 torque계로 진행할 계획이다. 분쇄 정/역과압출 정방향에 대해 각각3개 독립coupon의 lot·형상·목경·해제값을 기록한다. 측정값±불확도가8.8–9.3에 모두 들어야 수치 판정이 가능하다. 해제된핀은재사용하지 않는다.

== 전류 검출과 부하토크
BTS7960의 IS를 디지털 fault나 이미 교정된 토크로 취급하지 않는다. 두 축 각각 motor lead 전류를 측정한다. PWM 공급측 평균전류와 winding 전류를 혼용하지 않는다. 기존6 A 입력한도와 보호값을 임의 상향하지 않는다.

#enum(
 [ADC 영점과0–5 A 범위를 독립 reference계측값과 대조한다. 최소5개점, ADC rail 포화는 거부한다. 전류환산은 I=a×ADC+b다.],
 [무부하 전류를3회 이상 확인한다. 이후 실제 감속기 출력에서 torque-reference와동시ADC/RPM을 기록한다. cutter축과gearbox축 토크를 혼동하지 않는다.],
 [최소5개 fit점과3개 holdout점을 분리한다. SH는 정/역holdout이 모두 필요하고EX는 정방향만 허용한다.],
 [T=k×max(abs(I)−I0,0) 모델의 holdout 잔차와 계측불확도를 합쳐0.4 N·m 이내인지 확인한다. fit에쓴데이터를 holdout으로재사용하지 않는다.],
 [숫자가통과해도프로그램은firmware를쓰거나출력을켜지않는다. 검토된계수와원시기록의hash를사람이확인한다.])

최소자료와방법은 설계된 교정절차다. 온도·속도·회전방향에 따른 감속기 손실 변화가 이 범위를 넘으면 한계·부하 운전점을 다시 검토한다. 전체안전승인과기계시험은별개다.
#pagebreak()
= 검증 경계와 기록 사용
== 온라인 자료와 프로젝트 요구를 분리한다
GGM 외형·출력축 nominal은 저장소에 보존된 GGM catalogue 원본을 따른다. 해당24 V 주문변형의 실제 승인도면과 수령값은 아직 없다. 모터는 현재 재고 기록에서 미구매 상태다.

NSK6201 자료는12×32×10, housing abutment 최대28 mm, shaft abutment16–17 mm를 제시한다. 이번D27.4 캡/relief는 그 비교를 사용한 설계이며 개별 sealed bearing의 축방향 clearance와 씰 형상을 보증하지 않는다.

#link("https://www.nsk.com/engineering/6201-apn.html")[NSK 6201 공식 사양]

#link("https://sym.or.kr/exec/front/Board/download/?no=385&realname=2015/08/12/ad973f33ec6581719b6f3b76c7e90c53.pdf&filename=K9DG60N1.pdf")[GGM catalogue 사본 출처]

== 승인 상태
#table(columns:(1.5fr,2fr),inset:6pt,stroke:.5pt,
 [도면·기하],[정의한 CAD revision의 디지털 검토. 전체 실제 조립성 인증은 아님],
 [수령·정렬],[NOT_RUN. 실물 자료 없음. 요구값을 측정값으로 복사하지 않음],
 [핀·전류],[시험/검사 코드만 준비. 실제 교정계수0, 승인flag false 유지],
 [전체 기계],[HOLD. 고온부·재료·추력·실물 안전 등의 기존미해결 항목을 면제하지 않음],
 [작업공간],[기존 /home/monad/develop/PPR 및 기존branch 사용. 새로운 외부worktree 없음])

`inspection_packet_template.json`의 빈 measurement란을 나중에 실측값으로 채우고, 원시 CSV와 사진의 SHA-256을 연결한다. `inspection.py`는 파일과 수치를 검사할 뿐 센서를 읽거나 모터를 돌리거나 firmware를 변경하지 않는다. numeric pass는기록의형식·허용범위가맞다는의미이며계측의진위는사람이검토한다.

모든 정의된 필수 simulation case가 수렴하고, 입력·하중·계측경계·오차 및 unresolved 항목을 검토한 이후에도 사용자의 별도 승인 없이 실물시험으로 자동전환하지 않는다. 무한한 현실조건을 완벽히 증명했다고 표현하지 않는다.

== 수정본을 다시 만드는 위치
도면 계약: `analysis/drive_acceptance_v08/manufacturing/drawing_contract.json`

제조자료 생성: 같은 폴더의 `define_drawings.py`, `draw_parts.py`

구동부 CAD: `cad/freecad/drive_v08/`

현재 guide와 A3 도면book은 기존 Typst로 생성했다. 이전 PDF 브라우저 도구 실패를 우회하기 위해 보안정책이나sandbox를 변경하지 않았다.
