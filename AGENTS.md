# PPR C2 작업 규칙
- Active baseline은 c2/design/requirements.json 및 c2/src. 루트 C1 소스/CAD/BOM은 frozen reference이며 C2 확정값이 아니다.
- 공용 분쇄M1 한 개, 별도M2, 보유24V800W/240x120x65 PSU,500W 운전 cap, 전체 추가비100000KRW soft limit, PLA/PET/TPU를 유지한다. 모터 미선정.
- 모든 새 기하/열/성능 가정을 출처 및 증거 등급과 함께 기록한다. Kinematics/합성 수식은 실제 분쇄 성능 label이 아니다.
- ML은 보정된 DEM 또는 실험 응답에서만 성능을 학습한다. TPU의 파괴/인열/감김을 PLA 법칙으로 대체하지 않는다.
- 본체700x420x520mm 상한/보유 프로파일 변경은 사용자와 합의한다. C2 전체 기계 간섭/가공승인 상태를 부분 CAD PASS로 덮지 않는다.
- C1 root 검증/해시/기존 pre-push를 지우거나 우회하지 않는다. C2 tests 및 verify_artifacts를 함께 통과시킨다.
- 원본 dirty worktree에는 reset/clean/stash/checkout/일괄커밋 금지. 작업은 별도 clean worktree에서 진행하고 보존 브랜치를 변경하지 않는다.
- 구매/가공/통전은 승인 전 HOLD. 고하중 금속 지지, 가드, 비상정지, 독립 열차단과 인터록을 원가 절감용으로 삭제하지 않는다.
- 한국어로 결과와 미종결 항목을 보고한다. 코드MIT/하드웨어LICENSE-HARDWARE를 유지한다.
