# Vibratory sorter visual/solid review — 2026-08-28

## 증거

- `vibratory_sorter_after_motor_mount.png`
- `renders/modules/vibratory_sorter_proof_{front,right,top,isometric}.png`
- `simulation/vibration/vibratory_sorter_response.json`
- `simulation/vibration/vibratory_sorter_geometry.json`
- `validation/fabrication_review/vibratory_sorter_proof.json`

## 확인 결과

- 2단 screen이 30.5 mm normal clear로 분리됨
- top retained / bottom retained / bottom pass의 세 경로 envelope가 분리됨
- motor와 eccentric가 금속 bracket을 통해 moving tray 쪽에 배치됨
- motor–base 46.96 mm, bracket–base 36.66 mm, motor–fines bin 22.52 mm
- eccentric–bracket 최소 4.0 mm로 2.8 mm nominal motion allowance 초과
- isolator upper stud가 tray rail에 연결되고 rubber body는 base에 놓임
- 28×18×8 mm service clamp는 210 mm print volume 내이며 M5 screw hole을 가짐

## 시각 한계와 수정 이력

초기 proof에서는 motor envelope가 base 쪽에 떠 있어 moving mass load path가 불명확했다. motor를 상류 tray 하부로 이동하고 metal bracket을 추가했다. screen 격자의 많은 삼각분할선은 software STL render 결과이며 균열이 아니다.

chute는 흐름 방향 envelope일 뿐 flexible boot와 seal이 없고, fines bin은 dust-tight latch 상세가 없다. screen은 source mesh가 아니라 square-grid proof다. eccentric guard, wiring loop, service interlock와 60 mm cassette 인출 공간은 최종 assembly에서 추가 검증한다.

결론: 계산·명목 clearance·세 경로 개념은 proof 통과지만 진동 운전·분진·분류 승인 상태가 아니다.
