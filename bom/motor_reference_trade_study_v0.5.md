# 분쇄기 기준모터 trade study — v0.5

|항목|GMP42-775PM ratio 51|GMP60-60127-2460 ratio 47|판정|
|---|---:|---:|---|
|전압|24 V|24 V|동일|
|출력 무부하/정격속도|110/90 rpm|95/70 rpm|둘 다 12:30 후보 범위|
|출력 정격토크|26 kg·cm = 2.5497 N·m|100 kg·cm = 9.80665 N·m|GMP60 우세|
|모터 정격전류|2.2 A|8.2 A|GMP60은 20 A branch 내 정격점|
|stall current|7.5 A|31 A|GMP60 stall은 branch fuse/DRV-F01/전자 trip로 지속 금지|
|12:30, η=0.85 cutter 속도|36 rpm|28 rpm|둘 다 속도범위|
|12:30, η=0.85 cutter 정격토크|5.42 N·m|20.84 N·m|42GP는 14 N·m 미달|
|기준 형상|DRV-A42, Ø42/44.5 body, Ø10 shaft|DRV-A60, Ø60.5 body, Ø12 shaft|Adapter만 교환|
|선정상태|`REJECTED_CONTINUOUS_TORQUE`|`DIGITAL_REFERENCE_ONLY`|실물 Gate-1은 별도|

공식 자료: `https://www.ttmotor.com/uploads/GMP42-775PM.pdf`, `https://www.ttmotor.com/uploads/GMP60-609760127.pdf` (확인일 2026-08-29). Marketplace의 maximum/stall/gearbox allowable torque를 continuous rated torque로 바꾸어 쓰지 않는다.

Project-lab 우선순위는 (1) 24 V wheelchair/conveyor geared DC, (2) 검증된 scooter/e-bike geared motor, (3) 60 mm급 신규 motor RFQ다. 어떤 후보든 cutter 20–40 rpm, 연속 14 N·m, 3초 peak 24 N·m, case ≤80 °C/30분과 DRV-F01 22 N·m cutter-equivalent calibration을 만족해야 한다.

