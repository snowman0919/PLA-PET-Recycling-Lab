# HS-R1-S2 작업과 커밋

루트 AGENTS.md를 따른다. 이 폴더는 무가압 시험치구이며 본체의 제작·고온 운전 승인 범위를 바꾸지 않는다.

의미가 독립적인 변경마다 검증 후 커밋한다. 형상·하중 계약, 실측 기록 검사, 패키징을 불필요하게 한 대형 커밋으로 묶지 않는다. `git add .`나 전체 작업트리 커밋 대신 검토한 경로만 stage하며 다른 writer의 index와 미커밋 변경을 보존한다.

커밋 전 관련 코드·생성기·시험을 실행하고 실제 결과를 기록한다. 이 폴더의 graphify AST와 검토된 문서 관계는 `update_scoped_graph.py`로 갱신한다. 전체 프로젝트 그래프 재추출로 주장하지 않는다. 스크립트는 graphify가 설치된 기존 Python에서 실행한다.

실측 기록은 무시 경로 measurements/에 보관한다. 합성 시험을 MEASURED 증거로 게시하지 않는다. 기본 physical_test_template.json은 performed=false와 빈 samples를 유지한다. package_review.py는 기준 package를 덮어쓰지 않는 r1 검토 묶음을 만든다.

기계 설치, 구매·가공·가열, branch merge, GitHub Release 게시 권한을 일반적인 코드 수정·커밋 승인에서 추론하지 않는다. 원격 push와 로컬 commit은 별도로 보고한다.

현재 HS-R1-S2는 연구용 보존 후보이며 MVP 기본 제작안이 아니다. 사용자 재선택 없이 12장 spring의 추가 고온 재료/인증 작업을 기본 일정으로 확장하지 않는다. 후보의 HOLD를 없애지 말고 본체 마감의 필수 요구와 구분한다. 현재 본체 방향은 docs/final/practical_mvp_priority_ko.md를 따른다.
