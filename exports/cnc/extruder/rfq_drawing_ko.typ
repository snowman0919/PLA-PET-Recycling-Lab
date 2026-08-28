#set page(paper: "a4", margin: 14mm)
#set text(font: "Noto Sans CJK KR", size: 8.5pt)
#set heading(numbering: "1.")
#let hold = box(fill: rgb("#ffe1dc"), inset: 7pt, stroke: rgb("#a52a2a"), [*FULL 발주 HOLD — EX-CPN-SCR/EX-CPN-BAR 공정 coupon과 공급사 DFM, Gate-3 승인 전 EX-SCR-01/EX-BAR-01 발주 금지*])

= 16 mm × 16 L/D screw/barrel RFQ drawing

Revision: `solid-manifold-openmodelica-v0.4` / 단위: mm / 온도: 20 ±2 °C / 일반 모서리 C0.2–0.5, burr 없음

#hold

== EX-SCR-01

#image("EX-SCR-01_drawing.svg", width: 100%)

#table(columns: (30%, 70%), inset: 4pt,
  [재료], [SCM440, normalized blank → rough turn → QT 28–32 HRC],
  [주요 치수], [Total 316.0 ±0.10; active 256.0; single-start RH; pitch 16.00 ±0.03; land 1.60 ±0.05; OD Ø15.92 -0.02/0],
  [Zone/root], [Feed 128, root Ø10.88; compression 64, linear Ø10.88→Ø14.08; meter 64, root Ø14.08],
  [Journal], [Drive Ø12 h6 ×35, KS/DIN key 4×4, keyseat 4 P9 wide ×2.5 +0.10/0 deep; thrust Ø15 h6 ×20; shoulder perpendicularity 0.03 to Datum A; flight start 0° ±5° from key plane],
  [GD&T], [Flight OD TIR ≤0.05/256; drive-to-flight concentricity ≤0.03; straightness ≤0.05/256],
  [표면], [Flight OD Ra≤0.8 µm; root/flank Ra≤1.6 µm; weld repair 금지],
  [열처리], [Gas nitride effective case 0.30–0.50, surface 900–1100 HV; journals mask; final OD grind between centres],
)

가공 route: normalized blank → datum centre drilling → rough turn → QT → finish journals/shoulders leaving flight allowance 0.15 → 4-axis flight mill → root/flank polish → gas nitride → flight OD grind → TIR/Ra/hardness 검사.

#pagebreak()

== EX-BAR-01

#image("EX-BAR-01_drawing.svg", width: 100%)

#table(columns: (30%, 70%), inset: 4pt,
  [재료], [SCM440 solid/seamless blank, QT 28–32 HRC],
  [주요 치수], [OD Ø34.00 ±0.05; L280.00 ±0.05; final bore Ø16.20 +0.02/0],
  [Port/thread], [18 axial ×20, rear edge 12.0 from Datum B, edge R0.5; front 4× M4×0.7-6H full depth≥8/tap drill≥11 on PCD26 at 45/135/225/315° from port centre plane; OD/bore breakthrough 금지],
  [나사 ligament], [M4 major envelope 기준 outer 2.0 mm, bore-side 2.9 mm 이상; supplier는 thread minor/major와 실제 OD/ID로 재확인],
  [GD&T], [Bore straightness ≤0.05/256; bore-to-OD/register concentricity ≤0.05; end face perpendicularity 0.03],
  [표면], [Final bore Ra 0.4–0.8 µm; no weld/plating in bore],
  [열처리], [Gas nitride 0.30–0.50, ≥900 HV; final hone 후 effective case ≥0.25],
  [검사], [ID/roundness at z=20/140/260; roundness ≤0.02; air/3-point bore-gauge record],
)

가공 route: rough deep drill → stress relieve → semi-finish ream/hone leaving 0.05–0.08 → port/flange machine → gas nitride → final hone → ID/roundness/Ra/case-depth 검사.

Matched drawing-limit diametral clearance는 0.28–0.32, radial clearance는 0.14–0.16이다. Screw OD와 barrel ID를 세 station에서 기록하고 이 범위 안에서 pair한다.

== Supplier deliverables

- Material certificate, QT hardness, nitride surface hardness/effective case depth
- Screw OD/TIR/concentricity/straightness, barrel ID/roundness/straightness report
- Ra trace, actual matched clearance table, STEP 기준 DFM deviation list
- 공차 변경 제안은 발주 전 서면 승인; silent substitution 금지

== Process coupon release

먼저 `EX-CPN-SCR` L48.00 ±0.05, three RH pitches 16.00 ±0.03, feed-zone OD/root/land와 `EX-CPN-BAR` L60.00 ±0.05, OD34.00 ±0.05, final ID16.20 +0.02/0만 견적·가공한다. Ends는 axis에 0.03 이내 수직이다. Coupon은 동일 material/route/heat treatment로 만들고 OD/ID, pitch, land, Ra, hardness/case depth를 검사한다. Coupon 불합격 또는 질문 미해결이면 full part는 계속 HOLD다.
