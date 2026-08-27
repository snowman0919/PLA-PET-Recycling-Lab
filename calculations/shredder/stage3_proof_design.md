# Stage 3 granulator proof design

- 상태: 해석·CAD 후보, 물리 시험 미검증
- 입력: 6–12 mm
- 목표 출력: 3–6 mm

## baseline

| 항목 | 값 | 제한 |
|---|---:|---|
| rotor OD/core | 40/34 mm | fused insert envelope |
| cutting rows | 4열 × 12 segment | segment 4 mm, 총 22° stagger |
| active width | 48 mm | feed/retention screen과 함께 검증 |
| shaft/bearing | 17 mm / 6203-2RS 후보 | bearing center span 68.4 mm |
| stator clearance | nominal 0.15 mm | measured shim stack 필요 |
| screen | flat proof 4/5/6 mm, 8 mm pitch | 최종 curved screen/support 아님 |
| speed | 120–240 rpm | 8–16 row-pass/s |
| continuous/trip/proof | 5–12 / 20–28 / 35 N·m | coupon에서 갱신 |

4 mm segment full-shear 상한에서 PET folded wall은 약 `5.9 N·m`, PLA 2 mm shell은 `14.4 N·m`, 두 segment 동시 engagement는 `28.8 N·m`다. 17 mm shaft, 35 N·m proof, 68.4 mm span은 nominal von Mises `88.3 MPa`, `SF/Kt1.6=2.16`, 처짐 `0.014 mm`다. fatigue, shoulder, keyway와 insert pocket FEA는 제외한다.

## screen 비교

50×48 mm flat proof plate에 36개 원형 hole을 둔 기하 open-area ratio는 다음과 같다.

| opening | pitch web | geometric open area |
|---:|---:|---:|
| 4 mm | 4 mm | 18.8% |
| 5 mm | 3 mm | 29.5% |
| 6 mm | 2 mm | 42.4% |

이는 flake blocking, curved support, edge ligament와 실제 유효 유량을 포함하지 않는다. 4 mm는 입도는 작아지지만 체류시간·dust·열이 증가할 수 있고, 6 mm는 throughput은 유리하지만 긴 PET strip 통과 위험이 있다. 5 mm를 baseline coupon으로 쓰고 세 후보를 같은 batch로 비교한다.

## power와 운전

12 N·m에서 120/180/240 rpm의 기계 출력은 약 151/226/302 W다. reducer/driver 효율과 jam reverse를 포함하면 전기입력은 더 크며, heater와 동시 운전을 포함한 24 V PSU budget은 별도다. Stage 2와 drive를 공유한다고 가정하지 않는다.

## Gate

1. 4/5/6 mm screen별 3/6/12 mm sieve mass fraction, 3 mm 미만 fines와 긴 strip 기록
2. screen differential load 또는 carrier strain, current, rpm drop와 residence time 동기화
3. screen clog/bridging과 clean-out 시간 비교
4. 240 rpm 무부하 balance/temperature 후 guarded material coupon
5. oversize는 자동 또는 폐쇄형 수동 recirculation으로 Stage 3 입구에 복귀시키고 dryer로 bypass하지 않음
