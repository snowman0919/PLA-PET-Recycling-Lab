# 히터 입력과 전역 오류 래치 재검토

기준 commit: dada3ffe873f4a7faba555e63016fcd581c7d4aa.

## 재현과 수정

실제 HeaterController를 host 공유 라이브러리로 컴파일한 뒤 첫 온도에 NaN을 전달했다. 수정 전 반환은 duty=[NaN,1,1,1], faults=0이었다. 별도 C++ 회귀시험도 첫 잘못된 온도 입력에서 assert 실패했다. 이는 실물 입력 측정이 아니라 production source의 host 실행이다.

온도 및 목표온도의 유한성, 목표온도 범위, allocator 입력 유한성을 검사한다. 잘못된 목표/할당 입력은 HEATER_COMMAND_RANGE로 래치한다. 기존 285 C 과온 차단과 물리 thermal chain을 변경하지 않는다. 이미 다른 채널에서 오류가 래치되면 applyAllocation도 이전 요청값으로 재통전 출력을 반환하지 않는다.

`validation/test_heater_numeric_safety.py`가 실제 C++ 구현을 독립 컴파일하고 10개 사례를 검사한다. NaN/+Inf/-Inf 각각의 온도, 목표, 할당 입력과 다른 채널의 오류 이후 할당을 포함한다. 기존 heater PI 시험과 전체 firmware Makefile 시험도 별도로 실행한다.

## 범위

수치 입력 거부와 전역 래치 경로만 보완한다. PWM 실제 파형, MOSFET 단락, 전원 접점, 센서 단선, 열응답, 실제 PID 안정성 및 안전인증을 증명하지 않는다.

controller_bridge.cpp/py는 같은 HeaterController의 host 호출용 도구다. 기존 유한체적 열모델에 연결하는 편집 요청은 도구에서 차단되어 실행하지 않았다. 열모델과 연결한 새 해석 결과는 없다.

후방 지지의 integral radial crown 소스 작성 요청도 도구에서 차단되어 파일이 생성되지 않았다. 기존 지지 형상은 바꾸지 않았다. 이는 사용자 실측으로 넘길 문제가 아니라 미완료 디지털 작업이다.

## 남은 디지털 작업

- 실제 제어기와 열모델 연결 및 고온/목표 미도달 조건의 재설계 검토.
- 후방 음의 반력을 실제 금속 접촉으로 지지하는 구조와 응력/간극 검증.
- 뚜껑 레일/래치/인터록 및 센서 장착 상세.
- 위 변경의 통합 CAD/도면/BOM/전체 해석/새 배포 재생성.

위 항목을 완료하지 않은 채 PHYSICAL_ONLY_REMAINDER나 전체 디지털 closure로 승격하지 않는다. 기존 physical_validation_state=NOT_RUN 및 제작/통전 HOLD를 유지한다.
