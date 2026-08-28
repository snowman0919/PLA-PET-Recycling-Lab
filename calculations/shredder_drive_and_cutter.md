# Cycloidal-derived cutter와 interchangeable drive

CUT-01은 7 hook, pitch의 76% cycloidal capture rise와 24% fast relief를 쓰는 비대칭 profile이다. Actuator는 특정 MY1016Z/coupling에 종속되지 않고 DRV-01 slotted plate, DRV-02 replaceable hub, #35 chain, motor-side 22 N·m slip/fuse를 사용한다.

토크 계층은 `14 < 18 < 22 < 34 < 48 N·m`(normal < electrical trip < upstream relief < phase gear/key allowable < shaft/cutter allowable)이며 digital check는 `True`다. 22 N·m relief에서 cutter tip 758.6 N, phase tangential/separating 916.7/333.6 N, chain tight-side increment 603.0 N이다. Phase key는 sacrificial element가 아니다.

Current threshold는 donor calibration 뒤 `I = I0 + T/(Kt × ratio × efficiency)`로 계산한다. 현재 reference sensitivity는 실제 donor 합격값이 아니며 universal 16/18 A limit를 release하지 않는다. Gate-1 및 donor calibration은 `PHYSICAL_NOT_RUN`이다.
