# v0.6.2.1 공정 CAD parent 시각 검토

- 검토일: 2026-08-31
- 범위: `PF-01` hopper, `PF-04` auger, `SR-01` return wedge, `SR-02` anti-ribbon comb의 FreeCAD 투영과 생성 manifest
- 합성 미리보기: `validation/visual_review/v0.6.2.1/process_overview.png`
- 판정 범위: 디지털 형상 검토만 수행했으며 제작·조립·입자 거동·강도 실험이 아니다.

## 확인 결과

- PF-01은 위쪽 개구가 넓고 throat로 수렴하는 steep-wall 단일 hopper이며 두 번째 material path를 만들지 않는다.
- PF-04는 root와 외경 사이에 연속 양의 이송 flight가 있고 전체 bounding box가 `24.06 x 24.06 x 108.00 mm`다.
- SR-01은 screen 위 dead pocket으로 떨어지는 형상이 아니라 cutter engagement 쪽으로 상승하는 wedge 방향을 갖는다.
- SR-02 comb은 교체 가능한 back bar와 다중 tooth를 가지며 long PET strip의 정렬 통과를 끊는 형상이다.
- 네 부품 모두 투영에서 자기교차나 열린 외곽을 발견하지 못했고, machine-readable 검사상 10개 part는 valid single solid이며 모든 축이 210 mm 이하이다.
- nominal assembly collision 검사에서 auger/housing 및 agitator/hopper 공통 체적은 0.01 mm³ 미만이다.

## 제한과 후속 gate

- 도면은 설계 판단용 투영이며 공차·용접·굽힘 전개·bearing/fastener 상세 제작도 승인을 대신하지 않는다.
- PF-04/PF-05의 2.2 N·m attachment 반력은 기존 Fusion LC01–LC10에 없으므로 `LC11_FEEDER_ATTACHMENT` 실제 solve 전에는 해당 부착부를 구조 검증 완료로 표시하지 않는다.
- debris, cable, deflection, tolerance stack 및 service 손 접근은 실물 lockout 상태의 조립 검증이 필요하다.

판정: `CAD_VISUAL_REVIEW_PASS_WITH_LC11_EXTERNAL_BLOCKER`.

## PDF 재생성 시각 검토

`build_manual_ko.pdf` 8쪽, `design_report_ko.pdf` 8쪽, `digital_release_report_ko.pdf` 3쪽을 Typst로 재생성한 뒤 80 dpi 전 페이지 contact sheet로 확인했다. 페이지 누락, 잘린 표/그림, 겹친 본문 또는 빈 페이지는 발견하지 못했다. 이는 문서 layout 검토이며 문서에 기술된 물리 성능의 실증이 아니다.
