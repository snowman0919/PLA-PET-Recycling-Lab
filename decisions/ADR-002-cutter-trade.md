# ADR-002: 공용 cutter 최소화 trade study

수치는 RFQ/coupon 전 planning range다.

| 평가 | Candidate A: dual-shaft+screen | Candidate B: pre-shredder+granulator |
|---|---:|---:|
| Unique CNC families | 4 | 7 |
| Total machined parts | 24 | 39 |
| Motor | 1 | 2 |
| Bearing | 4 | 6 |
| Module envelope | 220 x 210 x 190 mm | 340 x 250 x 260 mm |
| Continuous/trip torque | 18/30 N·m | 18/30 + 7/12 N·m |
| 3–6 mm fraction | 미검증 55–85% 가정 | 미검증 75–95% 가정 |
| Cleaning time | 12–20 min | 25–40 min |
| CNC/fabrication allowance | 56,000 KRW | 105,000 KRW |
| Printed mass | 0.28 kg | 0.45 kg |
| Jam recovery | bounded reverse 후 lid-off manual | stage별 isolation 필요 |

Candidate A를 채택한다. 동일 hook disc 반복, standard spacer/shaft/bearing, removable 5 mm screen과 oversize 수동 recirculation으로 단순화한다. 3–6 mm fraction은 Gate 1/2가 입증하지 못하면 그때만 별도 granulator를 재검토하며 현재 CAD/BOM에 숨겨 넣지 않는다.
