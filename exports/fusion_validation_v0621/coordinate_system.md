# LC11 좌표계 및 선택 계약

단위는 mm, N, N·mm, MPa이다. 부품 local 좌표에서 +Z는 auger 축을 따라 hopper
방향이고 +X/+Y는 단면 평면이다. 중력과 5.4 N inventory load는 `-Z`, 2.2 N·m
reaction torque는 오른손 법칙의 `+Z`이다.

개별 STEP을 함께 import할 때 PF-05 base를 `(0,0,0)`에 두고 PF-04를 `(0,0,+3 mm)`로
이동한다. 이는 source assembly의 PF-05 `z=-115 mm`, PF-04 `z=-112 mm` 배치와 같다.
`process_feed_assembly.step`은 이 배치와 주변 hopper를 시각적으로 대조하기 위한 것이며
LC11 structural mesh에는 포함하지 않는다.

선택은 이름이 아닌 기하 규칙으로 재확인한다.

- 고정: PF-05의 local `z=0` 평면에 있는 지름 27–48 mm annular flange face.
- 하중: PF-05의 local `z=115 mm` 평면에 있는 상단 annular face에 분포된 axial force와
  remote moment를 적용한다.
- PF-04: source/axis reference만 유지하고 attachment study에서 suppress한다.

Fusion import 또는 repair가 face identity를 바꾸면 operator가 위 기하 규칙으로 다시
선택하고 evidence screenshot에 coordinate triad, constraint, force, moment를 함께 남긴다.
