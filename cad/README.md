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

Input-classifier generator는 최대 500 mL 병 envelope, 상·하 이중 게이트의 상호 배타 위치, 차광 카메라/백라이트 광로, reject flap과 6색+Reject 7-port 분배기를 만든다. 광학 부품과 병은 keep-out이고, 힌지·positive-opening interlock·충격 containment 및 재료 정확도는 실물 coupon으로 검증한다.

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

Forming-line generator는 3분할 440 mm 횡류 공랭 덕트, 두 직교 광로를 갖는 직경 게이지, Ø40 mm 동기 nip roller와 독립 Ø30 mm odometer를 만든다. `diameter_gauge_optical_proof`는 enclosure를 제거한 광학 배치 확인용이고, reference ray는 초점·왜곡·불확도 인증을 대신하지 않는다. 첫 hot-strand 덕트는 금속 또는 온도 적합 재료로 제작한다.

Spooler generator는 Ø200×73 mm 최대 1 kg급 spool reference, 12 mm steel shaft/6001 bearing 지지, 교체형 taper adapter, 120 mm dancer, 70 mm traverse와 보호 cage를 만든다. Printed adapter는 유일한 torque·축방향 하중경로가 아니며 drive와 slip clutch는 공급품 keep-out이다.

Control-enclosure generator는 500×400×200 mm grounded enclosure 안에 BOM 부품을 개별 객체로 배치한다. 녹색은 공식 치수의 selected-candidate envelope, 파란색은 190×130 mm PCB 예약영역과 실측 대기 user inventory, 주황색은 주문 불가 TBD placeholder다. 24 V 고전류/히터, hardwired safety chain, 5 V logic/sensor, PE 경로는 별도 색·객체·harness ID로 분리하고 30 mm terminal service keep-out을 둔다. 실제 MPN 확정, 열·SCCR·연면거리·침투보호·배선 굽힘 반경·PE 연속성은 별도 승인 게이트다.

표준 review view는 FreeCAD 환경의 VTK로 STL triangle을 읽고 Pillow software projection으로 생성한다. OpenGL/EGL이 필요하지 않는다.

```bash
QT_QPA_PLATFORM=offscreen nix develop --command bash -lc \
  "FreeCADCmd -c <<'PY'
import runpy
_ = runpy.run_path('cad/generation/render_views.py', run_name='__main__')
PY"
```
