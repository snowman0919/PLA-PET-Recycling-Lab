# PPR — 균일 직경 필라멘트를 위한 통합 재활용기
목표와 경계는 [KODEX.md](KODEX.md), 현재 증거·작업은 [STATUS.md](STATUS.md), 압출 방법 비교는 [품질 경로 결정 기록](docs/decisions/filament-quality-route.md)을 따른다.

제품 범위: 호퍼 → S1 2축 파쇄 → 선택 이송부 → S2 편심/역자전 분쇄 → 버퍼 → 수평 압출 → 냉각/직경 계측 → 가압 인출 → 장력 분리 권취.
최종 목표는 냉각 후 일정한 1.75mm 필라멘트를 경제적으로 만드는 것이다. 현재 연결 이송과 실제 필라멘트 생산 모두 미완료다.
상류 실패와 별개로 최종 제품의 같은 압출 모듈에 건조 기준 원료를 넣는 설계/디지털 시험을 진행할 수 있다. 전체 제품 성공과는 구분한다.

## 작업 자산
- c2.1/cad/PPR_VP1.step: 전체 기계 STEP
- c2.1/cad/PPR_C2_1_machine_integration.FCStd 및 c2.1/src/: 편집 원본/생성기
- c2.1/bom/system_bom.csv, .xlsx: 활성 BOM
- c2.1/firmware/, electrical/: 제어/전장 자산
- c2.2/sim/assets/usd/full_machine.usda: 대응 Isaac 장면
- c2.2/results/full_machine/layout_comparison.json: 기준안/재배치안 비교
- tests/, c2/tests/, c2.1/tests/, c2.3/tests/: 범위별 회귀 자산

재현은 해당 생성기/실행기의 --help와 결과의 원본 해시·설정을 사용한다. CAD/STEP, 충돌 메시/USD, BOM, 시험 결과를 같은 후보로 맞춘 후 해당 verify_artifacts를 수행한다.
역사 실험의 재실행이나 Graphify 완료를 새 제품 작업의 선행조건으로 만들지 않는다. 숫자·PASS 명칭은 당시 범위에서만 유효하다.
물리 제작·구매·통전·실물시험·main 병합은 사용자 승인 전 HOLD다. MIT 및 LICENSE-HARDWARE를 유지한다.
