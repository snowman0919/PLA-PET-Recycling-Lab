# ADR-003: Stage 1 narrow throat와 drive 선정 보류

- 상태: Proposed baseline
- 날짜: 2026-08-28

## 결정

200 x 200 mm 외형의 입력을 200 mm cutter 폭으로 한 번에 자르지 않는다. anti-reach hopper와 agitator/gate가 병과 hollow PLA 출력물을 62 mm active cutter stack으로 순차 포획하도록 한다. 초기 cutter는 OD 60 mm, 축간거리 50 mm, 20 mm shaft, 15~30 rpm 탐색범위를 사용한다.

Stage 1 drive는 donor NEMA17로 확정하지 않는다. 첫 비교 우선순위는 실제 donor dyno 결과, 24 V DC geared motor, geared motor + guarded chain final reduction 순이다.

## 이유

목표 처리량 200 g/h는 200 mm 동시 절삭폭을 요구하지 않는다. 폭을 줄이면 cutter/shaft/plate/CNC 비용과 동시 tooth engagement torque가 감소한다. 반면 input folding과 bridge 위험이 증가하므로 hopper agitator와 feed gate가 필수 인터페이스가 된다.

## 기각·변경 조건

- bottle/PLA coupon이 throat에서 지속 bridge
- 200 g/h에서 feed duty가 과도하거나 flake shape가 Stage 2 요구와 불일치
- 20 mm shaft 해석이 keyway, overhang 포함 SF 2 또는 clearance/3 기준 미달
- 안전한 anti-reach path 안에서 500 mL 병 capture 실패
