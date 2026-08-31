# v0.6.2.1 cross-solver release 보고서

현재 release 판정은 `UNMET — PENDING_EXTERNAL_FUSION`이다.

OpenModelica 1.27.0 DASSL은 v0.6.2.1 24개 scenario를 실제 실행해 24/24 PASS했다. 동결 기계 envelope 대비 cutter torque, phase torque, bearing load, chain force 변화는 모두 0%다. CalculiX의 기존 coarse/medium/fine 기준은 유지된다.

Autodesk Fusion의 mandatory LC02, LC04, LC05, LC07, LC08, LC08+LC06, LC10과 신규 LC11 결과가 없다. 따라서 mesh convergence, source/hash binding, reaction balance, global displacement 및 regional stress correlation을 판정할 수 없고 `CROSS_SOLVER_VALIDATED`를 사용하지 않는다.

Windows worker `win`은 세 차례 재시도 뒤에도 마지막 12초 SSH connect timeout으로 접근할 수 없었다. 이전 연결에서 Fusion 2704.1.53 process와 interactive session은 확인했지만 solve/result export는 실행되지 않았다. 이는 계산 실패가 아니라 외부 GUI worker 접근 불가이며, 결과가 없는 상태에서 저장된 PASS나 빈 cell을 대체 증거로 사용하지 않는다.

필수 허용치는 reaction/load balance 5% 이하, global displacement 15% 이하, regional stress 20–25% 이하이다. singular point stress를 대표값으로 사용하지 않는다. 결과가 수신되면 `analysis/cross_solver/import_fusion_results.py`에서 source Git SHA, STEP SHA-256, load-case manifest SHA-256, 단위 및 evidence hash를 먼저 검증한다.

가격은 `INFORMATIONAL_NON_BLOCKING`이며 구매와 powered commissioning은 사용자 승인 전 금지다.
