# v0.6.2.1 기술 blocker closure 보고서

## 판정

P0-A~K는 가상/설계 범위에서 통과했다. 2026-09-01 사용자 결정으로 P0-L 실제 Fusion 실행은 `DEFERRED_TO_POST_V0.6.2.1_MACBOOK_STAGE`로 이관했다. 이는 Fusion PASS가 아니며, v0.6.2.1의 release target은 `TECHNICAL_CLOSURE_BASELINE` / `CROSS_SOLVER_VALIDATION_DEFERRED`다.

## 확인된 결과

- 소스 v0.6.2: `f9fde47359ef84744daf1a9279040c507ef60497`.
- 가격: 198,729 KRW 정보성 추정, 기술 release 비차단, 구매 승인 필요.
- Tach: 6/12/20/20 PPR, nominal 오차 모두 1% 미만, timeout/rollover/missing/bounce mutation 통과.
- Actuation: shredder/screw/puller/spooler production PI 경로, anti-windup, tach-loss, saturation 보호.
- Spool/traverse: volume-conservation radius, packing factor 0.88 test, explicit homing 후에만 spool eligibility.
- Process: PLA/PET nominal 95.856–100.243 g/h, starvation 1 s, bridge 2 cycle, passive recirculation 검증.
- OpenModelica: 실제 1.27.0 DASSL 24/24 PASS, 기존 고하중 envelope 변화 0%, LC11만 신규 case.
- LC11 Fusion 패키지: 구현 source `e86e436861fd28f4055af1a1b9387bb764a7179b`에 Git object 기준 결박 완료. 실제 Fusion 실행과 결과 상관은 여전히 `PENDING_EXTERNAL_EXECUTION`이다.
- Mutation: 요구 17/17 재도입 결함이 실제 compile/run 또는 validator에서 거부됨.
- Hardware-adapter E2E: production class와 timestamp pulse/ADC/PWM 경계를 사용한 필수 37/37 scenario, powered phase E-stop 8종 PASS. 실제 hardware 시험은 아님.
- 명시 정책 gate: `python3 validation/run_v0621.py --fusion-policy deferred` 통과. package integrity는 PASS지만 출력은 `solver_pass=false`다.
- 최종 handoff lock: engineering source `a22f06ea534cad9e99949872e550d2789d49ef9f`, source tree `49fd972b95aa9647773aa4a347c9ca6531cc134b`, input set SHA-256 `d311156905635edb9bd7585c1540e1a81cfc3262a1359553260bffd03ec88efa`에 두 Fusion 패키지와 worker 계약을 결박했다.

## 이관된 외부 검증

1. P0-L: Windows/macOS Fusion mandatory study와 LC11, mesh convergence, cross-solver correlation은 post-v0.6.2.1 stage에서 수행한다.
2. 실제 결과가 없으므로 `CROSS_SOLVER_VALIDATED`나 `FUSION_VALIDATED`를 사용하지 않는다.

Windows worker `win`은 이번 Goal에서 6회 재시도했으며 마지막 `2026-08-31T08:22:28Z` 접속은 12초 SSH timeout이었다. 로컬 Tailscale backend는 정상이나 worker peer가 `Online=false`이고 최신 Tailscale ping 3회도 응답하지 않아 SSH 이전의 device/peer offline으로 범위를 좁혔다. 이전 연결 시 Fusion 2704.1.53 process와 interactive session 3까지 확인했지만 해석 실행/결과 수집은 하지 못했다. 상세 차단 증거는 `validation/fusion_external_blocker_v0.6.2.1.json`에 기록했다.

worker 복구 후의 실행 간극은 `fusion_worker/scripts/prepare_run.py`로 폐쇄했다. 현재 checkout이 최종 handoff source commit의 descendant인지, source tree와 source STEP Git object 및 package/worker hash가 일치하는지 검증하고 LC02/04/05/07/08/08+06/10/11용 `PENDING` manifest만 만든다. `validation/fusion_worker_handoff_v0621.py`는 8개 실행 조합과 잘못된 study/LC06 누락 거부를 검증한다. `DEFERRED`에서도 실제 결과 파일이 나타나면 fail-closed validator를 우회할 수 없으며, 이 준비 증거는 실제 Fusion solve를 대체하지 않는다.

실제 motor/flake/airflow/열/구조 시험은 수행하지 않았다. Donor 전압·전류·기어비·센서형식은 라벨/실측 전 확정하지 않는다.
