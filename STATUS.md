# PPR VP1 현재 상태 (2026-09-23)

현재 설계 규칙은 `KODEX.md`, 기계 판독 원본은 `c2.1/results/`와
`c2.2/results/full_machine/`이다. 이 문서는 과거 196/225 솔리드 수치와
미구현 목록을 현재 사실로 승계하지 않는다.

## 통합 제품

- `c2.1/cad/PPR_VP1.step`: 호퍼→S1→능동 슈트→S2→버퍼→압출→냉각→
  1.75 mm 풀러→스풀을 포함한 전체 조립. 편집 가능한 원본은
  `c2.1/cad/PPR_C2_1_machine_integration.FCStd`와 `c2.1/src/`의
  FreeCAD/CadQuery 파라미터 생성기다.
- `c2.2/sim/assets/usd/full_machine.usda`: 동일 STEP의 솔리드별 메시,
  구동 관절, 기능 보존 collider를 가진 실행 씬. `sim/assets/out/full/bodies.json`
  및 sidecar가 STEP/메시 해시를 연결한다.
- `c2.1/bom/system_bom.csv`/`.xlsx`: 활성 시스템 BOM. 미견적 항목을 0원으로
  취급하지 않는다.
- `c2.2/results/full_machine/reviewer_scenes/`: 전체 조립, 구동계 중간 회전,
  이송 슈트와 프로브, 풀러·권취 장면 4장과 `index.json`.

## 수정된 구조와 디지털 증거

- DRV-JACK은 절단 없는 연속 축이고 체인 B는 잭샤프트에서 S2로 간다.
  M2 참조 외형을 파내던 중복 헬리컬 물림을 제거했다. S1/S2는 공용 M1
  단일 입력에서 종속되고 S2에 제2 모터가 없다. 구동비·무간섭은 디지털
  검증 대상이며 토크·베어링 반력·치형 하중의 실물 정격은 아니다.
- 풀러는 1.75 mm 필라멘트에 대해 1.5–3.0 mm 스프링 가압 니프와
  통과 공간/그립 별도 게이트를 갖는다. 양단 스풀 베어링, 모터-드럼
  토크 결합, 트래버스·가이드 눈을 조립 형상으로 포함한다.
- 수동 계단/패들/얕은 오거를 폐기하고 x237..354의 능동 오거,
  체인·웜 감속, 우선회 횡이송 스크루를 배치했다. S1 광폭 벨트와
  양쪽 횡방향 스크루, 중앙 17 mm 연속 벨트를 조립했지만 **광폭
  배출물의 주 오거 인수는 미해결**이다. 현재 STEP
  `d44b8c2f…`는 **251 객체/275 솔리드**를 재가져왔고 예상 밖
  BRep 간섭 0건이다. 본체 630×414×510 mm와 운전 포락
  847×414×510 mm는 디지털 한계 안이다. 이는 이송 성능이 아니다.
- 같은 STEP/USD `0a1e8eec…`의 Isaac 국부 투입(각 단계 Ø3 mm
  10개, Ø1.5 mm 10개, 판형 2개, 60 s/24,000 step, M1 5회전):
  호퍼 경계 22/22, S1 배출면 22/22이나 **주 오거 픽업 0/22**,
  월드 유실 6/22. 별도 슈트 주입에서 x335 이후 15/22,
  S2 입구 +Y 횡단 8/22, 월드 유실 4/22. 별도 S2 주입에서
  21/22가 수용 경로에 있었으나 월드 유실 13/22, 스크린
  bounding band 1/22이다. 각 국부 주입은 연결 이송이 아니다.
- 동일 씬의 연결 시험(Ø3 mm 100개와 Ø1.5 mm 100개,
  19,200 step/96 s/M1 8회전)은 구동 추적 합격, 예상 밖
  접촉 보고 0건, 스크린 *bounding box 근접* **0/200**이다.
  `product_flow_verified=false`, `LOCALIZED_BLOCKED`. 국부
  시험에서 스크린 band/평면을 넘은 것으로 분류된 입자는
  구멍 통과·압출·완성 필라멘트의 증거가 아니다.
- 중앙 차선만 투입한 비채택 탐색에서는 5/22가 x237 픽업에
  진입했으나 x242..243에서 정체했다. 중앙 벨트 종단 이후
  플라이트 접촉이 이어지지 않는다. 현재 광폭 분포의 0/22를
  이 좁은 투입 결과로 대체하지 않는다. cap bore 앞 횡이송
  구동 플라이트의 **3.28 mm 비구동 공백**도 남았다.
- 전력: 보유 PSU 24 V×33 A, 명판 800 W, 전류 정격 강제 상한 792 W,
  소프트 운전 목표 500 W. host-tested 제어 core 19건에서 히터 밴드
  동시 점등 배제, 500 W 초과 경고·허용, 792 W 초과 거부를 확인했다.
  가상 운전 1800 s의 모델 피크는 416 W(목표 여유 84 W)이며
  566 W 요구는 경고 허용, 816 W 요구는 거부한다. M1/M2/팬 전력은
  **UNRATED_ESTIMATE**이지 실측 소비전력이 아니다.

## 미완료 기능과 물리 HOLD

- **현재 광폭 S1 오거 픽업 0/22**. 벨트에서 횡방향 플라이트,
  중앙 벨트, 주 오거 플라이트까지 모든 폭에서 연속된 능동
  접촉을 입증하지 못했다. 중앙 제한 투입에서도 벨트 끝
  x242..243에서 멈춘다. 프레임·S2 지지부 하중 경로를
  보존한 재설계가 필요하며 수동 램프의 공간 간극만으로
  수송 합격을 주장하지 않는다.
- 횡이송 플라이트 끝 y251.72와 S2 입구 y255 사이
  3.28 mm 공백은 `path_check` FAIL. cap 보어와 구동축의
  간섭을 피하면서 능동 접촉을 연결해야 한다. 별도 슈트
  투입의 S2 입구 8/22도 배출 안정성을 증명하지 않는다.
- S2 cap 후방의 버퍼 포집, 스크린 **구멍** 통과, 버퍼에서
  압출 다이까지의 용융 경로, 실제 연속 필라멘트 출력 모두
  미검증이다. 연결 시험 스크린 bbox 0/200과 국부 band
  관측을 제품 PASS로 전환하지 않는다.
- 모터, 웜/휠, 축·베어링·coupling, 체인, 가드 containment,
  E-stop/lid/service interlock, thermal fuse/branch fuse의 물리 정격과
  작동 시험은 없다. 소재별 파쇄 성능·실제 처리량·열·마모·수명도 미검증이다.
- 구매·가공·통전·실물 운전·main 병합은 명시적 사용자 승인 전 **HOLD**.
  개발 브랜치의 커밋/푸시와 Draft PR 갱신은 별개다.

## 재현 순서

`c2.1/src/build_machine_integration.py` → `build_machine_freecad.py` →
`path_check.py`/`build_system_bom.py`/`build_machine_wiring.py`/
`build_firmware.py`/`power_sim.py` → `c2.2/sim/assets/convert.py --full` →
`c2.2/sim/full_machine.py` → `c2.2/sim/flow_localize.py` →
`c2.2/sim/verify_full.py` → `c2.2/sim/render_reviewer_scenes.py` 순서다.
최종 결과 생성 후 `c2.1/src/build_release_manifest.py`를 마지막에 실행하고
`c2.1/src/verify_artifacts.py`로 해시·계약을 검사한다. 실제 실행 명령의
세부 인자는 각 스크립트 `--help`와 PR 검증 기록을 따른다.

## 지식 그래프 갱신 경계

`graphify update .`로 코드 AST를 재추출해 1750 노드/3162 간선/
195 커뮤니티로 갱신했다(외부 API 토큰 0). `GRAPH_REPORT.md`의
God Nodes, Surprising Connections, Suggested Questions를 검토했다.
과거 변경 문서 8건의 호스트 시맨틱 캐시는 남지만 이번 STATUS
수정의 시맨틱 추출 완료를 주장하지 않는다. 스키마 confidence
경고 1건과 전체 코퍼스의 시맨틱 미완료·추출 품질은 HOLD이며
물리 또는 제품 흐름 증거를 그래프 연결로 대신하지 않는다.
