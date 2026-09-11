# PPR v1.0.0-rc1 - 전체 설계 및 제작 인수인계

현재 revision은 `final-design-fabrication-closure-v0.8`이다. 이 배포는 디지털 제작 후보이며 완성 기계의 성능 보증이나 안전 인증이 아니다. 이전 revision의 변경 경위와 과거 수치는 Git history에서 확인한다.

## 상태

- release state: `FABRICATION_CANDIDATE`
- design state: `FINAL_DESIGN_FROZEN` (해당 배포 snapshot; 실측 결과에 따른 후속 설계 변경 가능)
- technical handoff state: `READY_FOR_USER_APPROVAL`
- validation basis: `OPENMODELICA_CALCULIX_CLOSED_FORM_CAD`
- cross-solver state: `NOT_COMPLETED_BY_SCOPE_DECISION`
- physical validation state: `NOT_RUN`
- safety certification: `NOT_CERTIFIED`
- procurement / fabrication / commissioning: `USER_APPROVAL_REQUIRED`

사용자가 승인한 것은 소스·도면·문서·검사 자료의 GitHub prerelease 게시다. 구매, CNC, 통전, 시운전, 양산, main merge는 자동 승인하지 않는다. 실제 게시 여부는 GitHub Release에서 확인하며 `release/publication_policy.json`은 게시 권한만 기록한다.

## 전체 제품을 확인하는 순서

COMPLETE ZIP을 풀고 `python3 verify_package.py .`를 먼저 실행한 뒤 `START_HERE.html`을 연다. `repository/`는 배포 commit의 원래 파일 경로를 보존한다. `packages/`에는 FABRICATION 및 PHYSICAL-VALIDATION-LAUNCH ZIP이 포함되고 `verification/`에 같은 commit의 실제 CI 결과와 해시 검증 근거가 있다.

최신 전체 CAD는 `GGM-FULL-ASM.step` 및 FCStd다. 외형은 470 x 729 x 930 mm로 hard envelope 안이지만 Y720 mm 선호 목표보다 9 mm 크다. 기본 프레임 470 x 700 mm 및 통합 전 `PPR-FULL-ASM` 참조를 최신 전체 배치와 혼동하지 않는다. 구동계는 GGM R2 제작 도면이 우선하며 EX-SCR-01/EX-THR-01 구동단 변경은 추가 수량이 아니다. 부품별 치수·공차·재료·공정·검사 요구사항을 해당 STEP/DXF와 함께 사용한다.

## 검증 범위

현재 기술 gate는 해석 증거의 재귀 source hash, CAD/인터페이스/공차, 제조 파일과 문서, 펌웨어 및 host runtime을 대조한다. CI-LIGHT는 현재 회귀시험과 기록 증거의 무결성, CI-FULL은 FreeCAD 회귀시험 및 실제 배포 GGM/BTS7960 HEX 재빌드를 수행한다. CI-FULL 이름만으로 전체 FEA/Modelica 신규 solve나 실물시험 수행을 주장하지 않는다.

완전 패키지의 regeneration 기록에는 실제 실행한 distribution builder와 생성 입력 commit을 보존한다. 생성된 파일을 커밋하면 HEAD가 바뀌므로 generation_base_commit과 최종 release source_commit은 의미가 다르다. 최종 ZIP은 모든 입력이 커밋된 HEAD에서 생성하고 원격 tag도 그 commit에 고정한다. 과거 ZIP이나 다른 source_commit의 검증 결과를 최신으로 표시하지 않는다.

FABRICATION verifier는 schema, 경로, exact layout, 내부/현재 원본 해시를 확인한다. 전체 compliance25항목과 inventory13항목이 통과한 상태만 패키징한다. COMPLETE verifier는 모든 파일의 크기/SHA-256, 추가·누락 파일, 경로, 물리 권한, 같은 commit의 검사 소스·로그 및 펌웨어 해시를 별도로 검사한다. `DIGITAL_TECHNICAL_CLOSURE`는 디지털 제작 후보의 검토 준비이며 물리 적합성 선언이 아니다.

## 유지하는 실물 HOLD

MVP와 최종 제품은 동일한 기계다. P1-P12 및 S0-S5를 제작과 병행하며 실패한 구획과 의존하는 후속 단계만 HOLD한다. 원시 증거를 보존하고 CAD/BOM/전기/펌웨어를 수정한 뒤 영향 검증과 같은 실물의 재시험을 수행한다. 실패 후 acceptance limit을 임의로 느슨하게 하지 않는다.

SCM440의 Q&T/질화/최종 연삭·호닝, 소재 heat 및 공정 coupon, 고온 물성 근거와 제조사 승인도면·수령검사는 미완료다. JLCCNC의 2026-09-08 회신은 현 screw/barrel 전체 공정을 충족하지 않는다. 전단핀 파단 torque, GGM 전류/토크/RPM, hot-zone 열간 fit·잔류 예압·누설, PE/interlock/차단/재시작, 측경·권취·생산량은 실제 증거가 필요하다.

SYS-04는 M4x45 class10.9 stock을 42.5 +/-0.1 mm로 가공한 dry1.50 N.m 조건이다. 실제 체결/열사이클/누설은 NOT_RUN이다. 열차단은 TF-BARREL + TF-DIE의 K0 coil 직렬 chain이며 spare1개를 합쳐 TH-FUSE-01 총3개다. F-H1..H4는 별도의 heater branch 과전류 보호다.

TH-INS-01은 사용자 보유 PI 테이프 25 mm x30 m다. 220 C는 판매자 주장 하한으로 잡은 잠정 기준이지 검증된 연속 정격이 아니다. 접착면 peak+U95<=190 C 조건과 같은 롤 S4 coupon을 요구하며 직접 heater/barrel/die wrap이나 안전장치 대체는 금지한다. 얇은 PI의 내열성만으로 단열 효과를 주장하지 않는다. Hopper PTC는 활성 설계에서 제거했고 외부 predry는 유지한다.

상세 미해결 입력은 `open_items_ko.md`, 스펙은 `product_specification_ko.md`, 제작 순서와 문서 우선순위는 `COMPLETE_HANDOFF_KO.md`, 도구 및 재현 절차는 `package_replay_ko.md`를 따른다. 일반 사용자에게 동일한 디지털 설계와 문서를 복원할 자료를 제공하되, 조달·가공·교정·실물 성능의 무조건적인 동일성은 보증하지 않는다.
