# P1 실물 재고·수령검사 실행안

P1은 구매나 통전이 아니라 **현재 보유품을 식별하고 실제 치수를 기록하는 단계**다. `P0=PASS`는 유지되지만 이 문서 자체가 어떤 구매/가공/전원 인가도 승인하지 않는다.

## 1. 먼저 측정할 것

1. 2020/2040 profile은 절단하지 말고 각 bar의 사용 가능 길이를 `templates/profile_stock_measurement.csv`에 한 줄씩 기록한다. 150 mm 캘리퍼로 장척 길이를 이어 재지 말고 `MEAS-16` 장척 steel tape/rule처럼 stock 전체 길이를 직접 커버하는 계측기를 사용하며, usable length와 U95를 함께 기록한다. 2020은 현재 cut-list 순수 길이 합계 13,348 mm, 2040은 1,320 mm다. 총길이만 맞아도 890/660/430 mm 조각이 배치되지 않으면 부족하므로 `profile_nesting.py`로 실제 nesting을 확인한다.
2. 24 V PSU, BTS7960 x2, Arduino Mega, E-stop은 사용자 보유 회신과 실물 검사를 구분한다. 라벨/단자/손상 사진을 남기고 실제 식별 전에는 `INSPECTED`로 바꾸지 않는다.
3. 6201 x3, 61905/6905 x4, 51102 x1은 각인·내경·외경·폭·부식·자유회전을 기록한다. 대체 브랜드는 치수 일치만으로 정격 동등품으로 간주하지 않는다.
4. K0/K1, positive-opening NC switch, fuse holder, Hall current sensor, #35 chain/sprocket은 보유 여부와 **정확한 모델/정격**을 먼저 확인한다.
5. 도착한 `TH-INS-01` 열 차단 테이프는 포장/라벨, backing, adhesive, 폭/두께, 제조사 continuous service temperature rating을 기록한다. 이 단계에서는 hot-zone에 붙이지 않으며 안전 cutoff로 간주하지 않는다.

## 2. 기록 규칙

`templates/p1_inventory_record.csv`의 30개 item row를 삭제하거나 추가하지 않는다. Analyzer는 `inventory_confirmation.csv`의 exact item set, `planned_state`, required quantity/capacity와 전부 대조한다. PASS row는 instrument calibration ref, operator와 서로 다른 reviewer, timezone 포함 timestamp, evidence path/SHA-256을 모두 요구한다. Profile stock record도 같은 provenance를 유지하며 nesting에는 `usable_length_mm - u95_length_mm`만 사용한다. 미확인은 `NOT_FOUND` 또는 `IDENTITY_PENDING`, 보유하지만 미측정은 `SEEN_NOT_MEASURED`로 구분한다. 구매 후보라는 이유만으로 `PASS`를 입력하지 않는다.

`analyze_p1_records.py templates/p1_inventory_record.csv`는 증거 경로/SHA-256과 provenance를 fail-closed로 확인한다. GGM 축을 PASS로 기록하려면 `--ggm-packet`에 `analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json`을 복사해 채운 physical receipt packet을 함께 넘겨야 하며, 해당 축의 model/serial, raw evidence hash와 voltage/shaft/PCD/output-offset/case envelope를 current inspection authority로 재검증한다. 현장 launch ZIP에는 이를 `01_TEMPLATES/p1_ggm_receipt_packet.json`으로 포함한다. 프로젝트실 조사 대상이 모두 판정되고 GGM만 미수령이면 `P1_STOCK_SURVEY_PASS_GGM_PENDING`, 두 GGM receipt까지 검증되어야 `P1_RECORD_CHECK_PASS`가 된다. `NOT_FOUND`, `IDENTITY_PENDING`, `SEEN_NOT_MEASURED`는 P1 통과로 승격되지 않는다.

## 3. 다음 단계로 넘기는 정보

Profile nesting이 가능하면 P2 절단계획을 만들 수 있다. GGM 실측이 들어오면 `analyze_ggm_mount_compatibility.py`로 D02/D03의 PCD104, 출력축 편심 18 mm, Ø6.60 M6 clearance budget과 실측 U95를 먼저 대조한다. `AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED`일 때만 기존 mount 도면을 그대로 유지할 수 있으며, `HOLD_REDRAW_REQUIRED`이면 현장에서 장공 가공이나 강제 체결로 보정하지 않고 CAD/도면을 재검토한다. 어느 결과도 drilling 자체를 승인하지 않는다. P1에서 부족한 품목은 한 번에 구매목록으로 모으되 **주문은 별도 사용자 승인 전 실행하지 않는다.**
