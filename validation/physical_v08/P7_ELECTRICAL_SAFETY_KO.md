# P7 전기 안전·logic 검증

P7은 motor/heater branch를 물리적으로 분리한 상태에서 배선, PE, 절연, hardwired permission chain과 reset safe-state를 확인하는 단계다. 통전 구간은 logic branch만이며 별도 사용자 승인이 필요하다. `fuse_ids_match_schedule`과 `point_to_point_wiring_match`는 임의 체크박스가 아니라 현재 `exports/final/electrical/fuse_schedule.csv`, `pin_schedule.csv`, `wire_schedule.csv`에 대한 현장 대조 결과여야 한다.

## P7-A: 무통전 검사

1. Main disconnect OFF와 0 V를 확인하고 motor/heater branch fuse를 제거한다.
2. Accessible metal의 PE bond를 측정한다. U95 포함 0.10 Ω 이하여야 한다.
3. Mega, sensor module, motor driver, MOSFET 등 전자장치를 절연시험 경로에서 분리한 뒤 500 VDC 절연시험을 수행한다. 최소 1 MΩ이어야 한다. 연결된 전자장치에 megger를 인가하지 않는다.
4. Fuse ID, polarity, terminal label과 point-to-point wiring을 released schedule과 대조한다.

## P7-B: current-limited logic-only

1. 24 V supply current limit를 0.5 A로 두고 logic branch만 연결한다. Rail은 22.8–25.2 V, 초기 logic current는 0.5 A 이하여야 한다.
2. Reset 직후 hazardous enable 출력은 0개여야 한다.
3. E-stop, lid, service guard, thermal chain을 한 번에 하나씩 forced-open한다. 각 경우 K0가 실제 dropout되고 motor/heater permission이 제거되어야 한다.
4. 전원 복귀 또는 contact 재폐쇄만으로 motor/heater command가 자동 생성되면 FAIL이다.

`templates/p7_electrical_safety.csv`의 모든 행에 작업자·독립 검토자·timezone 포함 시각, repository 내부 raw evidence 경로와 SHA-256을 기록한다. Numeric 행은 계측기 ID와 교정 참조도 필수다. `analyze_p7_records.py`는 raw evidence hash를 재검증하고 현재 fuse/pin/wire/I/O schedule의 SHA-256을 결과에 결박한다. 결과를 저장한 뒤 별도 사람이 `templates/p7_stage_release.json`의 exact record/result SHA-256을 검토하고, `validate_p7_stage_release.py`가 현재 analyzer로 다시 계산해 `P7_STAGE_RELEASE_VALIDATED`를 내야 P8/P9 진입 검토에 사용할 수 있다. 이 release도 motor/heater authorization은 false이고 machine release는 HOLD다.
