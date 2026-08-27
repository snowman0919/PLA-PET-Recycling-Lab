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

표준 review view는 FreeCAD 환경의 VTK로 STL triangle을 읽고 Pillow software projection으로 생성한다. OpenGL/EGL이 필요하지 않는다.

```bash
QT_QPA_PLATFORM=offscreen nix develop --command bash -lc \
  "FreeCADCmd -c <<'PY'
import runpy
_ = runpy.run_path('cad/generation/render_views.py', run_name='__main__')
PY"
```
