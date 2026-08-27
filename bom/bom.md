# 시스템 BOM 요약

총 82개 line item, CRITICAL 56개다. 이 문서는 `build_design_boms.py`가 `bom.csv`에서 생성한 검사 요약이며 주문서가 아니다.

## 모듈별 line item

| 모듈 | 행 수 |
|---|---:|
| Assembly | 3 |
| Classification storage | 1 |
| Control | 2 |
| Control enclosure | 1 |
| Cooling | 1 |
| Diameter gauge | 2 |
| Dryer | 11 |
| Electronics | 4 |
| Extruder | 9 |
| Frame | 1 |
| Input classification | 2 |
| Power | 1 |
| Puller | 1 |
| Safety | 6 |
| Spooler | 1 |
| Stage 1 | 8 |
| Stage 2 | 9 |
| Stage 3 | 9 |
| User interface | 2 |
| Vibratory sorter | 8 |

## 비용 상태

공개 후보 두 품목의 planning floor는 235,200 KRW로 200,000 KRW cap을 35,200 KRW 초과한다. 나머지 부품·가공·배송·세금은 포함하지 않았다.

- `target_budget_design.csv`: 검증된 project-lab/donor stock을 우선하며, critical stock이 없으면 BLOCKED다.
- `engineering_recommended_design.csv`: 안전·압력·열 부품을 생략하지 않고 MPN 선정과 CNC quote를 요구한다.
- `cost_evidence.csv`: 조회일·URL·계획 환율을 보존한다.
- `cost_rollup.csv`: 신규 구매·CNC·print filament·project-lab replacement·donor replacement와 required/optional을 분리한다.

주문·가공은 사용자 승인 전 진행하지 않는다.
