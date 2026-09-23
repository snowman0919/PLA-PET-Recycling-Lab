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
- 수동 계단/패들/얕은 오거는 이전 이송 시험에서 폐기했다. 현재 형상은
  x237..354의 4회전 능동 오거, 35링크 오프셋 체인, 2-start/16T 웜,
  y축 횡이송 스크루와 12T 기어 3개를 포함한다. 잭샤프트 제2 24T도
  별도 키/키시트로 결합한다. BRep 재가져오기 **235 객체/253 솔리드**,
  예상 밖 통합 간섭 0건, FreeCAD **194/194 유효 객체**다. 본체
  630×408×510 mm 제한을 충족한다.
- **소재 이송은 HOLD**: 현재 STEP `0753f249…`/USD `594b77e4…`에서
  8-cycle 국부 시험은 호퍼 입구 22/22, S1 배출 판정면 22/22지만
  S1에서 오거 픽업 5/22, 슈트 x335 도달 21/22에서 S2 입구
  +Y 횡단 0/22, x335 이후 월드 유실 13/22다. S2 국부 주입
  22/22는 입구부터 별도 주입한 결과이며 연결 성공이 아니다.
  19,200 step(96 s, 8 입력 회전) 연결 실행의 S2 스크린 근접은
  **0/200**, 제품 흐름 검증은 false다. 구동 추적 PASS와
  무예상 접촉은 물질 경로/스크린 구멍 통과/압출 제품의 증거가 아니다.
  `path_check.json`도 플라이트-입구 수동 간극 3.28 mm 때문에
  `all_material_path_clear=false`다.
- 전력: 보유 PSU 24 V×33 A, 명판 800 W, 전류 정격 강제 상한 792 W,
  소프트 운전 목표 500 W. host-tested 제어 core 19건에서 히터 밴드
  동시 점등 배제, 500 W 초과 경고·허용, 792 W 초과 거부를 확인했다.
  가상 운전 1800 s의 모델 피크는 416 W(목표 여유 84 W)이며
  566 W 요구는 경고 허용, 816 W 요구는 거부한다. M1/M2/팬 전력은
  **UNRATED_ESTIMATE**이지 실측 소비전력이 아니다.

## 미완료 기능과 물리 HOLD

- S1 배출은 주 오거 픽업이 5/22에 그치고, 오거의 x354 끝에서
  횡이송 스크루/입구까지 연속 포집되지 않아 0/22만 S2 입구를
  횡단한다. 1.5/3 mm 파편의 포집·낙하·횡이송 경로를 실제 CAD와
  충돌 형상에서 다시 설계하고 STEP→USD→국부/연결 시험을 재실행해야
  한다. 스크린 *근접*도 구멍 통과나 완성 필라멘트가 아니다.
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

`graphify update .`로 코드 AST를 갱신하고 이번 변경 문서 8건을
호스트 시맨틱 추출(44 노드/34 간선/1 하이퍼간선)해 캐시 8/8을
확인했다. 병합 그래프는 1730 노드/3109 간선이다.
`graphify-out/GRAPH_REPORT.md`의 God Nodes, Surprising Connections,
Suggested Questions를 검토했다. Ollama 전체 코퍼스 증분 실행은
`gemma4:e2b`에서 72/86 파일 누락·69개 응답 불완전,
`Qwythos-v2-9B:Q4`의 작은 청크 재시도는 20개 중 14개에서 시간
초과했다. **변경 문서 8건은 갱신 완료**, 그 외 코퍼스의 시맨틱
미완료·추출 품질은 완전한 그래프라고 주장하지 않는다. 외부 유료
API 호출은 없었다.
