# P6 냉간 압출기 조립 검증

P6는 P5 process coupon이 승인되고 production screw/barrel을 수령한 뒤, 히터를 장착하거나 통전하기 전에 수행한다. 목표는 실제 screw/barrel/thrust stack이 냉간에서 자유롭게 회전하고 열팽창용 축방향 여유를 확보하는지 확인하는 것이다.

## 조립·측정 순서

1. Screw flight OD와 barrel ID의 수령검사 원시값으로 실제 diametral clearance 범위를 계산한다. U95 포함 0.28–0.32 mm 안에 있어야 한다.
2. 51102를 지정 방향으로 조립하고 housing pocket diametral clearance 0.30–0.35 mm를 확인한다. Shaft washer는 integral Ø23 shoulder 쪽, housing washer는 지정 pocket 쪽이다.
3. 실제 bearing height를 사용해 steel shim을 선정하고 loaded-direction thrust endplay를 0.05–0.15 mm로 맞춘다. Printed shim은 사용하지 않는다.
4. GGM coupling을 분리한 상태에서 screw를 손으로 최소 20회 회전한다. Barrel/flight rub, bind, scraping contact는 0이어야 한다.
5. Coupling 기준 drive coaxiality를 dial indicator로 측정한다. U95 포함 0.05 mm 이하여야 한다.
6. Front sliding guide의 사용 가능한 cold axial travel은 1.50 mm 이상, rear retainer cold endplay는 0.12–0.28 mm여야 한다.

## 판정

`templates/p6_cold_extruder.csv`에 실제 값과 계측기·작업자·독립 검토자·증거 경로를 기록하고 `analyze_p6_records.py`로 판정한다. P6 PASS는 heater authorization이 아니며 P7 전기안전 gate와 P9 empty-hot-zone gate가 별도로 남는다.
