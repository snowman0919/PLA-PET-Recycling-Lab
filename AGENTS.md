# Filament Recycler Agent Rules

이 저장소의 모든 작업은 아래 규칙을 따른다. 루트의 지시는 하위 디렉터리 전체에 적용된다.

## 소유권과 언어

- parent Codex가 최종 요구사항, 아키텍처, 안전 결정, 외부 저장소, merge, release acceptance를 소유한다.
- 사용자 보고와 프로젝트 핵심 문서는 한국어로 작성한다. 코드 식별자와 표준 용어는 영어를 병기할 수 있다.
- 계획만 작성하고 멈추지 않는다. 각 단계에서 실제 파일, 계산, 실행 결과와 변경 이력을 남긴다.
- 시뮬레이션 결과와 실제 물리 시험 결과를 명확히 구분한다.

## 로컬 subagent

- 비밀값은 루트 `.env`의 `KOTORI_SUBAGENT_API_KEY`에서만 읽으며 출력, URL, 로그, 예외, 저장소, 커밋에 남기지 않는다.
- `.env`의 `SUB_ENDPOINT`는 현재 스킴 없이 `/v1`을 포함한다. 호출 시 메모리 안에서만 `https://`를 앞에 붙이고 중복 `/v1`을 만들지 않는다.
- 첫 사용 전 `/v1/models`, `/v1/responses` 의미 시험, harmless tool-call probe를 수행한다.
- 확인된 모델 중 기본은 `dgx-moa-fast`, 높은 정확도·성능이 필요한 독립 계산 검토만 `dgx-moa`를 사용한다.
- subagent에는 파일 경계와 합격 기준이 분명한 작업만 맡긴다. 같은 파일에 여러 writer를 동시에 배정하지 않는다.
- subagent는 원격 저장소 생성, push, 구매, 가공 승인, 최종 안전 판정, merge를 수행하지 않는다.
- parent는 결과를 그대로 채택하지 않고 수식, 출처, diff, 실행 결과를 재검증한다.
- API timeout이나 불완전 응답은 결과로 채택하지 않는다. 진행을 막지 말고 parent가 직접 수행하며 실패를 기록한다.

## 안전과 구매

- E-stop, lid/service interlock, thermal fuse와 branch fuse는 소프트웨어 하나에 의존하지 않는다.
- cutter, screw, heater, mains/high-current 작업은 물리적 lockout과 사용자 확인 없이 검증 완료로 표시하지 않는다.
- 사용자 승인 없이 부품 주문, CNC 주문 또는 비용 지출을 진행하지 않는다.
- donor 부품 전압, 전류, 토크, 축경, 센서 형식을 추측하지 않는다. 사진, 라벨, 실측으로 확정한다.

## 설계와 검증

- 핵심 CAD의 source of truth는 FreeCAD Python과 파라미터 파일이다.
- 고하중 경로는 `metal part -> bearing/plate -> aluminum profile -> table`로 구성하고 출력물만으로 지지하지 않는다.
- 3D 출력 부품 기본 bounding box는 각 축 210 mm 이하로 제한한다.
- 실제 시험 전 계산값에는 가정, 경계조건, 안전계수와 검증 필요 상태를 붙인다.
- cutter/blade clearance는 출력 공차가 아니라 금속 shim으로 조절한다.
- 의미 있는 테스트만 작성하며 보호 요구사항, 의사결정 가치, 입력, 방법, 증거, 합격기준, 결과를 기록한다.

## Git과 산출물

- source of truth와 사람이 검토할 수 있는 경량 산출물은 추적한다. 재생성 가능한 큰 출력은 manifest와 생성 명령을 우선한다.
- 커밋 전 관련 생성 스크립트와 검증을 실행한다.
- `.env`, API 키, 인증 토큰, 다운로드 캐시, 주문용 임시 파일은 커밋하지 않는다.
- software/firmware/scripts는 MIT, hardware CAD/drawing/electronics는 CERN-OHL-P-2.0을 적용한다. 자세한 범위는 `docs/licensing.md`를 따른다.
