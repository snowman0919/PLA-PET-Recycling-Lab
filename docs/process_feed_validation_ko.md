# v0.8 단일 축 auger/agitator 공급 가상 검증

> 상태: `DIGITAL_SURROGATE_PASS_PHYSICAL_COUPON_REQUIRED`. 활성 설계는 `FD-HOP-01` + `FD-MET-01..03`의 동축 anti-bridge agitator/positive-displacement auger이며, housing ID25.00 +0.05/0, auger OD24.60 -0.05/0, Ø8 shaft, radial clearance 0.20–0.25 mm이다. 최종 형상·도면·BOM·pin map은 `exports/final/`과 `cad/freecad/compact/geometry.py`를 따른다.

결과는 설계 판단용 deterministic surrogate와 FreeCAD solid 검증이다. DEM 또는 실제 flake 시험이 아니다.

- PLA/PET 8형상×5변형 전체: 95.857–106.381 g/h.
- 최대 연속 starvation 1.0 s, bridge clear 2 cycle, uncontrolled overfeed 0건.
- 최대 추정 feeder torque 1.413 N·m, current 2.768 A.
- degraded case는 75 g/h derate, controlled pause 또는 derate 후 pause로 수렴했다.
- passive rotor-swept return의 oversize return 최저 94.22%, PET ribbon bypass 최고 0.7875%, dead-pocket retention 최고 1.1107%였다.
- FreeCAD source-of-truth에서 10개 valid solid를 생성했고 모든 부품 bounding box는 210 mm 이하, 정적 collision check는 PASS다.

Feeder shaft는 2.2 N·m torsion envelope에서 CalculiX/closed-form qualification SF≥2를 요구한다. 질량/회전 계수, bridge 해소, PLA/PET 전환 청소는 Gate-2 물리 coupon 전까지 `NOT_RUN`이다.

동축 shaft는 auger와 agitator를 한 drive로 구동한다. Mega는 D44 PWM/D42 direction/D46 enable/D47 fault/A7 tach를 사용하고, no-motion timeout을 host test로 검증한다. Donor motor·tach 형식과 실제 mass/rev를 확인하기 전에는 powered feed commissioning을 허용하지 않는다.

재현:

```bash
python3 analysis/process_feed/verify_process_lane.py
nix develop --command FreeCADCmd cad/freecad/compact/process_v0621.py
```
