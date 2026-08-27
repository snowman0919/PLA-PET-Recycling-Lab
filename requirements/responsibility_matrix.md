# 책임 분리

| 활동 | Codex | 사용자 | Gate/증거 |
|---|---|---|---|
| 요구사항·아키텍처·계산·CAD·시뮬레이션 | 수행/검증 | 검토 | 추적 ID, source, report |
| donor inventory 절차 | 체크리스트 제공/분석 | 사진·라벨·실측 제공 | `donor_inventory.csv` |
| 3D print | STL·설정·검사기준 제공 | 출력 및 치수 측정 | inspection log |
| CNC | 도면·quote package 제공 | 견적 승인 및 주문 | 서면 승인 전 주문 금지 |
| 구매 | BOM·대체품·가격 비교 | 비용 승인 및 구매 | 날짜·출처·승인 |
| 조립 | 단계별 한국어 매뉴얼 제공 | 실제 조립 | 사진·검증 치수 |
| 고전류/heater 배선 | schematic·wire/fuse spec 제공 | 자격 있는 감독 하에 실제 배선 | continuity/insulation/earth test |
| 무부하·저부하 물리 시험 | 절차·합격기준·log parser 제공 | 장비를 조작해 시험 | 원시 log와 사진 |
| PLA/PET production test | recipe와 안전절차 제공 | 시편 준비·시험 | 30분 log, 질량, filament sample |
| 안전 승인 | 분석과 checklist 제공 | 물리 장치 최종 승인 | 모든 critical item signed |
| Git 원격·release | parent만 생성/push/tag | 인증 또는 권한 제공 | commit/tag/push status |
| subagent | 범위 설정·재검증 | 불필요 | 위임·검증 기록 |

사용자에게 물리 작업을 요청할 때는 필요한 공구, 전원 상태, 측정 지점, 단위, 위험, 합격범위와 기록 양식을 함께 제공한다.
