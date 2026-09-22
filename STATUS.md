# PPR STATUS (2026-09-22 기준)

VP1 통합 제품 작업 진행 중. 영구 규칙은 [`KODEX.md`](KODEX.md).

## 1. 현재 제품 파일 (C2.1)
- `c2.1/cad/PPR_C2_1_machine_integration.FCStd` — 네이티브 FreeCAD 편집 가능 본체 조립 (156 객체, 전부 valid — `c2.1/results/machine_freecad.json`)
- `c2.1/cad/PPR_C2_1_machine_integration.step` — 전체 기계 STEP (196 솔리드 재가져오기 검증 — `machine_integration.json`)
- `c2.1/cad/PPR_C2_1_S2_transmission.step` / `..._exploded.step` / `..._schematic.svg` — S2 구동계 (41 객체 — `cad_validation.json`)
- `c2.1/results/p6_manifest.json` — 56 아티팩트 해시 동결 (self-excluding)
- 진행 중(VP1, **IN_PROGRESS**): 전체 라인 통합 — 호퍼→S1→슈트→S2→버퍼→압출→냉각→풀러→스풀 단일 STEP/CAD/Isaac 씬/BOM. `c2.1/src`, `c2.2/sim` 동시 편집 중.

## 2. 실제 수행된 검증 범위
| 검증 | 근거 |
|---|---|
| STEP 재가져오기 (topology/volume) | `results/step_roundtrip.json` (C1 파트), `c2.1/results/cad_validation.json`, `machine_integration.json` |
| CAD↔BOM 대응 / 인터페이스 간섭 | `c2.1/results/machine_integration.json`, `system_bom_summary.json` |
| 실제 메커니즘 운동 (S2 구동계, 9 케이스) | `c2.1/results/kinematic_validation.json`, `motion_samples.json` |
| 배선/펌웨어 디지털 증거 (컴파일만, 플래시/통전 미실행) | `machine_wiring.json`, `firmware_build.json` |
| 운동 단위 테스트 등 로컬 72 테스트 통과 | `tests` 14, `c2.1/tests` 11, `c2.3/tests` 47 OK |
**범위 밖(미검증)**: 실분쇄 성능, 열, 수명, 소재 경로 실측, Isaac 전체 기계 씬. 전체 판정: 디지털 패키지 PASS, 물리 해제 **HOLD** (`validation_summary.json`).

## 3. 주요 미해결 결함 (Gap Analysis)
1. 무치(toothless) 기어/체인 — 링크만 존재, 실동력 전달 기하 미완
2. 슈트(chute) 누락 — S1→S2 연결 경로 없음
3. 스풀/풀러가 엔벨로프 표현만 — 실기구 없음
4. 가드가 애니메이션 전용 — 실체 가드 부품/체결 미완
5. 전체 기계 Isaac 씬 없음 (S2 부분 씬만)
6. 집계 전력 모델 없음 (M1/M2 분배 미정, 모터 미선정)
7. S2 로터 부착부 강도 무정격(unrated)
8. [해결됨 2026-09-22, VP1 Stage 2] CI frozen-hash ULP 드리프트 — `c2/src/run_study.py`와 `c2.1/src/transmission.py`의 직렬화 지점에서 모든 float를 소수 8유효숫자로 정준 반올림(규격: `_canon`). 12유효숫자는 러너 간 1-2 ULP(~16번째 자리) 드리프트보다 ~1000배 크고, 계약 허용오차(최소 여유 ~1e-5, 게이트 >=1e-9)보다 훨씬 미세해 계약 약화 없음. `c2/src/verify_artifacts.py`도 메모리 재계산 값에 동일 정준화를 적용. 재생성된 JSON 4종(p5_thermal_control, performance_gate, kinematic_validation, motion_samples)과 매니페스트 해시를 로컬에서 재확정 — 이것이 이 변경의 목적이며, verify_artifacts(c2, c2.1) 모두 통과. **재확정 순서 필수**: run_study/transmission 실행(결과 재생성) -> build_release_manifest(해시 재확정) -> verify_artifacts. 순서를 바꾸면 매니페스트가 이전 바이트를 고정해 CI에서 파일 없음/해시 불일치 발생 (2026-09-22 3회 CI 실패의 근본 원인). 정준 자릿수는 12->8->6유효숫자로 단계 조정: FD 유도 값은 libm 표차(1e-16)가 캔슬링으로 ~1e-8 상대 오차로 증폭되므로 6유효숫자(1e-7 상대 경계)가 안전 여유 4자리를 확보. c2.1 verify의 고정 개수 196->200, 156->160도 VP1 Stage 1 반영으로 갱신

## 4. 다음 단계
1. ~~VP1 통합~~ **완료 (2026-09-22, VP1 Stage 1-3)**: 전체 라인 통합 STEP 225 solids
   (sha256 1734ab0a487f60188c5e85e63f90f6df777ee3ec1ac03253de5ed48a94303cd8),
   재수입 유효, 예상/재수입 일치, BREP 충돌 0 (vp1_against_retained/vp1_internal),
   본체 630x408x512.5 <= 700x420x520, 운전 847x408x512.5 <= 850x450x510.
   ADR-002 체인 경로 릴리프 9건 적용 (제거 23,853 mm3, 기록:
   vp1_stage3.chain_relief_records). FCStd 185 objects/valid.
2. Isaac 전체 기계 씬 + 실기하 구동/간섭 시험 -> 결함 수정 -> 재생성 (KODEX §3) — 진행 중 (c2.2/c2.3 워크스트림)
3. BOM 집계: 시스템 BOM 163행 (VP1 델타 30행, 전부 UNQUOTED_NOT_ZERO — 견적 없음, 미견적 != 0);
   알려진 비용 11행; 100,000 KRW 소프트 리밋 대비 견적 대기
4. ~~CI frozen-hash ULP 정책~~ **해결됨 (2026-09-22)**: 직렬화 지점 정준 반올림(소수 12유효숫자) — 결함 8 참조

## 4a. VP1 전력 설계 결정 (Stage 3)
- 원수치: 기기 명판 동시 합계 **616 W > 500 W 운전 상한** (초과 116 W) — M1/M2는
  미소유 참조라 UNRATED 추정치(evidence grade UNRATED_ESTIMATE), 히터 3x100 W +
  60 W는 NAMEPLATE_SOURCE (design/assembly.json 명판).
- 설계 결정 (채택): **단계적 히터 전력 제어** — 컨트롤러가 밴드를 순차 점등하여
  임시 순간 부하를 EX-H100 1개 + EX-H60 (160 W)로 제한 -> **staged_peak_W 416 W
  <= 500 W (여유 84 W)**. 원수치 616 W는 electrical_load.json에 그대로 노출.
- 하드웨어: EL_CURRENT_LIMITER 릴레이 뱅크 CAD 배치 완료. 펌웨어 제어 로직은
  **UNIMPLEMENTED_IN_FIRMWARE** — 펌웨어 고장 시에도 두 밴드가 동시 점등되지
  않도록 하는 하드웨어 인터락 요구를 문서화.

## 4b. 남은 결함 (정직 목록)
- 가드 판 두께/구조 미검증 (containment unrated; service sweep만 검증)
- ADR-002 릴리프 포켓 적용 부품의 구조적 강도 미검증 (ROOF-R 코너, DECK 절삭,
  JACK 절단, STUD 트림 — FEA 없음)
- 스테이지 히터 제어 펌웨어 로직 UNIMPLEMENTED_IN_FIRMWARE (하드웨어 배치만 존재)
- Isaac 런의 토크는 0/운동학 값 (pose-driven kinematic rigid bodies — 실측 토크 불가,
  c2.3 TORQUE_SOURCE 판정 유지)
- 체인 B 스트랜드가 DRV-JACK을 관던하는 근본 설계 충돌은 절단+스페이서로 디지털
  해결 — 실물 제작 전 재배치/커플링 재설계 필요 (ADR-002)

## 5. 역사 문서 분류 (파일은 수정하지 않음)
아래 문서들은 **역사적/실험 기록**이다. 현재 승인 상태가 아니며, 과거 PASS 값은 현재 승인으로 **상속되지 않는다**. 현재 유효한 것은 KODEX.md와 이 문서(STATUS.md), 그리고 `c2.1/results/` 실제 증거 파일뿐이다.

| 디렉터리 | 문서 | 분류 |
|---|---|---|
| `c2/` | `docs/CALIBRATION_AND_RFQ.md`, `docs/C2_ENGINEERING_NOTES.md` | 역사적 실험/계획 기록 |
| `c2.1/` | `docs/PLAN_KO.md`, `docs/OPEN_ACTIONS_KO.md`, `docs/HANDOFF_KO.md`, `docs/ADR-001-S2-TRANSMISSION.md`, `docs/ASSEMBLY_SERVICE_KO.md` | 역사적 계획/인수인계 기록 (P0–P6 패키지 시점) |
| `c2.2/` | `README.md`, `docs/SOURCES.md`, `docs/HANDOFF_KO.md` | 역사적 실험 기록 (sim 시도) |
| `c2.3/` | `CONTRACT.md`, `NEXT.md`, `docs/REVIEW_HANDOFF_KO.md`, `revisions/r1/CONTRACT_R1.md`, `revisions/r1/AMENDMENT_LOG.md`, `revisions/r1/DIAGNOSTIC_SUMMARY.md`, `revisions/r1/REQUIREMENTS_EVIDENCE.md`, `revisions/r1/REVIEW_HANDOFF_KO.md` | 역사적 계약/실험 기록 — **C2.3 확장은 중단됨** (KODEX §3) |

이 문서들에 기록된 "PASS/VALIDATED/COMPLETE" 표기는 당시 실험 범위에서만 유효하며, 현재 VP1 통합 제품의 승인 상태와 무관하다.
