# P1 실물 재고·수령검사 실행안

P1은 구매나 통전이 아니라 **현재 보유품을 식별하고 실제 치수를 기록하는 단계**다. `P0=PASS`는 유지되지만 이 문서 자체가 어떤 구매/가공/전원 인가도 승인하지 않는다.

## 1. 먼저 측정할 것

1. 2020/2040 profile은 절단하지 말고 각 bar의 사용 가능 길이를 `templates/profile_stock_measurement.csv`에 한 줄씩 기록한다. 2020은 현재 cut-list 순수 길이 합계 13,348 mm, 2040은 1,320 mm다. 총길이만 맞아도 890/660/430 mm 조각이 배치되지 않으면 부족하므로 `profile_nesting.py`로 실제 nesting을 확인한다.
2. 24 V PSU, BTS7960 x2, Arduino Mega, E-stop은 사용자 보유 회신과 실물 검사를 구분한다. 라벨/단자/손상 사진을 남기고 실제 식별 전에는 `INSPECTED`로 바꾸지 않는다.
3. 6201 x3, 61905/6905 x4, 51102 x1은 각인·내경·외경·폭·부식·자유회전을 기록한다. 대체 브랜드는 치수 일치만으로 정격 동등품으로 간주하지 않는다.
4. K0/K1, positive-opening NC switch, fuse holder, Hall current sensor, #35 chain/sprocket은 보유 여부와 **정확한 모델/정격**을 먼저 확인한다.

## 2. 기록 규칙

`templates/p1_inventory_record.csv`의 `observed_*` 칸만 실측으로 채우고 증거 파일은 저장소 상대경로와 SHA-256으로 결박한다. 미확인은 `NOT_FOUND` 또는 `IDENTITY_PENDING`, 보유하지만 미측정은 `SEEN_NOT_MEASURED`로 구분한다. 구매 후보라는 이유만으로 `PASS`를 입력하지 않는다.

`analyze_p1_records.py templates/p1_inventory_record.csv`는 증거 경로/SHA-256과 provenance를 fail-closed로 확인한다. 프로젝트실 조사 대상이 모두 판정되고 GGM만 미수령이면 `P1_STOCK_SURVEY_PASS_GGM_PENDING`, 두 GGM 수령검사까지 PASS면 `P1_RECORD_CHECK_PASS`가 된다. `NOT_FOUND`, `IDENTITY_PENDING`, `SEEN_NOT_MEASURED`는 P1 통과로 승격되지 않는다.

## 3. 다음 단계로 넘기는 정보

Profile nesting이 가능하면 P2 절단계획을 만들 수 있다. GGM 실측이 들어오면 최종 mount drilling과 P3 bench를 확정한다. P1에서 부족한 품목은 한 번에 구매목록으로 모으되 **주문은 별도 사용자 승인 전 실행하지 않는다.**
