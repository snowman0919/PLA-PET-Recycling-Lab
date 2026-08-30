# Machine fabrication package — safety-orchestration-closure-v0.6.1

이 디렉터리는 shredder CUT, drive DRV, Gate-1 jig, extruder RFQ와 중복되지 않는 본체 제작품을 담는다. 각 part 폴더의 note가 공차를 지배하고 STEP은 3D 형상, DXF/STL은 견적 reference다. Frame은 겹치는 profile solid가 아니라 `frame_cut_list.csv`의 butt-joint cut length로 조립한다. 모든 주문은 사용자 승인 전 HOLD이며, donor 치수와 Gate-1/2/3/5 상태는 대체할 수 없다.
