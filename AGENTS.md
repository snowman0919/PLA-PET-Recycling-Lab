# PPR C1 작업 규칙
공용 분쇄 M1 한 개, 별도 압출 M2, 24V800W PSU와500W 운전 cap을 유지한다.
source of truth는 src/design.py, src/supports.py 및 src/geometry.py이며 파생 JSON/CAD/BOM을 재생성한다.
실측·제조사 확인·가정·수치 해석을 구분하고 검사 범위를 축소해 전체PASS로 표시하지 않는다.
본체700x420x520mm 상한 및 보유 프로파일 제약을 변경하기 전 사용자와 합의한다.
새 구조는 main, 이전 설계는 잠긴 archive 브랜치에 보존한다. 원본 dirty worktree에 reset/clean/stash를 하지 않는다.
사용자 승인 없이 주문/가공/통전하지 않는다. 고하중 지지·가드·독립 thermal cutoff/interlock은 누락하지 않는다.
한국어로 결과와 HOLD 항목을 보고한다. 코드/스크립트는 MIT, 하드웨어는 LICENSE-HARDWARE를 따른다.
