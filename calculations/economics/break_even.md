# 경제성 — compact-single-path-v0.3

계획 신규 현금비용은 189,500 KRW다. Donor replacement value는 현금 budget에 합산하지 않으며 `reuse_inventory.csv`의 확인 전 품목을 보유 확정으로 간주하지 않는다.

가정: 전력 0.55 kW 평균, 안정 생산 0.18 kg/h, 전력단가 180 KRW/kWh, purge 0.10 kg/재질전환, usable yield 75%, 상용 filament 22,000 KRW/kg, 세척 원료 0 KRW. 전력비는 약 550 KRW/kg이고 purge/yield를 포함한 순 절감액은 보수적으로 13,500 KRW/kg로 둔다.

- 손익분기 생산량: `189,500 / 13,500 = 14.0 kg`
- 월 2 kg 사용: 약 7.0개월
- 월 5 kg 사용: 약 2.8개월

노동, 실패 batch, external dryer 감가, replacement part와 실제 CNC 초과비용은 제외했다. 따라서 이는 구매 결정용 확정 ROI가 아니라 민감도 baseline이다.
