# Shredder particle screening — v0.6.2

- 판정: `MITIGATION_REQUIRED`
- 방법: 12,000개/재료 seeded Monte Carlo reduced-order contact/transport screening
- 경계조건: 5 mm screen, width 2–9 mm, 재료별 aspect ratio·wall friction·fill 범위
- PLA: oversize recirculation 74.0%, bridging 43.5%, mean residence 7.06 cycles
- PET: oversize recirculation 76.4%, ribbon escape 26.2%, bridging 55.6%, mean residence 7.79 cycles
- 완화: removable screen inspection/cleaning, ribbon-rich feed 배제, Gate-2 회수율·bridging coupon 시험
- 한계: fracture-calibrated DEM이 아니며 실제 chip size·통과율을 검증하지 않는다. granulator 추가는 architecture freeze 때문에 자동 제안/적용하지 않는다.
