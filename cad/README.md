# Parametric CAD

`cad/parameters/baseline.json`이 초기 공통 parameter source이고 `cad/freecad/**/generate.py`가 FreeCAD source of truth다.

```bash
nix develop --command bash -lc \
  "FreeCADCmd -c <<'PY'
import runpy
_ = runpy.run_path('cad/generation/generate_all.py', run_name='__main__')
PY"
```

생성 대상은 `cad/generation/fcstd`, `exports/step`, `exports/stl`이다. full assembly skeleton의 module box는 keep-out envelope이며 제작 부품이 아니다. tolerance coupon을 먼저 출력·측정한 뒤 공차 parameter를 수정한다.

Stage 1 상세 proof generator는 다음을 함께 만든다.

- 8-hook cutter disc와 5-disc/shaft 교차 stack
- 20 mm keyed shaft, 6004 bearing 6개, combined retainer 3개
- 주 bearing plate 2개와 timing-gear 외부 support plate 1개
- tooth가 아닌 timing pitch/coupling keep-out envelope
- bearing plate DXF와 cutter/plate 제작 주석

축방향 plate·bearing·retainer·timing 위치는 `baseline.json`의 `stage1.axial_layout`에서 함께 관리한다. 타이밍 기어 envelope와 실제 gear tooth geometry를 혼동하면 안 된다.

Stage 2 proof generator는 50 mm single rotor, fixed bed knife, carrier, 양쪽 bearing plate/6004/retainer와 plate DXF를 생성한다. `stage2.axial_layout`과 0.2 mm nominal blade clearance가 source parameter다. fused rotor는 제작 승인 형상이 아니라 kinematic·load envelope이며 blade pocket/fastener/balance는 후속 상세 설계다.

Stage 3 generator는 40 mm staggered rotor/stator proof, 17 mm/6203 shaft support와 4/5/6 mm flat screen coupon family를 만든다. 조립에는 5 mm screen이 들어가지만 세 screen 모두 FCStd/STEP/STL로 export된다. flat screen은 opening 비교용이며 최종 curved containment로 사용하지 않는다.

Vibratory sorter generator는 8° 경사의 2단 cassette와 세 배출 경로, 4개 isolator, donor motor/eccentric envelope, M5 service clamp를 만든다. 상단 6 mm 잔류물은 재순환, 하단 3 mm 잔류물은 acceptable, 하단 통과물은 fines다. screen bar와 chute는 proof envelope이며 sourced mesh/seal 상세가 아니다.

Dryer/feeder generator는 ID 140 mm 금속 hopper/cone, 40 mm 단열, ventilated shield, agitator, double gate와 30 mm metering-auger proof를 만든다. PET hot path는 전부 금속으로 표시하며 auger flight와 dry-air 장치는 계산/공간 envelope이지 제작 승인 형상이 아니다.

Extruder generator는 18 mm×24 L/D single screw의 24회전 helical flight, 가변 root, ID18.2/OD38 barrel, cooled feed throat, breaker/screen interface, Ø3 mm die, 51102 thrust path, heater/insulation/shield와 pressure/rupture keep-out을 만든다. Flight는 10° chord의 닫힌 B-rep proof이며 smooth CNC toolpath 자체가 아니다.

표준 review view는 FreeCAD 환경의 VTK로 STL triangle을 읽고 Pillow software projection으로 생성한다. OpenGL/EGL이 필요하지 않는다.

```bash
QT_QPA_PLATFORM=offscreen nix develop --command bash -lc \
  "FreeCADCmd -c <<'PY'
import runpy
_ = runpy.run_path('cad/generation/render_views.py', run_name='__main__')
PY"
```
