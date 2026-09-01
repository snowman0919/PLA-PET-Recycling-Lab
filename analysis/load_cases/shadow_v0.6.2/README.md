# v0.6.2 shadow 하중 네임스페이스

이 디렉터리는 v0.6.2 제어·구동 변경이 구조 하중 envelope에 미치는 영향을
기존 Fusion 입력과 분리해 검토하는 전용 네임스페이스다.

- source of truth 비교: `analysis/fusion_delta_queue/shadow_envelope_comparison.json`
- 현재 판정: 4개 구조 하중 모두 기존 envelope 대비 변화 `0.0`, Fusion 재실행 불필요
- 동결 원칙: `exports/fusion_validation/loads/`, `run_binding.json`, STEP와 manifest는
  이 shadow 검토가 명시적으로 `FUSION_RERUN_REQUIRED`를 내기 전까지 수정하지 않는다.
- 실제 Fusion 결과는 자동 평균하지 않고 `analysis/cross_solver/import_fusion_results.py`의
  결합 검증을 통과한 뒤 상관 검토 대상으로만 승격한다.

이 판정은 디지털 시뮬레이션 결과이며 실제 물리 시험 완료를 뜻하지 않는다.
