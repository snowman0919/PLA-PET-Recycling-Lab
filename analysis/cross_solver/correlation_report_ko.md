# OpenModelica–CalculiX–Fusion 상관 보고서

현재 상태는 `PENDING_EXTERNAL_FUSION`이다. OpenModelica 74개 시나리오와 CalculiX 3단계 mesh 검증은 통과했지만 Autodesk Fusion 결과가 제공되거나 실행되지 않았다. 따라서 빈 Fusion cell을 수치로 채우거나 전체 교차 검증을 PASS로 표시하지 않는다.

확정된 내부 기준은 bearing plate fine displacement 0.252332 mm(수렴차 1.1644%), cutter shaft fine displacement 0.014140 mm(0.2769%), peak bearing load 1316.400717 N, peak cutter torque 21.993750 N·m이다. Fusion 반환물이 세 hash binding과 단위를 통과하면 `correlation_matrix.csv`를 갱신하고 독립 허용치와 solver 간 편차를 모두 판정한다.
