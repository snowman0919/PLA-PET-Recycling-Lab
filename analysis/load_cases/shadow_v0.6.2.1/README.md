# v0.6.2.1 OpenModelica shadow 하중 보고서

- 상태: `PASS`
- 해석: OpenModelica 1.27.0 / DASSL, reduced-order virtual shadow
- 범위: production tach/drive 계약과 process surrogate 경계값을 입력으로 사용
- 물리 시험: 수행하지 않음

기존 frozen 하중 4개는 모두 수치 변화가 없어 LC01–LC10에 이 변경만으로 인한 재실행은 필요하지 않다. 다만 기존 Fusion 결과 자체가 `PENDING_EXTERNAL_EXECUTION`이므로 결과 재사용 가능 판정은 아니다.

새 feeder attachment 반력은 2.2 N·m, 수직하중은 5.4 N이며 기존 case에 포함되지 않는다. 따라서 `LC11_FEEDER_ATTACHMENT = NEW_CASE_REQUIRED`이다.

가정/한계: 이 결과는 제어 및 feed inventory의 축약 시뮬레이션이다. donor motor 실측 보정, 실제 입자 접촉, 구조 시험, 파편 containment 시험을 대체하지 않는다.
