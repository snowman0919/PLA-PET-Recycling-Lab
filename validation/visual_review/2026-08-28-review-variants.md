# CAD review variant 시각검토 — 2026-08-28

`renders/review`의 22개 PNG를 개별 1600×1200 원본으로 검사했다. Section 7종, transparent/x-ray 4종, exploded 5종, tool-access 3종, cable-routing 2종, slicing-orientation 1종이 존재한다. 추가된 전체 assembly section은 `2026-08-28-two-tower-assembly.md`에서 별도로 판정했다.

확인 사항:

- Exploded scene에서 주요 disconnected shell의 분리 방향과 조립 순서를 읽을 수 있다.
- X-ray는 hidden-line removal을 끈 wireframe이며 내부 광로·heater/hopper·enclosure segregation 검토에 사용한다.
- Section은 triangle centroid clipping이라 닫힌 section cap이나 실제 절단면 해칭이 아니다.
- Tool-access 원은 wrench/tool sweep 검토 prompt이고 fastener별 실제 reach 판정이 아니다.
- Cable route는 power/sensor/PE topology overlay이며 실제 길이·connector·bend radius는 H01–H18과 physical harness mock-up으로 닫는다.
- Slicing preview는 높이 band만 표시하며 support·seam·infill·G-code를 승인하지 않는다.

Montage에서 빈 이미지·심각한 crop·label 누락은 없었다. 일부 cutaway의 긴 triangle edge는 cap을 생성하지 않는 의도된 open-section 표현이며 fabrication geometry로 사용하지 않는다.
