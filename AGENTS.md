# PPR AGENTS.md — 진입점 (entrypoint)

**목표와 영구 규칙은 [`KODEX.md`](KODEX.md) 를 따른다.** 이 문서는 저장소 고유 운영 메모만 남긴다.

## 운영 메모
- **Worktree 위생**: 작업은 clean worktree(예: `PPR-c2.1-codex-20260921`)에서. 원본 dirty worktree
  `/home/monad/develop/PPR` 와 보존 브랜치는 절대 변경 금지 (KODEX §5).
- **현재 상태**: 모든 물리 해제(구매/가공/통전)는 **HOLD**. 디지털 증거만 존재한다. 상세 현재 상태는
  [`STATUS.md`](STATUS.md) 참조.
- **C1 root 자산은 frozen reference**: 루트 `src/`, `results/`, `design/assembly.json` 등 C1 결과는
  참조 전용이며 C2 확정값이 아니다. C1 검증/해시/pre-push 게이트를 지우거나 우회하지 않는다.
- 검증 게이트: `tests/`, `c2/tests`, `c2.1/tests`, `c2.3/tests` unittest + 각 `verify_artifacts.py`.
  CI의 실패 원인은 STATUS.md "알려진 결함" 참조.
- 결과/미종결 항목은 한국어로 보고한다. 코드 MIT / 하드웨어 LICENSE-HARDWARE 유지.
