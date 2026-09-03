# 보관됨: v0.6.2.1 dual-auger feed/recirculation 가상 검증

> 상태: `SUPERSEDED_BY_FINAL_V0.8`. 이 문서는 탐색 이력이며 제작 기준이 아니다. 활성 설계는 `FD-HOP-01` + `FD-MET-01..03` 단일 six-pocket rotor, Ø8 shaft, radial clearance 0.20–0.25 mm이다. 최종 형상·도면·BOM·pin map은 `exports/final/`과 `cad/freecad/compact/geometry.py`를 따른다.

결과는 설계 판단용 deterministic surrogate와 FreeCAD solid 검증이다. DEM 또는 실제 flake 시험이 아니다.

- PLA 4형상×5변형: 95.860–100.243 g/h.
- PET 4형상×5변형: 95.856–100.006 g/h.
- 최대 연속 starvation 1.0 s, bridge clear 2 cycle, uncontrolled overfeed 0건.
- 최대 추정 feeder torque 1.413 N·m, current 2.768 A.
- degraded case는 75 g/h derate, controlled pause 또는 derate 후 pause로 수렴했다.
- passive rotor-swept return의 oversize return 최저 94.22%, PET ribbon bypass 최고 0.7875%, dead-pocket retention 최고 1.1107%였다.
- FreeCAD source-of-truth에서 10개 valid solid를 생성했고 모든 부품 bounding box는 210 mm 이하, 정적 collision check는 PASS다.

새 feeder attachment는 2.2 N·m reaction과 5.4 N vertical load 때문에 `LC11_FEEDER_ATTACHMENT`로 분류했다. LC01–LC10의 동결 하중/geometry는 변하지 않았지만 LC11 실제 Fusion 실행은 남아 있다.

`FeedDeliveryController`의 tach/current/jam/bridge/retry/permission-loss 동작은 host simulation에서만 검증했다. Mega 실기 배선은 기존 pin budget에 auger와 agitator의 독립 PWM·tach·current 채널이 배정되지 않았으므로 production sketch에 연결하지 않았다. Donor motor와 센서 형식, 안전한 multiplex/counter 회로 및 pin schedule이 확정되기 전에는 powered feed commissioning을 허용하지 않는다.

재현:

```bash
python3 analysis/process_feed/verify_process_lane.py
nix develop --command FreeCADCmd cad/freecad/compact/process_v0621.py
```
