# 원격 재연결 후 실제 실행 / 2026-09-14

재개 시 기준은 a0a2a4b9fd0d6e65b5e93161c40834c80c7312d1이다. 이전 401 상태는 이번 명령에서 재현되지 않았다. 이전 세션의 완료 주장을 그대로 승계하지 않고 로컬 실행 결과를 확인했다.

## 이번 수정

Modelica provenance 입력은 CAD 이동량 결박 후 15개지만 package import 시험이 구형 13개를 요구했다. 단순 개수 비교를 정확한 파일 집합과 중복 금지로 교체한다.

패키지에는 CADParameters 생성기, 신규 Z1 모델/설정/기준 형상/결과, 일반 축 치수 도면 생성기, 통합 간섭/운동/고정 검사 모듈을 추가한다. 격리된 패키지 소스 사본에서 thermal model과 reference/width_only/support_only/combined 네 경우를 import해 확인한다. 기존 R1 프레임 경로 추가도 함께 보존한다.

이 수정은 모든 해석 원시 파일의 배포 완료를 의미하지 않는다. 별도 조사에서 기존 evidence가 참조하지만 package layout에는 없는 의존 파일 15개가 발견됐다. 전체 제작 ZIP 승격 전 이 의존 파일과 추적 상태를 정리해야 한다.

## 실제 실행 결과

- Z1 네 가지 경우, 열전달 가정 32조건: DIGITAL_DELTA_SCREEN_COMPLETE.
- OpenModelica 신규 실행과 후처리: 네 권취 경우, jam latch, 네 negative control 검증 통과.
- 고온 fit 산술 검토: HOT_ZONE_DIGITAL_PASS. 실물/소재 인증이 아니다.
- CalculiX 신규 실행: V08_CALCULIX_VALIDATION_OK; LC04 0.001179 mm, 선택 mount SF 2.089.
- 수정 후 로컬 CI-LIGHT: 60개 명령 / 56개 시험 모듈 통과. GitHub Actions 실행 결과로 표현하지 않는다.

실행 로그와 상세 결과는 .build/retry-closure-20260914/ 아래에 정리한다. 이번 수치 결과를 전체 기계의 모든 구조/열/동역학 qualification이나 물리시험으로 확대하지 않는다.

## 가열계 해석의 중요 제한

수정안의 불리한 가정에서 히터 lump 최고온도는 346.54 C이며, 300 C 비교값을 초과한다. 300 C는 공급자 승인 정격이 아니다. 수치 수렴/에너지 수지 통과와 가열계 적합 판정은 분리한다. 일부 조건의 목표온도 미도달, 약 -50 N의 후방 beam 반력도 공개한다.

기존 rc1 태그/자산은 변경하지 않는다. physical_validation_state=NOT_RUN, fabrication_authorized=false, energization_authorized=false를 유지한다. 수정 소스와 구형 제조 도면을 섞어 사용하지 않는다.
