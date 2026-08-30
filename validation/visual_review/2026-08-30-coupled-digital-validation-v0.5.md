# Parent multimodal visual review — coupled-digital-validation-v0.5 (HISTORICAL ARCHIVE)

> 이 문서는 v0.5 아카이브 렌더의 이력이며 현재 release 판정에 사용하지 않는다. 현재 검토는 `2026-08-30-virtual-physics-closure-v0.5.1.md`를 따른다.

- 날짜: 2026-08-30
- 검토자: parent agent (멀티모달, 실제 PNG 픽셀 직접 확인)
- 대상 render: `renders/assembly/compact_full_assembly_isometric.png`, `renders/review/compact_exploded.png`, `renders/review/compact_section.png`, `renders/modules/shredder_drive_guard_removed.png`, `renders/modules/interchangeable_drive_interface.png`, `renders/cnc/extruder_die_exploded.png`, `renders/cnc/extruder_screw_barrel.png`
- 결과: **PASS_DIGITAL** (수정 필요 항목 없음, 관찰 3건 기록)

## 확인 내용

| 렌더 | 확인 항목 | 판정 |
|---|---|---|
| assembly isometric | 타이틀 `coupled-digital-validation-v0.5 \| 470 x 700 x 930 mm` revision 라벨 동기화. frame 내부에 shredder/extruder/spooler/gauge panel/PSU 모듈 배치, envelope 초과 요소 없음 | PASS |
| exploded by service module | 서비스 모듈 단위 분해가 의도된 offset만 가지며 유리/float 조각 없음 | PASS |
| center slab section (y=342..352) | 수직 단일 경로 hopper→flake bin→7-hook cutter+screen→수평 barrel(적색 band heater 블록 3개)→die(단자 히터)→puller→guide roller 순서가 architecture contract와 일치 | PASS |
| shredder drive (guard removed) | 12T motor sprocket(주황) → #35 chain → 30T cutter sprocket(보라), M3 Z16 phase gear pair 맞물림 간섭 없음 | PASS |
| interchangeable drive interface | DRV-01 universal plate + adapter slot pattern(slotted tension) + keyed hub + shear fuse 요소가 goal §3.3 교체성 요구와 일치 | PASS |
| extruder die exploded | EX-DIE-01..05 연결(Ø8 turn/breaker/insert/relief/gasket)과 die cartridge heater solid 확인 | PASS |
| screw/barrel RFQ | 16 mm × 16D screw/barrel 형상과 SCM440 RFQ 라벨 일치 | PASS |

## 관찰 (조치 불요, 기록 목적)

1. 전용 "thermal render" PNG는 없으며 thermal geometry 증거는 section view의 band heater 블록, die exploded의 cartridge, `exports/thermal/channel_schedule.csv`, heater RFQ PDF로 커버된다. 향후 thermal overlay render가 필요하면 `cad/generation/render_views.py` 확장으로 추가 가능.
2. assembly isometric에서 hopper 상부 커버 일부가 개방 상태로 렌더링된다(lid 개방 상태 표현). 서비스 접근성 표현으로 의도된 것이나, 운전 상태 렌더에서는 폐쇄 확인 필요.
3. 2020 profile 중심 frame(Option A) 유지. Frame Option A/B/C 비교와 shredder load loop 판단은 `analysis/structural/structural_validation_ko.md`와 engineering screening을 따르며, bearing center 상대변위 관점의 CalculiX 재검토는 Gate-3 전 물리 근거와 함께 재개방된다.

## 판정 근거

- 모든 렌더의 revision 문자열이 `coupled-digital-validation-v0.5`로 일치.
- virtual/surrogate 상태 표기가 제거되지 않았고(무시험 결과를 실험처럼 표기하지 않음), PHYSICAL_VALIDATION_PENDING 문구와 충돌 없음.
- 발견된 geometry 오류, 간섭, 라벨 불일치 0건 → before/after 수정 증거 불요.
