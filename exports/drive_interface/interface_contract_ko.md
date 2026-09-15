# GGM v0.8 분쇄기 구동 인터페이스

Revision: `final-design-fabrication-closure-v0.8`

현재 powered 기준은 `GGM K9DG60N2 + K9G75C -> GGM 보호 커플링 -> 2x6201 지지 jackshaft -> direct-keyed #35 12T:30T -> CUT-05R`이다. 12T는 jackshaft의 4x4 key, 30T는 CUT-05R의 6x6x20 key가 토크를 전달한다. Key가 아닌 set screw/clamp 마찰만으로 토크를 전달하지 않는다.

두 sprocket의 exact MPN은 아직 승인되지 않았다. 수령품은 key/bore가 해당 shaft와 맞고 maker의 독립 axial-retention feature가 있어야 한다. Retention hardware는 축방향 위치만 유지하며 체결 토크는 수령품 maker 값 확인 전 `HOLD`다. 조립 후 각 sprocket tooth/root radial TIR <=0.10 mm, total axial shift + U95 <=0.20 mm, chain plane alignment <=0.20/150 mm, midspan slack 2-3%를 확인한다. 이 조건을 만족하지 못하면 adapter revision을 새로 발행하며 구형 `DRV-02`를 임의 재사용하지 않는다.

`DRV-03/DRV-03R` phase gear pair는 계속 active이며 matched 8 mm key가 shaft torque/phase를 전달한다. `DRV-01`, `DRV-02`, `DRV-A42`, `DRV-A60`, `DRV-F01A/B/P`는 generic donor-drive compatibility archive이며 현재 GGM fabrication baseline에서는 superseded다. 이 디렉터리의 해당 STEP/DXF가 존재하더라도 제작 승인으로 해석하지 않는다.

현재 보호 기준은 gearbox software limit 8.0 N.m, mechanical protection coupon 8.8-9.3 N.m, motor-lead current calibrated range 0-6 A다. 과거 14/18/22 N.m donor-drive hierarchy와 50 A current calibration은 GGM v0.8 물리 합격기준이 아니다.

Controlling sources: `control/ggm_drive_contract.json`, `analysis/drive_acceptance_v08/drive_component_register.csv`, `validation/physical_v08/P3_GGM_BENCH_KO.md`, `validation/physical_v08/P4_SHREDDER_COUPON_KO.md`.
