# SKF 625/6001 인터페이스 근거

- 적용 revision: `final-design-fabrication-closure-v0.8`
- 공식 자료 확인일: 2026-09-08
- 상태: 디지털 치수 근거 확정, 구매·수입검사·압입/회전 시험 `NOT_RUN`
- 선정 형식: SKF `625-2Z`, 5 × 16 × 5 mm, C=1.14 kN, C0=0.38 kN; SKF `6001-2RSH`, 12 × 28 × 8 mm, C=5.40 kN, C0=2.36 kN. [SKF 단열 깊은 홈 볼베어링 표](https://cdn.skfmediahub.skf.com/api/public/0901d196802809de/pdf_preview_medium/0901d196802809de_pdf_preview_medium.pdf)
- 공차 등급: 별도 정밀도 suffix가 없는 SKF 일반 볼베어링은 ISO 492 Normal 공차를 적용한다. [SKF A.2 Tolerances, Table 1–2](https://cdn.skfmediahub.skf.com/api/public/0901d196802809de/pdf_preview_medium/Rolling_bearings_-_17000_1_EN_pdf_preview_medium.pdf)
- 625 보어 한계: 4.992–5.000 mm; 외륜 한계: 15.992–16.000 mm; 폭 한계: 4.880–5.000 mm.
- 6001 보어 한계: 11.992–12.000 mm; 외륜 한계: 27.991–28.000 mm; 폭 한계: 7.880–8.000 mm.
- 축 설계: FM-GA-01 Ø5 h6=4.992–5.000 mm, SP-SH-01 Ø12 h6=11.989–12.000 mm.
- POM-C 열팽창: Ensinger TECAFORM AH natural의 23–60 °C CLTE는 `13×10⁻⁵/K`다. [Ensinger 공식 제품 자료](https://www.ensingerplastics.com/en-gb/shapes/acetal-tecaform-ah-natural)
- 베어링강 열팽창: SKF가 제시한 100Cr6 bearing steel 값은 `12×10⁻⁶/K`다. [SKF 공식 재료 비교표](https://cdn.skfmediahub.skf.com/api/public/0901d19680495562/pdf_preview_medium/0901d19680495562_pdf_preview_medium.pdf)

따라서 계산상 FM-GA-01–625 diametral fit은 −0.008–+0.008 mm다. FM-GR-01의 Ø16.000–16.018 H7 seat와 625 외륜은 23 °C에서 0.000–0.026 mm clearance이고, 위 CLTE 차이를 60 °C까지 적용한 상한은 0.096 mm다. 5.10 mm pocket과 bearing 폭은 0.10–0.22 mm axial clearance를 남긴다. 매입형 FM-GC-01의 Ø15.00–15.10 relief는 외륜을 반경 방향 0.446–0.500 mm 겹치며, 3개 SYS-14 관통 체결이 열간 외륜 이탈을 막는다.

SP-SH-01–6001 fit은 −0.008–+0.011 mm다. SP-BP-01의 Ø28.000–28.021 H7 seat와 6001 외륜은 0.000–0.030 mm clearance이며, pocket 8.05–8.10 mm와 bearing 폭은 0.05–0.22 mm axial clearance를 남긴다. SP-BR-01의 Ø26.00–26.10 relief는 외륜 가장자리를 반경 방향 0.9455–1.000 mm 겹쳐 양의 축방향 고정을 만든다. 이는 도면의 디지털 fit 배분이며 실제 bearing lot, 축 측정, 압입력, blue-check, shield drag, 자유회전, 열간 TIR 및 retention 시험을 대체하지 않는다.
