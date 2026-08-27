# ADR-008: PLA/PET dual-profile desiccant dryer와 gravimetric feed check

- 상태: Accepted for proof baseline
- 날짜: 2026-08-28

PLA와 bottle PET를 같은 저온 filament-dryer recipe로 처리하지 않는다. PLA는 45 °C/6 h 저온 branch, PET는 140 °C 2 h 후 160 °C 4 h의 고온 dry-air branch를 사용한다. PET branch는 -40 °C dew point와 50 ppm moisture endpoint를 물리 검증하기 전 생산 승인하지 않는다.

ID 140×320 mm 금속 hopper와 40 mm 단열을 사용하고, 고온부에 PLA/ABS 구조물을 직접 사용하지 않는다. PLA 60 W와 PET 240 W heater branch는 서로 다른 독립 high-limit/fuse를 가지며 hardware interlock로 상호배제한다. PET 건조와 extruder 최대 가열도 power arbiter로 시간 분리한다.

정량공급은 30 mm auger 2–6 rpm과 간헐 agitator를 baseline으로 하고, load-cell 질량감소와 motor current를 융합해 bridge/empty를 구분한다. dry-air 보존과 hot-gas 역류 방지를 위해 출구 이중 gate 또는 rotary airlock을 후속 CAD에 포함한다.
