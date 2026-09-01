# v0.6.2.1 Fusion deferred release 정책

## 결정

2026-09-01 사용자 결정에 따라 v0.6.2.1은 비가격·비Fusion 기술 blocker P0-A~K를
종결한다. Autodesk Fusion 실제 실행과 Fusion/CalculiX/closed-form 수치 상관은
`POST_V0.6.2.1_MACBOOK_STAGE`로 이관한다. 이 결정은 Fusion을 통과시킨 것이 아니다.

정책 source of truth는 `validation/fusion_policy_v0.6.2.1.json`이며 선택값은
`FUSION_GATE_POLICY=DEFERRED`다. release 상태는 다음과 같다.

```text
release_state=TECHNICAL_CLOSURE_BASELINE
hardware_adapter_state=HARDWARE_ADAPTER_VALIDATED
actuation_state=CLOSED_LOOP_ACTUATION_VALIDATED
process_feed_state=PROCESS_FEED_VIRTUAL_VALIDATED
virtual_physics_state=VIRTUAL_PHYSICS_VALIDATED
cross_solver_state=CROSS_SOLVER_VALIDATION_DEFERRED
fusion_state=DEFERRED_TO_POST_V0.6.2.1_MACBOOK_STAGE
price_state=INFORMATIONAL_NON_BLOCKING
empirical_state=EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN
procurement_gate=USER_APPROVAL_REQUIRED
commissioning_gate=USER_APPROVAL_REQUIRED
```

`CROSS_SOLVER_VALIDATED`와 `FUSION_VALIDATED`는 실제 Autodesk 결과를 import하고
검토하기 전까지 금지한다.

## Fail-closed 경계

- 결과가 없으면 `DEFERRED`이며 v0.6.2.1 기술 release를 차단하지 않는다.
- legacy와 LC11 package의 source/STEP/model/load/run-binding hash 검사는 항상 필수다.
- 실제 result CSV가 존재하면 `DEFERRED`에서도 importer/schema/unit/evidence hash 검사를
  통과해야 한다. malformed, stale, orphan 또는 결박이 어긋난 결과는 release를 차단한다.
- `DEFERRED` gate 출력은 `solver_pass=false`를 명시하며 PASS로 변환하지 않는다.
- placeholder Fusion 수치나 빈 cell 대체값을 생성하지 않는다.

검증 명령은 다음과 같다.

```bash
python3 validation/run_v0621.py --fusion-policy deferred
python3 validation/exact_head_evidence_v0621.py \
  --stage CI-FULL --fusion-policy deferred
```

후속 MacBook stage는 동결된 최종 handoff package로만 실행한다. FreeCAD Python은 계속
지배 형상이며 Inventor는 독립 consumer로만 사용한다. 실제 결과가 생기기 전에는 이
정책 문서를 solver 증거나 안전 인증으로 사용할 수 없다.
