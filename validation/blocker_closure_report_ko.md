# v0.6.2.1 기술 blocker closure 보고서

## 판정

`TECHNICAL_PREFLIGHT_PASS_RELEASE_UNMET`이다. P0-A~K는 가상/설계 범위에서 통과했다. P0-L 실제 Fusion 증거가 없어 Goal과 release는 완료하지 않는다.

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
- CI 성격의 로컬 gate: `python3 validation/run_v0621.py --allow-fusion-pending` 통과. 이는 exact-head CI나 Fusion 완료를 의미하지 않는다.

## 미해결 technical blocker

1. P0-L: Windows Fusion mandatory study와 LC11, mesh convergence, cross-solver correlation이 없다.
2. 이 항목 때문에 CI-LIGHT/CI-FULL exact final HEAD, PR, merge를 수행하지 않았다.

Windows worker `win`은 이번 Goal에서 5회 재시도했으며 마지막 `2026-08-31T08:05:08Z` 접속은 12초 SSH timeout이었다. 로컬 Tailscale backend는 정상이나 worker peer가 `Online=false`이고 Tailscale/ICMP ping도 응답하지 않아 SSH 이전의 device/peer offline으로 범위를 좁혔다. 이전 연결 시 Fusion 2704.1.53 process와 interactive session 3까지 확인했지만 해석 실행/결과 수집은 하지 못했다. 상세 차단 증거는 `validation/fusion_external_blocker_v0.6.2.1.json`에 기록했다.

worker 복구 후의 실행 간극은 `fusion_worker/scripts/prepare_run.py`로 폐쇄했다. 현재 checkout이 결박 metadata를 포함하면서 engineering source commit을 ancestor로 갖는지, source STEP Git object 및 package manifest hash가 일치하는지 검증하고 LC02/04/05/07/08/08+06/10/11용 `PENDING` manifest만 만든다. `validation/fusion_worker_handoff_v0621.py`는 8개 실행 조합과 잘못된 study/LC06 누락 거부를 검증한다. 이는 실제 Fusion solve를 대체하지 않는다.

실제 motor/flake/airflow/열/구조 시험은 수행하지 않았다. Donor 전압·전류·기어비·센서형식은 라벨/실측 전 확정하지 않는다.
