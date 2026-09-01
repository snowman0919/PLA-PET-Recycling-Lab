# Headless Windows Fusion worker handoff

이 폴더는 Windows worker가 중립 패키지를 검증하고 Autodesk Fusion UI/API 실행을 재현하기 위한 계약이다. Autodesk Fusion은 이 Linux 저장소에 설치되어 있지 않으므로 여기서는 외부 실행을 주장하지 않는다.

1. 결박된 패키지를 포함하고 engineering source commit을 ancestor로 갖는 checkout을 준비한다.
2. `scripts/prepare_run.py --dry-run`으로 source Git object, STEP, model/load manifest hash와 실행 허용 상태를 검증한다.
3. 같은 도구로 `PENDING` hash-bound run manifest를 만든다. 이 도구는 solver 값이나 PASS를 만들지 않는다.
4. `cua_playbooks/fusion_execution.md` 순서로 STEP import와 study를 구성한다.
5. 결과 CSV와 증거 파일을 `result_validation/validate_fusion_results.py`로 검사한다.

현재 HEAD 문자열을 engineering source SHA와 같게 만드는 방식은 LC11에서 사용할 수 없다.
LC11 결박 metadata가 engineering source commit 뒤의 별도 commit에 있기 때문이다. 준비 도구는
대신 source commit의 존재와 ancestor 관계를 확인하고, 해당 Git object의 STEP 바이트를 현재
패키지 및 manifest hash와 직접 비교한다.

```powershell
py -3 fusion_worker/scripts/prepare_run.py `
  --package-root exports/fusion_validation `
  --case-id LC02 --study-type static_stress `
  --solver-version 2704.1.53 --dry-run

py -3 fusion_worker/scripts/prepare_run.py `
  --package-root exports/fusion_validation_v0621 `
  --case-id LC11_FEEDER_ATTACHMENT --study-type linear_static `
  --solver-version 2704.1.53
```

LC08+LC06 조합은 LC08 `thermal_stress` manifest에
`--related-case-id LC06`을 추가한다. `environment_check.ps1`와
`New-RunManifest.ps1`은 동결 legacy 절차 보존용이며 LC11 실행에는 사용하지 않는다.

Windows worker에 interactive login/cloud solve 승인이 필요하면 중지하고 사용자에게 요청한다. 이 handoff는 구매·cloud 비용 승인을 포함하지 않는다.
