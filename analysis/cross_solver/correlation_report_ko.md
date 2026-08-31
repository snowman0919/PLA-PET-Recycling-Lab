# OpenModelica–CalculiX–Fusion 상관 보고서

현재 상태는 `PENDING_EXTERNAL_FUSION`이다. 동결 baseline OpenModelica 74개 시나리오, v0.6.2.1 shadow 24개 시나리오, CalculiX 3단계 mesh 검증은 통과했지만 Autodesk Fusion 결과가 제공되거나 실행되지 않았다. 따라서 빈 Fusion cell을 수치로 채우거나 전체 교차 검증을 PASS로 표시하지 않는다.

확정된 내부 기준은 bearing plate fine displacement 0.355869 mm(수렴차 1.1644%), cutter shaft fine displacement 0.017715 mm(0.3119%), peak bearing load 1856.544176 N, peak cutter torque 21.993750 N·m이다. 새 LC11 경계는 feeder attachment의 2.2 N·m와 5.4 N이다. Fusion 반환물이 source/STEP/load-manifest hash, 단위, mesh 증거를 통과하면 `correlation_matrix.csv`를 갱신하고 독립 허용치와 solver 간 편차를 판정한다.

필수 Fusion case는 LC02, LC04, LC05, LC07, LC08, LC08+LC06, LC10 및 LC11이다. 현재 모든 Fusion 열은 의도적으로 비어 있으며 분류는 `INSUFFICIENT_EVIDENCE`다.

Windows worker `win`은 세 차례 재접속 모두 timeout이었고 마지막 시각은 `2026-08-31T07:49:00Z`다. 따라서 실제 solve, mesh convergence export, result hash 수집은 수행되지 않았다.
