# 배포 파일 재현과 검증

## 1. 조회와 파일 무결성

COMPLETE ZIP을 새 폴더에 압축 해제한다. `START_HERE.html`은 인터넷 없이 열 수 있다. 최상위에서 `python3 verify_package.py .`를 실행하여 포함 파일, 상대경로, 크기와 SHA-256을 검사한다. 외부 `SHA256SUMS`의 ZIP 해시와 Release의 태그/커밋도 확인한다. 이미 검사된 폴더에서 재생성하면 원래 파일이 바뀔 수 있으므로 원본과 작업용 복사본을 분리한다.

## 2. 실행 환경과 소스

모든 Git 기반 release 생성·실물 stage 기록은 `git clone --branch v1.0.0-rc1 https://github.com/snowman0919/PLA-PET-Recycling-Lab.git`로 만든 체크아웃에서 실행한다. COMPLETE의 `repository/`는 같은 소스의 오프라인 복사본이며 `SOURCE_SNAPSHOT.json`에 원본 커밋을 보존한다. 파일 검증과 P0는 이 스냅샷에서도 동작하지만 스냅샷 표식만으로 실제 Git 원격 게시·실물 시험 승인까지 증명하지 않는다.

경량 검사는 Python 3.12, `python3 -m pip install -r environment/ci-requirements.txt`, g++, poppler-utils를 사용한다. `python3 validation/ci_v08.py --suite light`가 현재 기술 gate, firmware host runtime, P-stage와 packaging 회귀시험을 실행한다. `.build/ci-v08/light/result.json`에 모든 명령, 종료코드, 소스/로그 해시를 남긴다. 이전 실행 JSON을 fresh PASS로 재사용하지 않는다.

FreeCAD 검사는 `nix develop --command python3 validation/ci_v08.py --suite cad`다. 이는 고정 FreeCAD 환경의 형상 회귀시험 및 GGM native/STEP 비교이며 모든 FEA/열/피로 해석을 새로 실행했다는 뜻이 아니다. 전체 해석 재실행은 개별 해석 스크립트와 source binding의 의존 순서를 따라 별도 시행해야 한다.

## 3. 펌웨어 독립 재빌드

공식 Arduino CLI 1.5.1, `arduino:avr@1.8.8`, manifest의 AVR-GCC 7.3.0을 사용한다. `arduino-cli core update-index`, `arduino-cli core install arduino:avr@1.8.8`, `python3 exports/final/firmware/reproducible_build/build_and_verify.py` 순서로 실행한다. 첫 설치에는 네트워크가 필요하다. CLI/core/compiler와 library lock을 대조하고 실제 clean compile HEX가 배포 HEX와 바이트 단위로 일치해야 PASS다. 장치에 업로드하거나 모터/히터를 켜지 않는다.

CI-FULL은 Ubuntu 24.04에서 CAD만 고정 Nix 환경으로 실행하고 AVR은 공식 호스트 CLI를 사용한다. Nix Arduino FHS wrapper의 bwrap 권한 오류를 피해 호스트 보안 제한을 해제하지 않는다. `docs/final/ci_full_replay_ko.md`를 따른다. FCStd는 geometry snapshot이며 파라메트릭 생성 코드는 별도로 제공한다.

## 4. 설계 재생성

변경 작업은 태그의 별도 작업 복사본에서 한다. 배포 산출물의 순차 재생성은 `nix develop --command python3 release/regenerate_release.py`로 실행한다. `.build/release-regeneration/result.json`에 명령·실제 로그·생성 입력 commit을 기록한다. 이 명령은 기록된 FEA/Modelica를 새로 solve하지 않으며 변경된 해석 입력은 별도 재검증해야 한다. 고정 Nix 환경에서 기본 형상/STEP은 `cad/freecad/final_v08/generate.py`, GGM source capture는 `cad/freecad/drive_v08/cache_source.py`, GGM 통합 STEP/native 생성은 `cad/freecad/drive_v08/run_generate.py` 순서로 FreeCADCmd에서 실행한다. 각 단계의 종료코드뿐 아니라 SOURCE_CAPTURE_COMPLETE / GENERATED 및 reimport/hash 결과를 확인한다. `analysis/drive_integration_v08/rebuild.py`의 과거 특정 Nix 경로는 일반 머신의 명령으로 그대로 사용하지 않는다.

부품 출력은 `release/build_mechanical_release.py`(FreeCAD + Typst), `build_print_release.py`, `build_ggm_drive_release.py`; BOM과 설명서는 `build_bom_release.py`, `build_final_documents.py`; 전기/펌웨어는 `build_electrical_firmware_release.py`가 담당한다. 생성된 입력이 바뀌면 관련 solver/공차/evidence의 source hash가 stale해질 수 있다. 해당 producer를 다시 실행하고 판정 결과를 검토한 뒤 coherent input commit을 만든다. 파일 해시만 수동 변경해서 재생성한 것처럼 처리하지 않는다.

## 5. 배포 생성

모든 채택 입력을 커밋·push한 뒤 현재 HEAD에서 경량/CAD/펌웨어 검사를 실행한다. `python3 validation/v08_full_compliance.py`, `python3 validation/v08_release_inventory.py`의 패키지 이외 gate가 통과해야 `python3 release/build_fabrication_release.py`를 실행할 수 있다. `python3 release/verify_fabrication_release.py` 뒤 compliance/inventory를 재실행한다. 순환을 피하기 위해 prepackage 검사에서 패키지 gate만 아직 미완료일 수 있고, 최종 배포에서는 예외 없이 통과해야 한다.

완전 패키지는 `python3 release/build_complete_release.py --evidence <현재 HEAD의 CI 결과 폴더>`로 만든다. 생성기는 Git HEAD의 tracked blob만 취하고, 현재 HEAD의 실제 검증 증거와 모든 catalog 링크를 검사한다. ZIP은 커밋하지 않고 해당 commit을 가리키는 tag의 Release asset으로 게시한다. 물리 상태를 NOT_RUN에서 바꾸거나 미해결 조달·통전 권한을 확대하지 않는다.
