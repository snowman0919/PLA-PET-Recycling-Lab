# 제어함 제작 주석

상태: **격리 topology proof / 인증 패널 아님**

- 외피: 300×220×180 mm, 기준 판재 1.5 mm. backplate, 금속 partition, DIN rail과 PE stud를 포함한다.
- 고전류 영역과 logic 영역 keep-out 사이의 기준 빈 간격은 30 mm이며, 145 mm 위치 금속 partition을 둔다.
- 150×180 mm door half 두 장으로 분할한다. `control_door_half.dxf`는 한쪽 패널 외곽·M4 기준만 제공하며, 절곡 allowance·hinge·gasket·captive fastener는 선정품 도면으로 확정한다.
- E-stop은 단단한 패널에 장착하고 dual-channel safety relay에 직결한다. TFT·Mega·Pi는 안전 기능을 대체하지 않는다.
- 전원/히터와 센서/logic은 별도 duct와 gland로 배선한다. PE bonding, fuse/contactor SCCR, 열상승, 연면거리와 단자 굽힘 반경을 실제 MPN으로 재검증한다.
- 모든 field interface는 정격·절연된 conditioner를 거친다. 24 V 신호를 Mega에 직접 연결하지 않는다.

관련 파일: `control_enclosure_proof.FCStd`, `control_door_split.*`, `control_backplate_partition.*`.
