# 변경 이력

## compact-single-path-v0.3 — 2026-08-28

- 이전 연구 snapshot을 tag와 archive branch로 동결했다.
- PLA/PET의 기계 경로를 하나의 470 x 700 x 930 mm cabinet으로 재설계했다.
- 외부 pre-dry + sealed maintenance hopper, 16 mm x 16 L/D 공용 screw, vertical forming path를 채택했다.
- 자동 분류, 색상 routing, custom PCB, 대형 enclosure와 별도 forming 구조를 active scope에서 제거했다.
- FreeCAD source, print package, 비용/경제성, firmware profile, 검증과 한국어 PDF를 새 revision으로 교체했다.
# solid-manifold-openmodelica-v0.4 — 2026-08-29

- Active manufacturing CAD를 valid closed solid로 정리하고 motion/service keep-out을 격리했다.
- PrusaSlicer 2.9.6 actual plate/G-code와 913.67 g nominal, 1,023.31 g planning mass를 생성했다.
- CAD mass/inertia를 Modelica package로 생성하고 18 scenario/6 sensitivity sweep를 자동 판정한다.
- 22 N·m upstream fuse 하중 envelope를 9개 구조 screening과 2개 CalculiX deck에 연결했다.
- Firmware profile을 baseline에서 생성하고 donor torque calibration `verified` 전 start를 거부한다.
- Conditional target 178,420 KRW, reserve 포함 absolute 198,420 KRW로 value-engineering했다.
- Release는 `DIGITAL_FABRICATION_BASELINE`; physical result는 `PHYSICAL_NOT_RUN`이며 Gate-1 전 main 승격과 full order는 잠겨 있다.
