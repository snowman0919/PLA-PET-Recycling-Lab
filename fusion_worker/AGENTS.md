# Fusion worker 제한

- `exports/fusion_validation/geometry/*.step`를 지배 형상으로 사용하고 Fusion에서 치수를 재정의하지 않는다.
- `run_binding.json`의 source Git SHA, STEP SHA-256, load manifest SHA-256를 실행 전후 검증한다.
- Autodesk 계정 로그인, cloud solve 동의, 비용 발생, 결과 공개는 사용자가 직접 승인한다.
- 실제 실행하지 않은 study를 PASS로 기록하지 않는다. 오류·timeout·license 부재는 `BLOCKED_EXTERNAL` 또는 `PENDING`이다.
- 결과는 `results/fusion_result_template.csv` 형식과 원본 증거 파일 SHA-256으로 반환한다.
- E-stop, interlock, thermal fuse 및 물리 lockout 안전 판정을 solver 결과로 대체하지 않는다.
