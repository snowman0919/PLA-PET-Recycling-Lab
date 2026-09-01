# v0.6.2.1 cross-solver release 보고서

현재 v0.6.2.1 정책은 `CROSS_SOLVER_VALIDATION_DEFERRED`이며 실제 Fusion solver 판정은 `NOT_RUN`이다. 사용자 결정으로 외부 수치 상관은 post-v0.6.2.1 MacBook stage로 이관했으며, `DEFERRED`는 PASS가 아니다.

OpenModelica 1.27.0 DASSL은 v0.6.2.1 24개 scenario를 실제 실행해 24/24 PASS했다. 동결 기계 envelope 대비 cutter torque, phase torque, bearing load, chain force 변화는 모두 0%다. CalculiX의 기존 coarse/medium/fine 기준은 유지된다.

Autodesk Fusion의 mandatory LC02, LC04, LC05, LC07, LC08, LC08+LC06, LC10과 신규 LC11 결과가 없다. 따라서 mesh convergence, reaction balance, global displacement 및 regional stress correlation은 미판정이며 `CROSS_SOLVER_VALIDATED`와 `FUSION_VALIDATED`를 사용하지 않는다. 다만 package source/STEP/model/load/run-binding hash 무결성은 v0.6.2.1 필수 gate로 유지한다.

Windows worker `win`은 여섯 차례 재시도 뒤에도 마지막 `2026-08-31T08:22:28Z` 접속에서 12초 SSH connect timeout으로 접근할 수 없었다. 로컬 Tailscale backend는 `Running`이지만 Pocket4 peer는 `Online=false`, 마지막 관측은 `2026-08-31T06:50:00.1Z`이고 최신 Tailscale ping 3회도 모두 응답이 없었다. 따라서 범위는 Fusion 계산 실패가 아니라 worker device/Tailscale peer가 SSH 이전 단계에서 offline인 상태다. 이전 연결에서 Fusion 2704.1.53 process와 interactive session은 확인했지만 solve/result export는 실행되지 않았다. 결과가 없는 상태에서 저장된 PASS나 빈 cell을 대체 증거로 사용하지 않는다.

`fusion_worker/scripts/prepare_run.py`는 legacy mandatory case와 LC11에 대해 현재 checkout과 engineering source를 분리해 검증한다. source commit ancestor, source STEP Git object, 현재 model/load manifest hash, LC08+LC06 관련 case 결박, coarse/medium/fine 계획과 Fusion version을 manifest에 고정하며 결과값이나 PASS를 생성하지 않는다. 로컬 handoff 검증은 8개 필수 실행 조합을 모두 PASS했지만 실제 Fusion 실행 증거는 아니다.

필수 허용치는 reaction/load balance 5% 이하, global displacement 15% 이하, regional stress 20–25% 이하이다. singular point stress를 대표값으로 사용하지 않는다. 결과가 수신되면 `analysis/cross_solver/import_fusion_results.py`에서 source Git SHA, STEP SHA-256, load-case manifest SHA-256, 단위 및 evidence hash를 먼저 검증한다.

가격은 `INFORMATIONAL_NON_BLOCKING`이며 구매와 powered commissioning은 사용자 승인 전 금지다.
