# CI-FULL: CAD 회귀시험과 배포 펌웨어 재현

현재 workflow는 `.github/workflows/ci-full.yml`이다. CI-LIGHT와 동일한 commit을 지정해 실행한다. 이 작업은 전체 물리 해석의 신규 solve나 실물 안전시험이 아니다.

## 실행 환경 분리

FreeCAD 회귀시험은 `flake.lock`에 고정된 Nix 환경에서 수행한다. AVR 재빌드는 호스트의 공식 Arduino CLI 1.5.1로 수행한다. Nix Arduino FHS wrapper의 `bwrap: setting up uid map: Permission denied`를 피하기 위해 호스트 보안 설정을 해제하지 않는다.

- Runner: Ubuntu 24.04.
- Arduino CLI: 공식 setup action의 고정 commit과 버전 1.5.1.
- Board: `arduino:avr:mega`; core: `arduino:avr@1.8.8`.
- Compiler: 배포 manifest의 `avr-g++ (GCC) 7.3.0`과 정확히 대조한다.
- Arduino data/download/user 및 build 임시 파일은 `.build/ci-v08/firmware/` 안에 둔다.

CLI 배너의 distributor별 Commit/Date 차이는 실제 버전 변경과 구분한다. 버전 문자열의 prerelease/custom suffix는 제거하지 않는다. 관측 배너와 기존 manifest 배너를 모두 로그에 보존한다. 최종 HEX는 기존 배포 파일 및 manifest SHA-256과 바이트 단위로 일치해야 한다. 비교 기준 HEX를 재빌드 결과로 덮어쓰지 않는다.

## 실행과 확인

```sh
gh workflow run ci-full.yml --repo snowman0919/PLA-PET-Recycling-Lab --ref final-design-fabrication-closure-v0.8
gh run list --repo snowman0919/PLA-PET-Recycling-Lab --workflow ci-full.yml --limit 5
```

해당 run의 headSha와 검토 commit 일치를 먼저 확인한다. 모든 실제 검사 step이 success이고, 업로드된 CAD result.json의 각 returncode가 0이며, AVR rebuild.log에 `RELEASED_HEX_REPRODUCIBLE_OK`와 기대 SHA-256이 있어야 한다. workflow 이름만으로 전체 제품 검증 완료를 주장하지 않는다.

물리 검증 `NOT_RUN`, 안전인증 `NOT_CERTIFIED`, 구매/가공/통전 승인은 별도로 유지한다. 이 workflow는 장치 업로드, 모터 구동, 히터 가열, GitHub Release 게시를 수행하지 않는다.
