# CI 및 배포 감사 범위

v0.8의 CI-LIGHT는 현재 기술 계약, 기록 증거의 source hash, host runtime 및 부정 시험을 검사한다. 과거 v0.6.2.1 Fusion lock은 현재 설계의 평가 기준이 아니다. CI-FULL은 고정 Nix의 FreeCAD 회귀시험과 호스트 공식 Arduino CLI의 배포 HEX 재빌드다. 전체 FEA/Modelica를 새로 solve하는 workflow가 아니다.

초기 clean checkout에서 빠졌던 axial-retainer/phase-clock 및 benchmark raw 증거를 Git에 편입했다. 기록된 해석 증거의 재귀 해시는 유지하고 기준을 완화하지 않았다. local worktree에만 파일이 있어 PASS하는 경로와 과거 fixture의 잘못된 판정을 정리했다.

완전 패키지는 배포 commit의 Git blob을 원래 상대경로 그대로 포함한다. 시작 HTML과 catalog 링크, manifest, 디지털 상태와 물리 HOLD, 같은 commit의 light/CAD/firmware 로그를 독립 검증한다. 생성 단계와 최종 패키지 단계 사이의 commit은 별도로 기록한다. 생성 결과를 커밋하면 HEAD가 변하므로 내부 generation_base_commit은 실제 생성 입력을 나타내며 release source_commit과 같다고 위조하지 않는다.

GitHub 업로드는 draft에서 시작하고 모든 asset을 다시 내려받아 해시를 대조한 후 prerelease로 게시한다. 태그와 Release 상태는 GitHub API로 별도 확인한다. 메일 알림을 끄거나 오류를 continue-on-error로 숨기지 않는다.

최종 run ID와 파일 SHA-256은 패키지 verification/과 Release 자산의 SHA256SUMS를 따른다. 완전 패키지에는 연구 계보 보존을 위한 구형 소스도 존재하므로 제작 파일 선택은 COMPLETE_HANDOFF_KO.md의 우선순위를 따른다. 물리 검증은 NOT_RUN, 안전 인증은 NOT_CERTIFIED다.
