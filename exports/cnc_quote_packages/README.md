# CNC·sheet-fabrication RFQ precheck package

상태: `RFQ_PRECHECK_ONLY / NOT_FABRICATION_RELEASED / NO_ORDER_AUTHORIZED`.

이 디렉터리는 업체가 공정 가능성·누락 정보·대략 견적 범위를 회신할 수 있도록 BOM Part ID를 STEP/DXF/도면 메모에 묶는다. 최종 치수도·GD&T·재료 규격·열처리·표면처리·검사 성적서 요구가 닫히지 않았으므로 즉시 제작용 도면 세트가 아니다.

| 패키지 | 행 수 | 범위 |
|---|---:|---|
| `shredder_package.csv` | 12 | Stage 1 twin-shaft와 Stage 2 screened granulator |
| `extruder_package.csv` | 5 | screw barrel breaker die와 mixed-source thrust plate |
| `sheet_metal_package.csv` | 5 | compact dryer와 control enclosure |

## 업체에 요청할 회신

- 각 Part ID별 공정·setup·최소수량·단가·lead time·재료/열처리/검사 포함 여부
- STEP와 DXF 불일치 또는 가공 불가능 형상 및 필요한 공차 완화
- pressure/hot-zone/cutter 부품의 추적 가능한 소재 증명과 외주 열처리 범위
- 세금·배송·후처리를 분리한 견적과 견적 유효기간

## 주문 전 필수 gate

1. Donor shaft/bearing/motor 실측과 coupon 결과를 CAD에 반영한다.
2. Cutter impact/containment와 extruder pressure/relief risk review를 닫는다.
3. 부품별 datum·fit·GD&T·표면거칠기·열처리·검사표가 있는 최종 도면을 승인한다.
4. 사용자에게 실제 견적과 예산 차이를 제시하고 명시적 발주 승인을 받는다.

`EXT-THR-001`은 BOM primary source가 BUY인 bearing assembly에 plate machining이 섞인 행이라 extruder package에 보조로 포함했다. 따라서 package 22행과 BOM의 primary CNC/FABRICATE 21행은 모순이 아니다. 비용 rollup은 primary source 기준이며 mixed-source 비용은 여전히 TBD다.
