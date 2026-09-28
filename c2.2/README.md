# C2.2 — VP1 전체 기계 Isaac Sim 검증

`c2.1/cad/PPR_VP1.step`을 전체 솔리드 단위로 변환해
`sim/assets/usd/full_machine.usda`에서 실제 조립 운동과 소재 경로를 검사한다.
현재 STEP/USD SHA와 최종 실행 결과는 루트 `STATUS.md`가 기준이다.

## 주요 경로

- `sim/assets/convert.py`: STEP 솔리드와 조립 이름을 STL/sidecar로 대응시킨다.
- `sim/full_machine.py`: S1/S2/오거/풀러/와인더의 종속 운동과 접촉을 실행한다.
- `sim/flow_localize.py`: 호퍼, S1 배출, 슈트, S2 입구를 단계별로 주입해
  실제 통과·정체·world 이탈을 구분한다.
- `sim/verify_full.py`: 전체 운동 추적, 접촉, 소재 경로 결과를 판정한다.
- `sim/render_reviewer_scenes.py`: 동일 USD/STEP에 묶인 검토 이미지 4장을 만든다.
- `results/full_machine/`: 최종 기계 판독 JSON, runner log, 이미지 증거.

## 검증 경계

이 시뮬레이션은 결함 발견과 디지털 운동/경로 검증이다. 파괴 물성, 처리량,
토크, 열, 마모, 수명과 안전 containment의 물리 적합성을 인증하지 않는다.
PSU는 24V 33A/명판 800W이며 500W는 소프트 목표, 792W는 강제 상한이다.
구매·제작·통전·물리 운전·main 병합은 명시적 승인 전 **HOLD**다.
