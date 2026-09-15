# PR 실패 알림의 원인과 push 전 검사

## 확인한 상태

2026-09-15 재개 시 HEAD는 649d0194였다. Gmail의 최근 PPR 실패 알림은 24208c7f 실행34858627442를 가리킨다. 해당 로그는 `current firmware evidence mismatch`로 실패했으며, 그 결과 P0와 종속 현장 시험도 실패했다. 새 소스와 exports/final/drive_ggm_v08/firmware 사본 및 manifest가 같은 커밋에 들어 있지 않았던 문제다.

649d0194에 배포 사본을 반영한 PR 실행34861143561은 실제 SUCCESS다. 이번 세션 이전에 존재하던 수정이며 새로 작성한 것으로 보고하지 않는다. 메일을 삭제·보관하거나 알림 설정을 변경하지 않는다.

## 재발 방지

`.githooks/pre-push`는 Git이 stdin으로 전달한 실제 outgoing commit마다 `validation/verify_git_snapshot.py --revision <SHA> --suite light`를 실행한다. 기존 작업 폴더의 미커밋 생성물로 성공을 보충하지 않는다. 커밋된 Git blob만 분리해 검사하고 하나라도 실패하면 원격 전송 전에 종료한다. 여러 ref가 같은 커밋이면 한 번만 검사하며 ref 삭제에는 검사를 실행하지 않는다.

로컬 설치는 기존 `.git/hooks/pre-push`가 없을 때에만 `.githooks/pre-push`를 가리키는 symlink를 추가한다. 기존 post-commit/graphify hooks, 전역 설정과 GitHub 필수 검사는 변경하지 않는다. 다른 checkout에는 hook이 자동 설치되지 않는다. 직접 실행 경로는 다음과 같다.

```sh
nix develop --command python3 validation/verify_git_snapshot.py --revision HEAD --suite light
```

`test_pre_push.py`는 outgoing SHA 선택, 실패 차단, 삭제, 중복, 잘못된 입력, 여러 커밋 검사를 확인한다. 이 사전검사는 Genuine CI/플랫폼 장애나 main 변경에 따른 merge 결과의 실패까지 없애는 보장은 아니다. 원격 검사의 기준을 완화하지 않는다.

문서/AST 그래프의 무비용 증분은 수행하지만 문서 의미 그래프 전역 검증이나 기계 안전 검증으로 확대하지 않는다.
