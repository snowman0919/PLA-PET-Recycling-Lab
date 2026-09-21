# C2.1 후속 통합 실행 순서

상태 기준일: 2026-09-21. 활성 요구조건은 `c2/design/requirements.json`, 전달계 반복 입력은 `c2.1/design/requirements.json`이다.

1. P0 증거 verifier: 완료. 실행/원자료/입력 deck/형상 hash와 견적 근거를 계산하며 0건 상수를 사용하지 않는다.
2. P1 pin/window 하중 전달: rigid first-contact 위상·평형 완료. 탄성 분담, 접촉응력, 마찰, 수명은 HOLD.
3. P2 절삭·냉각 통합: C2 생성 부품 9종을 C2.1 assembly에 통합 완료. screen attachment, sensor wiring/응답, measured UA는 HOLD.
4. P3 조달·원가: 국내/해외 M1 후보 검색 진행. 전체 landed cost와 driver/reduction가 닫히지 않아 모터 선정·예산 적합은 HOLD.
5. P4 solver: CalculiX coupon 9건 실행 완료. DEM·절삭/파단·실물 보정·성능학습은 미실행.
6. P5/P6: 전체 열관리·제어·전체 기계 제작 검토 패키지는 이후 비의존 작업으로 계속한다.

구매·외주·통전·가공·main 병합은 사용자 별도 승인 전 수행하지 않는다.
