# Cycloidal-derived cutter와 interchangeable drive

CUT-01은 7 hook, pitch의 76% cycloidal capture rise와 24% fast relief를 쓰는 비대칭 profile이다. Actuator는 특정 MY1016Z/coupling에 종속되지 않고 DRV-01 slotted plate, donor-specific DRV-Axx, motor-side DRV-F01, #35 chain과 cutter-side DRV-02 hub를 사용한다.

토크 계층 `14 < 18 < 22 < 34 < 48 N·m`는 모두 cutter-shaft equivalent다. DRV-F01의 실제 motor-side setting은 12:18/24/30에서 각각 17.25/12.94/10.35 N·m이며 digital check는 `True`다. Cutter-equivalent 22 N·m에서 cutter tip 758.6 N, phase tangential/separating 916.7/333.6 N, chain tight-side increment 603.0 N이다. DRV-02와 phase key는 sacrificial element가 아니다.

Current threshold는 donor calibration 뒤 `I = I0 + T/(Kt × ratio × efficiency)`로 계산한다. 현재 reference sensitivity는 실제 donor 합격값이 아니며 universal 16/18 A limit를 release하지 않는다. Gate-1 및 donor calibration은 `PHYSICAL_NOT_RUN`이다.
