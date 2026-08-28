# Compact FreeCAD source

`cad/parameters/baseline.json`이 치수와 revision의 source of truth이고 `cad/freecad/compact/generate.py`가 실제 part/assembly 형상의 source다. 고하중 부품은 metal로, 출력품은 hopper/chute/duct/guard/adapter/bezels로 제한한다.

`cad/generation/generate_all.py`는 FCStd, STEP, STL, 3MF, print notes/manifest, assembly metadata를 생성한다. `render_views.py`는 같은 FreeCAD shape를 tessellate하여 assembly, exploded, section, fastener/tool access, print orientation과 support-contact view를 생성한다.

생성물은 실제 제작 도면 승인이 아니다. Cutter hook, screw flight와 die retainer는 coupon·RFQ 전 provisional geometry이며 금속 shim으로 clearance를 맞춘다.
