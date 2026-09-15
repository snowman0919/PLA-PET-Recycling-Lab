# P8 설치 후 motor dry-run

P8은 P3에서 교정한 GGM 구동계를 실제 machine load path에 장착한 뒤 재료·히터 없이 저속으로 구동해 방향, tach, stop, bearing/coupling 상태를 확인한다. 진입 검토에는 재검증 가능한 P3/P6/P7 stage release와 P3 calibration이 적용된 firmware/EEPROM의 readback 증거가 필요하며, 실제 motor 통전은 그와 별개의 명시적 승인이다.

## 순서

1. Fan → puller/spooler/traverse → feeder → screw → guarded shredder 순으로 한 branch씩만 구동한다. 동시에 여러 hazardous branch를 처음부터 올리지 않는다.
2. Shredder는 실제 cutter-shaft rpm을 기록하고 selected 40 rpm gearbox + 2.5:1 chain의 약 16 rpm 기대값과 비교한다. 편차가 있으면 sprocket ratio/tach PPR부터 확인하고 임의 보정하지 않는다.
3. Screw commissioning은 10 rpm 이하에서 시작하며 어떤 시험에서도 20 rpm hard limit를 넘기지 않는다. Reverse는 금지한다.
4. 각 branch에서 current, rpm, bearing/coupling temperature trend, vibration/abnormal noise를 기록한다.
5. Normal stop, E-stop, tach-loss를 각각 강제한다. 모든 경우 hazardous command가 제거되고 전원/신호 복구만으로 자동 재시작하지 않아야 한다.

`templates/p8_motor_dry_run.csv`의 모든 행은 timezone 포함 시각, 작업자·독립 검토자, repository 내부 raw evidence SHA-256을 가져야 하며 numeric 행은 계측기/교정 참조도 필요하다. `analyze_p8_records.py <record.csv> --p3-release ... --p6-release ... --p7-release ... --profile-dir ... --tach-calibration ... --firmware-installation ...`은 모든 선행 release와 firmware commissioning을 다시 검증한 뒤 P8 기록을 판정한다. Shredder의 16 rpm은 비교 기준이며 새로운 임의 허용 band를 만들지 않는다.

## P8 firmware commissioning evidence

P3의 review-only profile을 사람이 검토해 실제 `firmware/ggm_drive_v08/ggm_commissioning.h`에 적용하고 새 final HEX를 생성한 뒤에도, 파일이 존재한다는 사실만으로 P8 진입 조건이 되지 않는다. SH/EX tach는 logic-only/lockout 상태에서 각각 최소 10회 수동 회전해 실제 pulse 수를 세고 `templates/p8_tach_calibration.csv`에 기록한다. 특정 PPR 값을 문서에서 가정하지 않고 `observed_pulses / manual_revolutions`가 양의 정수로 귀결되는지 확인한다.

Flash 후에는 MCU의 읽기 전용 `GGM_REPORT` 한 줄과 실제 flash readback HEX를 원시 evidence로 저장한다. `templates/p8_firmware_installation.csv`는 이 두 파일의 repository 경로와 SHA-256, 작업자·독립 검토자·timezone 포함 시각을 가리킨다. `validate_p8_firmware_commissioning.py`는 P3 release, candidate profile, 적용된 commissioning header, variant/final build manifest, final HEX, flash readback, `GGM_REPORT`, tach calibration을 모두 교차검증한다. `FIRMWARE_COMMISSIONING_RECORD_CHECK_PASS`여도 motor/heater authorization은 false이고 machine release는 HOLD다.

## P8 완료 release

P8 analyzer 결과가 통과한 뒤에는 `templates/p8_stage_release.json`에 exact P3/P6/P7 release, firmware profile manifest, tach calibration, firmware-installation record, P8 raw record/result의 SHA-256과 독립 검토 정보를 기록한다. `validate_p8_stage_release.py`가 현재 P8 analyzer로 전체 chain을 재계산해 `P8_STAGE_RELEASE_VALIDATED`를 낸 경우에만 P9 진입 검토에 사용할 수 있다. 이 artifact도 heater energization을 승인하지 않는다.
