# 시스템 BOM 요약

총 85개 line item, CRITICAL 59개다. 이 문서는 `build_design_boms.py`가 `bom.csv`에서 생성한 검사 요약이며 주문서가 아니다.

## 모듈별 line item

| 모듈 | 행 수 |
|---|---:|
| Assembly | 3 |
| Classification storage | 1 |
| Control | 2 |
| Control enclosure | 2 |
| Cooling | 1 |
| Diameter gauge | 2 |
| Dryer | 11 |
| Electronics | 5 |
| Extruder | 9 |
| Frame | 1 |
| Input classification | 2 |
| Power | 1 |
| Puller | 1 |
| Safety | 7 |
| Spooler | 1 |
| Stage 1 | 8 |
| Stage 2 | 9 |
| Stage 3 | 9 |
| User interface | 2 |
| Vibratory sorter | 8 |

## 비용 상태

공개 primary 후보 5개 품목의 planning floor는 426,165 KRW로 200,000 KRW cap을 226,165 KRW 초과한다. 나머지 부품·가공·미확정 배송·세금은 포함하지 않았다.

- `target_budget_design.csv`: 검증된 project-lab/donor stock을 우선하며, critical stock이 없으면 BLOCKED다.
- `engineering_recommended_design.csv`: 안전·압력·열 부품을 생략하지 않고 MPN 선정과 CNC quote를 요구한다.
- `cost_evidence.csv`: 조회일·URL·계획 환율을 보존한다.
- `procurement_routes.csv`: 32개 BUY 행의 권장 공급처·대체 공급처·AliExpress 허용 경계를 기록한다.
- `cost_rollup.csv`: 신규 구매·CNC·print filament·project-lab replacement·donor replacement와 required/optional을 분리한다.

주문·가공은 사용자 승인 전 진행하지 않는다.
