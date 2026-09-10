# P6 냉간 압출기 조립 검증

P6는 P5 process coupon 결과가 `validate_p5_stage_release.py`에서 `P5_STAGE_RELEASE_VALIDATED`로 재검증되고 production screw/barrel을 수령한 뒤, 히터를 장착하거나 통전하기 전에 수행한다. P5 release에는 qualified supplier/process-route ID와 screw/barrel heat-reservation reference가 포함되어야 하며, P6 production receipt는 이 식별자와 정확히 일치해야 한다. 목표는 실제 screw/barrel/thrust stack이 냉간에서 자유롭게 회전하고 열팽창용 축방향 여유를 확보하는지 확인하는 것이다.

## 조립·측정 순서

1. Screw flight OD와 barrel ID의 수령검사 원시값으로 실제 diametral clearance 범위를 계산한다. U95 포함 0.28–0.32 mm 안에 있어야 한다.
2. 51102를 지정 방향으로 조립하고 housing pocket diametral clearance 0.30–0.35 mm를 확인한다. Shaft washer는 integral Ø23 shoulder 쪽, housing washer는 지정 pocket 쪽이다.
3. 실제 bearing height를 사용해 steel shim을 선정하고 loaded-direction thrust endplay를 0.05–0.15 mm로 맞춘다. Printed shim은 사용하지 않는다.
4. GGM coupling을 분리한 상태에서 screw를 손으로 최소 20회 회전한다. Barrel/flight rub, bind, scraping contact는 0이어야 한다.
5. Coupling 기준 drive coaxiality를 dial indicator로 측정한다. U95 포함 0.05 mm 이하여야 한다.
6. Front sliding guide의 사용 가능한 cold axial travel은 1.50 mm 이상, rear retainer cold endplay는 0.12–0.28 mm여야 한다.

## 판정

`templates/p6_production_receipt.csv`에는 EX-SCR-01/EX-BAR-01의 serial, supplier/process-route ID, P5 heat-reservation reference, 실제 heat/lot, material/process/final-finish report ID와 evidence SHA-256을 기록한다. `templates/p6_cold_extruder.csv`의 모든 행에는 timezone 포함 시각, 계측기/교정 참조, 작업자·독립 검토자, repository 내부 evidence 경로와 SHA-256을 기록한다. `analyze_p6_records.py <cold.csv> --p5-release <p5_release.json> --production-receipt <receipt.csv>`는 P5 release를 현재 validator로 다시 검증한 뒤 production identity와 cold-fit U95를 판정한다. 결과를 저장한 뒤 `templates/p6_stage_release.json`에 exact P5 release, production receipt, cold record, P6 result의 SHA-256과 독립 검토 정보를 기록하고 `validate_p6_stage_release.py`로 재검증해야 P8 진입 검토에 사용할 수 있다. 이 release도 motor/heater authorization은 false이고 machine release는 HOLD다.
