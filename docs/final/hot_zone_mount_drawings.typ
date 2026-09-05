#set page(paper: "a4", flipped: true, margin: 12mm)
#set text(font: "Noto Sans CJK KR", size: 8.5pt)
#set heading(numbering: "1.")
#let base = "../../exports/final/manufacturing/hot_zone/"
#let sheet(title, file, rows) = [
  = #title
  #align(center)[#image(base + file, width: 68%)]
  #table(columns: (24%, 76%), inset: 3pt, ..rows)
  #pagebreak()
]

#sheet("EX-MT-01 후방 고정 기준판", "ExtruderRearFixedDatum.svg", (
  [재료/수량], [S275 steel plate t8 / 1],
  [기준], [Datum A: rail 접촉면, B: barrel axis Ø34.10 bore, C: rear edge],
  [가공], [plate profile + Ø34.10 +0.05/0 bore; 2×Ø6.6 rail holes; open-top throat clearance],
  [공차/검사], [A 평면도 0.10; bore axis ⟂ A 0.10/54; hole 위치 ±0.10; CMM 또는 height gauge],
  [표면/조립], [Zn-rich primer, bore/접촉면 mask; rear axial datum, shim 0.1/0.2/0.5 mm 허용],
))

#sheet("EX-MT-02 전방 축방향 슬라이딩 가이드", "ExtruderFrontSlidingGuide.svg", (
  [재료/수량], [S275 steel plate t8 / 1],
  [기준], [Datum A: rail 접촉면, B: guide bore Ø34.60, C: front edge],
  [가공], [plate profile + Ø34.60 +0.10/0 bore; 2×Ø6.6 rail holes; open-top service slot],
  [공차/검사], [A 평면도 0.10; B position ±0.10; cold axial travel ≥1.30 mm를 feeler/travel gauge로 검사],
  [표면/조립], [Zn-rich primer, bore mask; axial clamp 금지, dry sliding guide로만 사용],
))

#sheet("EX-MT-03 후방 분할 고정 collar", "ExtruderFixedCollar.svg", (
  [재료/수량], [S45C / 1],
  [기준], [Datum A: Ø34.10 bore axis, B: rear thrust face],
  [가공], [OD Ø50; L12.00 ±0.05; bore Ø34.10 +0.03/0; split/open-top profile],
  [공차/검사], [B runout 0.05 to A; bore Ra≤1.6 µm; blue-fit contact ≥70%],
  [표면/조립], [black oxide, bore mask; rear datum side only, front guide에 collar 설치 금지],
))

#sheet("EX-MT-04 후방 2020 지지 rail", "ExtruderSupportRailRear.svg", (
  [재료/수량], [2020 aluminum extrusion / 1],
  [절단], [L390.0 ±0.5; 양단 직각도 0.3; 절단면 deburr],
  [기준/조립], [machine X 방향, Y400/Z320; FrameSpoolTopRail에 metal face-joint],
  [검사], [기존 전방 MidRail320과 높이차 ≤0.20 mm; 축 평행도 ≤0.20/390],
  [체결], [M5 profile hardware, 5 N·m; 최종 torque stripe 적용],
))

= 발주·조립 공통 주기

- 단위 mm, 제3각법, 별도 표기 없는 일반공차 ISO 2768-m.
- heater/barrel hot zone을 출력물로 지지하지 않는다. 하중 경로는 steel plate → aluminum profile → frame/table이다.
- PET 270 °C 계산상 자유 열팽창 1.1662 mm; 전방 guide의 냉간 가용 travel은 1.30 mm 이상이어야 한다.
- 본 도면은 디지털 제작 후보용이다. 실제 치수검사와 냉간 조립 확인 전 가열 승인 금지.
