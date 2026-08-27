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

표준 review view는 FreeCAD 환경의 VTK로 STL triangle을 읽고 Pillow software projection으로 생성한다. OpenGL/EGL이 필요하지 않는다.

```bash
QT_QPA_PLATFORM=offscreen nix develop --command bash -lc \
  "FreeCADCmd -c <<'PY'
import runpy
_ = runpy.run_path('cad/generation/render_views.py', run_name='__main__')
PY"
```
