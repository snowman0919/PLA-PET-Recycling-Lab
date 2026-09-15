# 열제어 연동 변경의 커밋·배포 사본 검사

열모델/제어 수정의 source commit은 74929bcbc9e52f06cdc3cf7542f4377c89e45624다. 생성된 펌웨어와 검사 기록은 후속 커밋에 함께 보존한다. 아직 원격 검사가 실행되기 전 작성한 이 문서만으로 GitHub Actions 성공을 주장하지 않는다.

## 재생성 결과

`release/build_electrical_firmware_release.py`를 고정 Nix 환경에서 실행했다. 출력은 GGM_FIRMWARE_SOURCE_READY42 및 V08_ELECTRICAL_FIRMWARE_RELEASE_OK다. 독립 원본/배포 사본 clean rebuild의 HEX가 일치했다.

- 대상: arduino:avr:mega, core1.8.8, Arduino CLI1.5.1.
- Flash: 62,582 bytes. SRAM: 4,779 bytes.
- HEX SHA-256: 9e1f0b0f69aa2759948349f4b40e0e2ac1f4cc74eec2b31dbfcf2d349fc5db22.
- heater_control.cpp 세 사본의 SHA-256: 92c8b20af74fb12eb6e9825de593b4d5551c2c63310ebd2d2fcaf68f08b88bed.

세 사본은 firmware/arduino_mega 원본, exports/final/firmware/source 배포 소스, exports/final/drive_ggm_v08/firmware GGM 변형이다. 세 번째 사본과 그 manifest를 누락하면 로컬 dirty tree 검사가 통과해도 PR에서 실패한다.

## 실제 로컬 검사

로컬 CI-LIGHT는 68개 실행 항목/64개 시험 모듈 PASS였다. 이 수치는 원격 GitHub 실행 수치가 아니다. pre-push는 outgoing SHA를 git archive로 분리하고 실제 커밋된 바이트만으로 같은 light 검사를 수행한다. 검사 실패 시 push를 보류하며 hook을 비활성화하지 않는다.

검사 로그는 checks/controller-ci-light.txt와 checks/controller-firmware-regeneration.txt에 보존한다. Graphify AST 갱신 실행 로그는 checks/controller-graph-update.txt다. 기존 controller_plant_verification.json의 graph_update=PENDING 필드는 이번 실행 로그를 반영하지 않은 상태이며, 문서 의미 그래프 전체 갱신 완료를 뜻하지 않는다.

물리 시험/보드 업로드/통전은 수행하지 않았다. 열손실 큰 조건의 전력 부족과 히터 외피온도 검토, 후방 지지 접촉하중, 뚜껑/인터록/센서 상세는 별도 디지털 HOLD로 남는다. 기존 공개 rc1과 과거 COMPLETE ZIP은 이번 새 펌웨어로 바뀌지 않는다.

## 사전검사에서 실제 차단한 누락

3af1bb04의 첫 push는 로컬 pre-push가 차단했다. 패키지 목록에 남아 있던 이전 미추적 초안 CONTROLLER_COUPLING_KO.md가 커밋된 소스 사본에는 없었다. 원격 HEAD는 a2747cdf에 그대로 머물렀고, 이 실패는 GitHub Actions를 실행시키지 않았다.

초안 파일을 지우거나 검사에서 누락을 허용하지 않는다. 검토 완료된 CONTROLLER_PLANT_REPLAY_KO.md를 패키지 기준으로 유지하고, 미채택 초안의 목록 항목만 제거한다. controller_plant_verification.json은 첫 source commit74929bcb에서 관찰한 범위의 기록이며 이후 패키지 목록 수정의 최신 해시를 주장하지 않는다. 새 모델 결과의 source_sha256과 실제 outgoing commit 격리 검사는 별도로 재확인한다.
