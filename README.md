# PPR - PLA/PET Recycling Lab

**현재 제품 기준: `final-design-fabrication-closure-v0.8` / 배포 태그: `v1.0.0-rc1`.**
디지털 제작 후보이며 물리 검증 NOT_RUN, 안전 인증 NOT_CERTIFIED다. MVP와 최종 제품은 같은 기계다. 공개 prerelease 게시 승인은 실제 구매·가공·통전 승인과 별개다.

## 전체 결과 확인

[전체 인수인계](docs/final/COMPLETE_HANDOFF_KO.md), [제품 스펙시트](docs/final/product_specification_ko.md), [미해결 입력](docs/final/open_items_ko.md), [재현 방법](docs/final/package_replay_ko.md)을 먼저 읽는다. GitHub Release의 COMPLETE 패키지를 받으면 `START_HERE.html`에서 오프라인으로 전체 결과와 파일을 탐색할 수 있다.

## 어떤 모델을 사용해야 하는가

최신 전체 모델은 [`GGM-FULL-ASM.step`](exports/final/drive_ggm_v08/GGM-FULL-ASM.step)과 [동일한 FreeCAD 파일](exports/final/drive_ggm_v08/GGM-FULL-ASM.FCStd)이다. 전체 외형은 **470 x 729 x 930 mm**, 기본 프레임 평면은 470 x 700 mm다. GGM R2 구동계 도면과 canonical EX-SCR/EX-THR 변경을 함께 사용한다. 과거 `PPR-FULL-ASM` 기본 모델과 GMP60/DRV-02 예시는 최신 전체 배치가 아니다.

## 문서와 제작 자료

[최종 BOM](exports/final/bom/BOM.xlsx), [체결 schedule](exports/final/bom/fastener_schedule.csv), [인터페이스·공차](exports/final/interface_catalog.csv), [금속 RFQ 목록](exports/final/manufacturing/RFQ/manifest.csv), [GGM R2 도면](exports/final/manufacturing/drive_ggm/PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf), [출력품 manifest](exports/final/print/print_manifest.csv), [조립 설명서](docs/final/complete_build_manual_ko.pdf)를 제공한다. 도면/manifest별 HOLD와 수령 조건을 유지한다.

## 제작과 검증

공용 분쇄기 -> 외부 사전 건조 -> sealed feeder -> 16 mm single screw/barrel -> die -> 냉각 -> X/Y 측경 -> puller -> dancer/traverse/spool의 단일 경로다. [P0-P12 실행 인덱스](validation/physical_v08/PHYSICAL_EXECUTION_INDEX_KO.md)와 S0-S5 smoke를 제작 과정에 병행한다. 실패한 구획과 후속 단계는 HOLD하고 설계를 수정한 뒤 같은 실물로 재시험한다. 200 g/h와 1 kg 권취는 아직 실측 보증이 아니다.

## 디지털 검증

Python 3.12와 `environment/ci-requirements.txt`, g++, poppler가 준비된 환경에서 `python3 validation/ci_v08.py --suite light`를 실행한다. FreeCAD 시험은 `nix develop --command python3 validation/ci_v08.py --suite cad`로 별도 실행한다. 정확한 AVR clean rebuild와 전체 실행 절차는 재현 문서를 따른다. CI는 현재 기술 gate와 회귀시험을 검사하며 과거 v0.6.2.1 Fusion 해시를 현재 제품에 강제하지 않는다.

## 계보와 라이선스

구형 v0.6/Fusion/experiment 자료는 변경 계보와 연구 참고로 남아 있다. 과거 README는 Git history에서 확인한다. 현재 인수인계 파일의 우선순위는 COMPLETE_HANDOFF_KO.md에 명시한다. 소프트웨어는 [LICENSE](LICENSE), 하드웨어 설계는 [LICENSE-HARDWARE](LICENSE-HARDWARE)를 따른다. 제조사 자료와 구매품은 해당 권리·조건을 별도로 따른다.
