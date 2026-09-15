# PR 정상화 확인과 고온부 방사방향 지지 검토

기준 commit: `8d95c18e74d157cca02f73abc656e3aac7679d2f`.
이 문서는 검토 후보에 관한 기록이다. 기존 정식 CAD, 절단표, 구매 목록과 공개 rc1을 변경하거나 제작을 승인하지 않는다.

## PR 실패 알림의 실제 원인

최근 실패 `34858627442`는 24208c7f의 `current firmware evidence mismatch`였다. 원본 히터 코드와 두 배포 경로 중 GGM 사본/manifest가 함께 커밋되지 않은 것이 원인이었다. 649d0194 이후 이 누락이 수정됐고, a2747cdf부터 outgoing commit을 격리 검사하는 pre-push가 추가됐다.

재개 시 `.git/hooks/pre-push`가 실제로 설치돼 있음을 확인했다. core.hooksPath가 비어 있다는 이유로 hook이 없다고 판단하지 않는다. 검사는 dirty 작업 폴더가 아니라 전송할 commit의 git archive를 대상으로 한다. 실패한 commit은 로컬에서 차단하며, 알림 설정/메일/검사 기준은 변경하지 않는다.

기준 commit의 PR CI-LIGHT34911507219와 별도 CI-FULL34911527383이 모두 completed/success임을 확인했다. 이후 새 commit의 결과는 GitHub의 해당 SHA 검사로 별도 확인한다. 과거 실패 알림이 삭제됐다는 의미는 아니다.

## 기존 배치에서 추가로 확인한 문제

균일 배럴 자중15.03097 N와 끝단25 N의 기존 비교 하중을 사용하면, 16/110 mm 지지점의 반력은 뒤 -50.00988 N, 앞90.04085 N이다. 뒤 C형 판은 폭 약12.21 mm의 입구와 원호를 가지므로, 위쪽이 열렸다고 축이 그대로 빠지는 것은 아니다.

다만 명목 bore만 고려한 자유 안착 한계는 뒤쪽 위로0.13386 mm, 앞쪽 아래로0.30000 mm다. 이를 두 지점 사이 강체 직선으로 연장하면 끝단 축 편차가 약1.08 mm가 된다. 이는 실제 장비가 그렇게 움직인다는 예측이 아니라, screw/feed/thrust 제약을 무시하고 이상적인 beam 지지만으로 정렬 PASS를 선언할 수 없다는 진단이다. 실제로는 다른 접촉에서 힘이 재분배된다.

## 간섭 없이 재배치한 후보

앞 guide를 기존 x261에서 x125로 이동한 후보를 따로 만들었다. 배럴 뒤끝 기준 지지 중심은 16/246 mm가 된다. 2020 L430 rail은 길이/단면을 유지한 채 이동하며 추가 프로파일은 없다. 위쪽 crown을 연속 금속으로 만들고 T3 센서와 고정부에는 측면 창을 둔다. guide bore는 후보34.25 mm다.

후보의 전체266개 객체 검사에서 새로운 미분류 간섭은0건이다. 기존15개 참조 형상 겹침만 유지한다. T3 probe6 mm, retainer3 mm, Z3 band7 mm, rail/cooling duct4.5 mm의 명목 여유를 확인했다. 양끝 rail 접촉은 각각400 mm2, guide/rail 접촉은1131.58 mm2다. 단순히 겹치지 않는 떠 있는 부재를 통과시키지 않는다.

같은 비교 하중에서 후보 반력은 뒤3.23166 N, 앞36.79930 N으로 양쪽 모두 압축 방향이다. 다른 하중 전체나 실제 접합부 용량까지 검증한 것은 아니다. 끝단 하중을 크게 하면 다시 인장 반력이 생길 수 있으며 부정시험에서 이를 확인한다.

검토용 STEP: `exports/review/radial_support_v08/RS-FRONT-GUIDE-CANDIDATE.step`. 제조도면/BOM/통합 Release의 대체물이 아니다. guide는 축방향 조립이 필요하며 밴드를 먼저 안쪽 구간에 배치한 뒤 guide를 넣고 die와 T3를 나중에 설치하는 순서를 검토해야 한다.

## 열간 정렬과 열손실은 별도 판정

양쪽을 같은 bore로 맞춰도 무조정 냉간 안착은0.125 mm 아래이므로 곧바로 정렬 PASS가 아니다. 별도의 냉간 축 위치 -0.065 +/-0.010 mm 설정을 가정하면, 판 발바닥부터 bore까지의 팽창과 배럴 반경 팽창을 모두 반영한 지지축 범위는 -0.075..+0.07978 mm다. 배럴 전장을 연장한 수직 축 편차 경계는0.10266 mm다.

이 가정에서 기존 참고 열간 반경 틈새0.13715 mm와의 차이는0.03449 mm뿐이다. screw runout, 배럴 ID/OD 편심, 판/rail 변형 및 feeder/thrust 정렬 오차를 아직 빼지 않았다. 그러므로 이 숫자를 최종 정렬 여유나 실제 합격값으로 사용하지 않는다. 냉간 설정을 실제로 구현할 상세와 전체 공차 예산을 먼저 완성해야 한다.

지지 위치만 변경하면 방열 부하도 Z3/die 쪽으로 이동한다. 현재와 후보 각각8개 조건의 정상 열수지 역산을 실행했으나 후보도 모든 조건에서 기존100/100/100/60 W 정격으로 목표온도를 유지하지 못한다. 지지 이동은 기존 열전력 부족의 해결이 아니다. 열손실·히터 정격·제어의 통합 설계 작업이 남아 있다.

## 검증과 남은 작업

- `validation/test_radial_support_mechanics.py`: 정역학, C형 포획 원호, 축선 연장, 발바닥 기준 열팽창 및 Hertz helper 단위시험13개.
- `validation/test_radial_support_candidate.py`: 정상 후보, guide 누락, 떠 있는 rail, 센서 창을 막은 형상4개 사례. 정식 CAD 파일의 불변도 검사한다.
- `analysis/radial_support_v08/run_review.py`: 실제 계산과 가정/수치 검증을 `results/review.json`에 기록한다.
- `analysis/radial_support_v08/cad_candidate.py`: 현재 원본에서 후보 형상을 만들고 전체 정적 검사 및 STEP 양방향 차집합 검사를 수행한다.

초기 시도에서 미완성이었던 지지판 FEA는 후속 PLATE_FEA_KO.md의 범위로 구현·실행했다. 초기 실패 이력은 다음과 같이 보존한다. 초기 시도에서는 파일 작성이 차단됐다. 불완전 초안은 `.build/digital-closeout-20260915/deferred/`에 별도 보존하고 정식 소스/증거로 채택하지 않는다. 지지 접촉응력과 체결부, 전체 열간 축 정렬, 운전하중 전체, 열전력 재설계, 뚜껑/인터록/센서 상세는 미완료 디지털 작업이다. 사용자 실물 blocker로 바꾸지 않는다.

참고 원리: Tsai/Huang, Journal of Mechanics41(2025), DOI10.1093/jom/ufaf013의 선접촉 반폭과 유효 탄성률. 내부 원통 접촉에는 오목 면의 음의 곡률을 적용한다. sharp C-lip이나 실제 마찰/가공면의 접촉응력을 이 helper로 승인하지 않는다.

`physical_validation_state=NOT_RUN`, `fabrication_authorized=false`, `energization_authorized=false`, `canonical_geometry_promoted=false`.
