# 입력 분류기·7-port 저장 분배기 제작 주석

상태: **공간·운동학 proof / 제작 승인 전**

- 입력 외피: 320×220×220 mm, 최대 병 기준 Ø66×210 mm.
- 상부 게이트 닫힘 위치와 하부 게이트 열림 위치의 수직 간격은 110 mm다. 두 게이트가 동시에 열리지 않도록 기계식 cam과 positive-opening 스위치를 실물 coupon에서 검증한다.
- `classifier_gate_half.dxf`는 105×200×4 mm 한쪽 패널의 2D 기준이다. 힌지축·cam·bearing·fastener는 선정품 도면을 반영한 뒤 절삭한다.
- 카메라, 백라이트, 기준 광선과 병은 광학 keep-out이다. 정확도는 재료/색/오염/조명별 source-object-grouped 데이터셋으로 승인한다.
- 7개 출구는 고정된 6색 bin과 Reject에 대응한다. 외부 grounded hose, bin 용량, sealing 및 교차오염 관리는 별도다.
- 파편이 닿는 면과 축/힌지는 금속 또는 충격 적합 재료를 사용한다. PLA 출력물은 구조·containment 부품으로 승인하지 않는다.

관련 파일: `input_classifier_proof.FCStd`, `classification_storage_proof.FCStd`, `classifier_gate_pair.*`, `color_diverter_rotor.*`.
