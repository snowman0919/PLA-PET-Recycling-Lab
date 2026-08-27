# Dryer·feeder visual/solid review — 2026-08-28

## 증거

- `dryer_feeder_hot_path_proof.png`
- `renders/modules/dryer_feeder_proof_{front,right,top,isometric}.png`
- `simulation/thermal/dryer_feeder_budget.json`
- `simulation/thermal/dryer_feeder_geometry.json`
- `validation/fabrication_review/dryer_feeder_proof.json`

## 확인 결과

- 내경 140 mm metal hopper, cone, Ø36 outlet, lid와 vertical agitator가 하나의 hot-path tower로 정렬됨
- 원통부 40 mm insulation과 ventilated shield 사이 명목 6.0 mm air gap 확보
- paddle–hopper 15 mm, auger–housing 2 mm 명목 radial clearance이며 rigid-solid intersection 0 mm³
- double gate 아래 수평 auger와 tee inlet/outlet이 연결되고, housing 내부 bore가 연속됨
- 320×270 mm base의 3개 load-cell envelope에서 post/cross-rail을 거쳐 auger housing 하부까지 metal load path가 표시됨
- auger와 개별 service component는 210 mm cube 내에 들어가지만 hopper/shield assembly는 metal fabrication 대상임

## 시각 한계와 수정 이력

초기 housing은 outer cylinder와 tee를 각각 뚫은 뒤 fuse하여 접합부에 내부 막이 남았다. outer solids를 먼저 합치고 모든 bore를 union-cut하도록 바꾸어 auger와 housing의 교차 부피를 0 mm³로 수정했다. 초기 base에는 load cells만 있고 tower까지 구조 연결이 보이지 않아 3점 metal post/rail envelope를 추가했다.

Shield가 불투명하여 isometric render에서는 내부 hopper와 insulation이 가려지는 것이 정상이다. Component STEP/FCStd로 각 층을 별도 검토한다. 얇은 ring들이 반복되는 auger는 연속 flight가 아니라 pitch envelope이며 제조 형상이 아니다. Desiccant cylinders, blower/heater boxes와 motors는 구매품 keep-out이라 duct, seal, fastener와 wiring detail이 없다.

결론: 명목 hot-path 배치, air gap, 회전체 간극과 load-path 개념은 proof 통과다. 고온 재료 적합성, thermal bridge, 구조강도, load-cell 정확도, gate leakage, 연속 오거 이송, dew point와 PET 수분은 물리시험 전 승인 상태가 아니다.
