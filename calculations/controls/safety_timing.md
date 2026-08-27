# 제어 안전시간·전력중재 계산

상태: `SOFTWARE_TIMING_ANALYSIS_NOT_PHYSICAL_SAFETY_VALIDATION`. Source는 `safety_timing.py`, 기계판독 결과는 `simulation/control/safety_timing.json`이다.

Mega main loop는 10 ms, Pi heartbeat timeout은 750 ms다. 따라서 Pi process·USB cable 상실에서 다음 loop까지 포함한 software safe-output 최악 지연은 760 ms다. AVR watchdog은 nominal 2 s로 별도 hang 경로를 차단한다. 이 수치는 E-stop safety relay의 물리 opening time, contactor arc extinction, motor coast-down이나 cutter 정지시간을 포함하지 않는다.

Jam sequence는 current/load와 encoder speed-drop이 동시에 250 ms 지속될 때 feed를 제한하고, 추가 500 ms 뒤 forward drive를 끈다. 300 ms 정지 확인 후 800 ms reverse, 1,000 ms retry를 최대 3회 허용한다. Persistent jam은 loop quantization을 포함해 7.372 s 이내 `FAULT_JAM`으로 latch된다. 실제 inertia와 파편 rebound 때문에 reverse time을 늘리려면 coupon과 containment review가 먼저 필요하다.

600 W 사용자 진술에 80% provisional ceiling을 적용한 480 W 중재에서 extrusion worst-case non-heater reserve 396 W가 요청되면 300 W heater request를 84 W, scale 0.28로 제한한다. Normal 추정 reserve 226 W와 steady heater 84 W는 제한 없이 310 W다. 실제 PSU label, driver efficiency, cable/terminal temperature-rise와 motor dyno가 더 낮은 한계를 제시하면 firmware ceiling도 즉시 낮춘다.
