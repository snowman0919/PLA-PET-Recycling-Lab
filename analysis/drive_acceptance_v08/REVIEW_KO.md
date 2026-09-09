# GGM 구동부 계속 작업의 독립 검토

현재 `cad/freecad/drive_v08`, `firmware/ggm_drive_v08`의 기존 생성 작업을 보존하면서 별도 검토를 수행한다. 본 폴더만 독립 작성한다.

## 확인된 결과
- 구동부 STEP manifest: 새 간섭 0, 전체 bounding box 470 x 729 x 930 mm. 기존 고온부 등의 상속 finding은 별도이며 전체 기계 PASS가 아니다.
- 실제 `ggm_drive_guard.h`와 `test_guard.cpp`를 g++ -Wall -Wextra -Werror로 재컴파일해 85개 software check 통과.
- 모터/기어박스의 실제 시험은 미수행이다.

## 마감 때 혼동하면 안 되는 경계
1. `control/ggm_drive_contract.json`의 소프트웨어 토크 차단값은 기어박스축 8.0 Nm다. 기존 `analysis/motor_sizing_v08/results.json`의 PET 권장 사례는 purge 최대 8.046 Nm, high-viscosity 최대 9.476 Nm다. 기어박스 정격 9.80665 Nm를 만족해도 8 Nm 운전차단을 만족하는 것은 아니다. 정상 운전과 purge, 점도 민감도에서 감속/공급 감소 또는 정지가 필요함을 명시해야 한다. 토크 차단을 몰래 올리지 않는다.
2. `build_variant.py`의 GgmInput.feedback_ms는 tach sampler 호출 시각이다. 새 펄스 수신 시각을 뜻하지 않는다. `feedback_valid`에는 current calibration만 전달된다. 상위 supervisor의 tach-valid/jam 처리를 함께 검토하고 guard 단독의 100 ms 검사를 tach 단선 검증으로 부르지 않는다.
3. 후기 패키지는 canonical hot-zone 제작 승인을 대체하지 않는다. 선언된 파일/원본 해시가 최신인지 확인하고, `.FCBak`/빌드 캐시/원시 로그 전체를 무분별하게 포장하지 않는다.

필수 보완을 독립 검사와 자료로 연결하되, 현재 생성 중인 원본 파일을 동시에 수정하지 않는다.
