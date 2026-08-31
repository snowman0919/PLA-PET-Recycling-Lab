# Fusion 결과 수신·correlation

`analysis/cross_solver/import_fusion_results.py`는 engineering source SHA, STEP SHA-256, load manifest SHA-256, case ID, study type, unit, geometry filename, evidence file SHA를 모두 확인한다. 하나라도 다르면 `INVALID_BINDING`이고 값은 correlation에 들어가지 않는다.

검증된 행도 즉시 PASS가 아니라 `CORRELATION_REVIEW`다. closed-form/CalculiX/Fusion의 reaction balance, displacement, regional non-singular stress, mode, temperature/gradient를 개별 비교하며 불일치 solver를 평균하지 않는다. 분류는 `AGREE`, `EXPLAINED_DIFFERENCE`, `UNRESOLVED_DIFFERENCE`, `INVALID_INPUT`, `INSUFFICIENT_EVIDENCE`다.

현재 result template에는 실제 행이 없어 `PENDING_EXTERNAL_EXECUTION`이다.
