# Headless Windows Fusion worker handoff

이 폴더는 Windows worker가 중립 패키지를 검증하고 Autodesk Fusion UI/API 실행을 재현하기 위한 계약이다. Autodesk Fusion은 이 Linux 저장소에 설치되어 있지 않으므로 여기서는 외부 실행을 주장하지 않는다.

1. 저장소를 exact source SHA로 checkout한다.
2. PowerShell에서 `./environment_check.ps1 -PackageRoot ../exports/fusion_validation`을 실행한다.
3. `cua_playbooks/fusion_execution.md` 순서로 STEP import와 study를 구성한다.
4. `scripts/New-RunManifest.ps1`로 hash-bound run manifest를 만든다.
5. 결과 CSV와 증거 파일을 `result_validation/validate_fusion_results.py`로 검사한다.

Windows worker에 interactive login/cloud solve 승인이 필요하면 중지하고 사용자에게 요청한다. 이 handoff는 구매·cloud 비용 승인을 포함하지 않는다.
