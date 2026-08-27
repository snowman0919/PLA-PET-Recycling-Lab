# 구조 1D FEA·해석 교차검증

상태: `SCREENING_ONLY_NOT_3D_FEA_OR_PHYSICAL_VALIDATION`. Source는 `beam_fea.py`, 기계판독 결과는 `simulation/structural/beam_crosscheck.json`이다.

두 절점 Euler–Bernoulli beam element 20개로 전역 stiffness matrix를 조립하고 경계조건을 제거한 뒤 직접 선형해를 구한다. 단순지지 중앙 집중하중과 cantilever 끝단하중의 닫힌형 해와 최대 처짐·모멘트를 교차검증한다. Support reaction으로 nominal 횡전단을 계산하고 원형축은 $J=\pi d^4/32$, $\tau=Tr/J$로 비틀림을 더해 굽힘+두 전단의 von Mises 응력을 판정한다. 7개 case는 Stage 1 shaft, cutter tooth ligament, bearing plate strip, 미확정 reducer output overhang, extruder thrust plate, spooler shaft와 tower frame column이다.

이 모델은 실제 CAD mesh를 사용한 3D solid/contact FEA가 아니다. Cutter root와 keyway 응력집중, bearing fit, plate hole과 fastener preload, weld, pressure seal, impact/reverse shock, fatigue, thermal property reduction, profile joint slip과 anchor를 해석하지 않는다. 따라서 `PASS_1D_SCREEN`은 다음 상세해석으로 진행할 수 있다는 뜻이지 제작 승인이나 안전계수가 확정됐다는 뜻이 아니다.

## 판정

- 닫힌형 해와 1D FEA의 처짐·모멘트 오차는 모든 case에서 수치 정밀도 수준이어야 한다.
- Stage 1 shaft는 0.20 mm cutter clearance의 1/3 처짐 기준을 사용한다.
- Spooler와 extruder thrust plate의 임시 처짐 기준은 0.05 mm다.
- Frame의 임시 횡변위 기준은 높이/500이다.
- Nominal combined von Mises yield SF 1.5 미만 또는 처짐 초과는 `REVIEW_REQUIRED`다. Notch/contact/joint factor가 없으므로 SF가 1.5 이상이어도 최종 승인하지 않는다.

60 N·m 비틀림을 포함하면 Stage 1 20 mm shaft nominal von Mises는 약 91 MPa, SF는 약 3.35다. 미확정 15 mm reducer output overhang은 약 270 MPa, SF 약 1.13으로 더 명확히 `REVIEW_REQUIRED`이고, unbraced single-column frame도 처짐 때문에 `REVIEW_REQUIRED`다. 이는 donor shaft를 추측해 승인하거나 frame brace를 생략하지 못하게 하는 의도된 gate다. 다음 단계는 donor 실측, 최종 load case, 3D mesh convergence/contact, hand calculation과 physical strain/deflection 비교다.
