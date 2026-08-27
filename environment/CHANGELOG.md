# 환경 변경 이력

## 2026-08-28 — 사전 점검

- Action: 읽기 전용 환경 및 저장공간 검사
- Reason: Phase 0 preflight
- Commands: `df -h .`, `du -sh .`, 실행 파일 탐색
- Paths affected: 없음
- Disk before: root filesystem 901 GiB 중 762 GiB 사용, 130 GiB 가용, 작업 디렉터리 12 KiB
- Disk after: 동일
- Space reclaimed: 0
- Risk/impact: 없음
- Found: git, gh, nix, kicad-cli, python3
- Missing from PATH: FreeCADCmd, Typst, PlatformIO, Arduino CLI
- Note: cache 삭제나 Nix garbage collection을 수행하지 않음

## 2026-08-28 — local subagent preflight

- `KOTORI_SUBAGENT_API_KEY`: 존재만 확인, 값 미출력
- endpoint: `.env` 값을 HTTPS URL로 메모리 내 정규화해야 함
- models: `dgx-moa-fast`, `dgx-moa`
- non-stream Responses semantic test: 통과
- harmless function-call probe: 통과
- 실무 prompt: fast 모델이 120초와 60초 timeout으로 결과를 반환하지 않아 미채택

## 2026-08-28 — Nix FreeCAD 환경 구성

- Action: `flake.lock` 생성 후 Nix 개발환경에서 FreeCAD 1.1.3, Typst, Python, Git LFS closure 준비
- Reason: parametric CAD를 FCStd/STEP/STL로 실제 headless 재생성
- Commands: `nix flake lock`, `nix develop --command FreeCADCmd --version`
- Paths affected: Nix store와 Git flake lock
- Re-downloadable: 예
- Disk before: 138,593,415,168 bytes available
- Disk after: 131,936,075,776 bytes available
- Space reclaimed: 0
- Space consumed: 6,657,339,392 bytes (약 6.20 GiB)
- Risk/impact: Nix store 사용량 증가; source/user data 삭제 없음
- Result: FreeCAD 1.1.3 확인, baseline CAD export 성공
- Rendering note: EGL/OSMesa 미지원으로 첫 OpenGL offscreen 시도가 실패하여 결과를 폐기하고 software projection으로 교체

## 2026-08-28 — subagent 실무 재시도

- `dgx-moa-fast`: 축소한 요구사항 prompt도 60초 동안 무응답, 미채택
- `dgx-moa`: Stage 1 shaft 독립 검토 prompt가 90초 동안 무응답, 미채택
- API key와 raw request header는 저장·출력하지 않음
- 영향: subagent 검증 완료로 표기하지 않고 parent 계산과 자동 검사만 증거로 유지

## 2026-08-28 — subagent 축소 검토 성공 및 일반 모델 timeout

- `dgx-moa-fast`: Stage 1 phase sweep 검사 항목과 cutter 형상 제조성 검토 응답 수신
- 채택 범위: 1° counter-rotation, hook-root/axial gap 검사와 작은 tip land를 parent 계산·CAD 검사 후 반영
- `dgx-moa`: 17 mm 대 20 mm shaft/bearing 독립 검토가 60초 timeout으로 결과를 반환하지 않아 미채택
- API key, endpoint credential과 raw header는 저장·출력하지 않음
- 최종 설계 판단은 parent 해석, FreeCAD solid 검사와 기록된 가정에 기반함
- 후속 fast 감사 재호출은 HTTP 403으로 거절되어 응답을 미채택; 비밀값은 출력하지 않음

## 2026-08-28 — Stage 2 통합 생성 결함 수정

- 첫 `generate_all.py` 실행에서 Stage 1/2의 동일한 short module 이름 `geometry`가 `sys.modules` cache에서 충돌
- 개별 generator 산출물은 유효했지만 전체 재생성은 ImportError로 실패하여 해당 통합 실행을 미채택
- 각 stage generator 전 `geometry` cache entry를 제거하도록 runner를 수정
- 후속 tolerance coupon → Stage 1 → Stage 2 → full assembly 전체 생성과 CAD/kinematic 검증 통과
