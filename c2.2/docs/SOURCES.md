# C2.2 VP1 실행 씬 출처와 증거 경계

## 활성 원본

- 파라미터: `../design/parameters.json`, `../design/assembly.json`,
  `../c2/design/requirements.json`, `../c2.1/design/requirements.json`.
- 전체 CAD: `../c2.1/src/build_machine_integration.py` 및 관련 파트 생성기
  (`chute.py`, `drive_teeth.py`, `winder.py`, `guards.py`,
  `electrical_bay.py`) → `../c2.1/cad/PPR_VP1.step`.
- 네이티브 조립: `../c2.1/src/build_machine_freecad.py` →
  `../c2.1/cad/PPR_C2_1_machine_integration.FCStd`.
- 기하 판정: `../c2.1/results/machine_integration.json`,
  `../c2.1/results/path_check.json`.
- STEP→STL/sidecar: `sim/assets/convert.py` →
  `sim/assets/out/full/bodies.json`. 동일 SHA의 USD는
  `sim/assets/usd/full_machine.usda`다.
- 실제 운동·소재 경로: `sim/full_machine.py`, `sim/verify_full.py`,
  `sim/flow_localize.py`, `results/full_machine/`의 JSON과 로그.
  검토 이미지는 `sim/render_reviewer_scenes.py`의 출력이다.

현재 STEP/USD 해시, 객체 수, 단계별 통과·정체·유실 수는 루트
`../STATUS.md`와 해당 결과 파일의 SHA 필드를 따른다. 과거 196/225
솔리드 STEP 해시와 단독 프록시의 DERIVED 전달 박스는 최종 VP1의 출처가
아니다.

## 디지털 검증과 물리 검증의 구분

- STEP 재가져오기와 BRep 간섭, USD 메시/충돌체 검사, Isaac의 경로
  추적은 명시된 자세·프로브·시간 구간에 한정된다.
- S2 q=8/e=7 mm, 입력 +120 rpm/출력 -15 rpm은 기구학 명목값이다.
  실제 체인 효율, 모터 토크, 베어링 하중, 웜/휠 정격의 물리 검증이 아니다.
- PLA/PET/TPU 파괴·마찰·입도·처리량·열·마모 데이터는 미보정이다.
  과거 `results/i*`, `results/dyn_*`는 별도 프록시/소규모 시뮬레이션
  이력이며 전체 제품의 이송 성공 증거로 합산하지 않는다.
- PSU 24V 33A/명판 800W, 500W 소프트 운전 목표, 792W 전류 정격
  강제 상한. M1/M2는 미선정이며 부품 구매·제작·통전·main 병합은 HOLD.

## 정책

현재 revision의 승인 경계는 원본 저장소
`/home/monad/develop/PPR/docs/final/release_notes_v1.0.0-rc1_ko.md`를
읽기 전용으로 확인했다. 개발 PR 공개는 허용되지만 물리 해제와
main 병합을 자동 승인하지 않는다.
