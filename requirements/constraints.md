# 제약조건

## 강한 제약

- 지원 재질: PLA, PET; TPU와 불확실 재질은 Reject
- 안정 연속 처리량 목표: 200 g/h 이상
- 출력: 1.75 mm, 초기 합격 1.75 ± 0.05 mm
- 신규 구매 목표: 200,000 KRW 이하
- CNC 비용 목표: 100,000 KRW 이하
- 공급 전원: donor 24 V 600 W PSU 한 대, label 확인 전 정격 확정 금지
- 제어 자원: Raspberry Pi 4, Arduino Mega 2560 우선 재사용
- 출력 volume: 220 mm급 printer에서 margin을 두고 부품 각 축 210 mm 이하
- source of truth: FreeCAD Python과 parameter files
- cutter/screw/shaft/bearing plate/hot-zone 핵심부는 금속
- 사용자 승인 없는 구매·CNC 주문 금지

## 설계 우선순위

1. 물리 안전과 fail-safe
2. 오염 없는 PLA/PET 분리와 품질
3. 제작 가능성·정비성
4. 안정 처리량
5. Target Budget
6. 크기·외관 최적화

예산이 안전 또는 핵심 신뢰성과 충돌하면 기능 차이를 명시한 Target Budget Design과 Engineering Recommended Design을 모두 유지한다.

## 입력 제한

자동 제거하지 않는 항목: cap, neck ring, label, adhesive, 금속, magnet, bearing, heat-set insert, fibre reinforced plastic, coating, food/drink residue. 대형 solid PLA block의 처리를 보장하지 않으며 허용 실질 두께는 cutter coupon 시험 후 확정한다.
