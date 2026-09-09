# GGM 구동부 제조도면·수령·교정 마감 r2

작업 위치는 `/home/monad/develop/PPR`, branch는 기존 `final-design-fabrication-closure-v0.8`다. 새 branch/worktree나 develop 하위 별도 프로젝트를 만들지 않았다. raw 계산·렌더는 이 디렉터리 안에 둔다.

## 산출물
- `exports/final/drive_ggm_v08/manufacturing_r2/PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf`: A3 23쪽,21도면종,39개 제조 CAD 객체 대응.
- 같은 폴더의 `PPR_GGM_ASSEMBLY_INSPECTION_KO_r2.pdf`: A4 5쪽 조립·수령·정렬·핀·전류 검사 기준.
- `drawing_contract.json`과 `define_drawings.py`: 명시한 공차·공정·검사 기준의 원본. 제조사 실측이나 보증값이 아니다.
- `draw_parts.py`: 실제 FCStd에서 TechDraw HLR 정투상·원통면 좌표·전체 치수를 추출해 SVG와 DXF를 생성한다.
- `inspection_packet_template.json`: 모든 실측값이 비어 있고 performed=false다. 측정값을 만들어 넣지 않았다.
- `inspection.py`: 기록의 단위·불확도·lot/serial·원본 해시·방향·교정 holdout을 검사한다. firmware write/장비 제어 기능은 없다.

## 기계 수정
`cad/freecad/drive_v08/detail.py`의 압출6201 캡은 ID18에서ID27.4로 바꾸고 thrust plate 후면에D27.4x0.30 relief를 추가했다. 외륜 지지를 남기고 씰/내륜 접촉을 피하기 위한 디지털 변경이다. 실제 sealed bearing의 치수와 자유회전은 미검사다.

`guard_details.py`는 두 coupling cover의 split seam·전면 flange·M3 mounting을 정의하고, chain cover에는 두 mounting tab과 대응 탭공을 추가한다. 앞/뒤 bearing판은 D04/D04R로 분리한다. cover 조립체는 각각 두 half-part다.

## 해석 경계
`check_retainer_strength.py`는 기존/수정 thrust plate의3단계 C3D4, `check_retainer_quadratic.py`는3단계 C3D10 계산을 수행한다. 6MPa·D16.22에 따른1,239.8N을51102 seat에 가하고4개bolt bore를 고정한 상온 선형 국부모델이다. 실제 preload·접촉·열간 물성·frame은 검증하지 않는다.

최초 FRD 공통 parser가 SI 단위를 가정하는 것을 발견해 mm/N/MPa deck의 변위·응력 표시 변환을 명시적으로 수정했다. 원시 deck/FRD는 보존했다. 선형0.6mm 재실행은300초 timeout, 초기 curved-midnode quadratic mesh는 Jacobian 오류로 제외했다. 최종 quadratic은 straight-midnode 요소를 사용했다. 실패를 성공 횟수에 포함하지 않는다.

`finish_review.py`는 변위 수렴과 최대응력 수렴을 별도로 보고한다. 최대응력은 경계/모서리에서 mesh-sensitive하므로 전체 응력 적격성이나 기계 승인을 주장하지 않는다.

## 실제 검사와 승인
관련 재고 기록에는 모터가 아직 미구매이고 수령·정렬·핀·전류 실측 자료가 없다. `physical_record_status.json`의 네 domain은 모두 NOT_RUN이다. 별도 시험 허가를 요청하거나 실행하지 않았고 전체 기계는 HOLD다. 정의한 디지털 검증 종료와 사용자의 별도 승인 이전에는 구매·가공·통전·모터/핀 시험을 시작하지 않는다.

## 재생성
FreeCAD1.1.3에서 구동부 `analysis/drive_integration_v08/rebuild.py`를 먼저 실행한다. 일반 Python에서 `define_drawings.py`, `finish_forms.py`, `test_inspection.py`를 실행한 뒤 FreeCADCmd로 `draw_parts.py`와 `check_mfg_geometry.py`를 실행한다. 한국어 문서는 PYTHONUTF8=1을 사용한다. 기존 Typst0.15.1로 drawing_book.typ과 assembly_inspection_ko.typ을 컴파일한다. PDF는 Poppler로 렌더해 검토했다.

소스·STEP이 바뀌면 해시만 고치지 말고 해당 계산/도면을 재생성한다. 과거 r1 ZIP은 보존하고 현재 r2와 섞어 발주하지 않는다.

## r2 후속 디지털 폐쇄
- 추력판의 rigid bolt-bore 주변 nodal peak는 release metric에서 제외하고, 실제 bearing-seat와 bolt 이상화 영역을 제외한 load-path web의 regional stress를 별도 계산한다.
- r2 C3D10 3.0→2.0 mm에서 regional max 변화는 약 1.25%, p95 변화는 약 1.35%로 수렴하며, fine regional max는 약 14.98 MPa다. 상온 S275 275 MPa reference 대비 screen SF는 약 18.36이다.
- 이 수치는 냉간 선형 국부 screen이며 preload/contact/hot-joint 적격성을 대신하지 않는다. rigid-boundary nodal peak는 diagnostic으로 계속 보존한다.
- GGM screw overspeed guard는 `control/ggm_drive_contract.json`의 hard limit 20 RPM과 일치하도록 수정했다. 독립 AVR build는 현재 release HEX와 동일함을 다시 확인한다.
- 사용자 정책에 따라 `validation/results/v08_full_compliance.json`의 전체 디지털 상태가 `PASS`가 아니면 수령·정렬·보호핀·전류교정 물리 기록은 검사기에서 fail-closed로 거부한다. 현재 전체 상태는 FAIL이므로 네 physical domain은 모두 `NOT_RUN`이다.
