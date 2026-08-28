# 환경 변경 이력

## 2026-08-28 — Gmsh/CalculiX 재현 환경

- Action: Nix 개발환경에 Gmsh 4.15.2와 CalculiX 2.23을 추가하고 실제 Stage 1 cutter STEP의 coarse/fine C3D4 해석을 실행했다.
- Reason: 이상화 beam/tooth 손계산에서 빠진 실제 치근·키홈 형상을 3D 선형 정적으로 스크리닝하기 위함.
- Commands: `nix develop --command python3 simulation/structural/stage1_cutter_3d_fea.py`.
- Paths affected: 재다운로드 가능한 `/nix/store` gmsh/CalculiX closure와 실행 중 자동 삭제되는 `/tmp/ppr-stage1-fea-*`; repository에는 source, JSON과 문서만 저장.
- Disk before: 122,751,750,144 bytes available.
- Disk after: 122,576,220,160 bytes available(다른 동시 작업 및 Nix store 공유 효과를 포함한 filesystem 관측값).
- Package fetch indication: 3.7 MiB download, 10.8 MiB unpacked(ccx/arpack/spooles); Gmsh closure는 현재 Nix store에 이미 존재했다.
- Space reclaimed: 0; garbage collection 또는 사용자 cache 삭제 없음.
- Risk/impact: system profile은 변경하지 않았다. 본 결과는 contact/impact/fatigue/physical validation이 아니다.

## 2026-08-28 — KiCad PCB authoring 및 SPICE 임시 환경

- Action: `/tmp/ppr-kiutils-venv`에 `kiutils==1.4.8`을 설치해 deterministic KiCad source를 생성하고, Nix 임시 shell에서 ngspice 45를 받아 9개 subcircuit를 실행했다.
- Reason: 최소 감시/기본-OFF 인터페이스 보드를 네이티브 KiCad 9로 작성하고 ERC/DRC/SPICE/EMC 증거를 남기기 위함.
- Commands: `/tmp/ppr-kiutils-venv/bin/python .../generate.py`, `kicad-cli sch erc`, `kicad-cli pcb drc`, `nix shell nixpkgs#ngspice --command ...`.
- Paths affected: 재다운로드 가능한 `/tmp` venv와 `/nix/store` ngspice closure; repository에는 source와 검증 산출물만 저장.
- Disk before/after: 별도 전체 filesystem snapshot 미수집; board tree 약 4.7 MiB, ngspice closure 11.4 MiB unpacked 안내.
- Space reclaimed: 0; garbage collection 또는 사용자 cache 삭제 없음.
- Risk/impact: system package/profile은 변경하지 않았다. `fill_zones.py`는 KiCad 9.0.9의 `/usr/bin/python3` pcbnew binding을 요구한다.

## 2026-08-28 — CUDA compiler/runtime for RTX 3080 validation

- Action: Nix에서 `cuda_nvcc 12.9.86`, `cuda_cudart 12.9.79`와 build dependencies를 단일 `--impure`/`NIXPKGS_ALLOW_UNFREE=1` 호출로 가져와 CUDA C++ kernel을 컴파일했다.
- Reason: GPU 이름만 기록하지 않고 2‑tower stability uncertainty sweep이 실제 RTX 3080에서 실행됐음을 검증하기 위함.
- Commands: `nix shell ... cuda_nvcc ... nvcc`, 임시 `/tmp/ppr-cuda-driver-libs` host-driver symlink, `run_two_tower_stability.py --samples 4194304`.
- Paths affected: 재다운로드 가능한 `/nix/store` CUDA/compiler dependency와 `/tmp` executable/symlink만 생성. Repository에는 source와 결과 JSON만 저장.
- Disk before: 약 118 GiB available.
- Disk after: 약 117 GiB available.
- Space consumed: filesystem 표시 기준 약 1 GiB; `cuda_nvcc` closure path 949.2 MiB, `cuda_cudart` 68.7 MiB. Garbage collection은 수행하지 않았다.
- Risk/impact: CUDA EULA package를 영구 system 설정에 추가하지 않았다. Host NVIDIA driver 595.84/CUDA API 13.2와 Nix runtime 사이 library search는 임시 symlink로만 연결했다.

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

## 2026-08-28 — 2-tower 계약 변경 후 RTX 3080 재실행

- Action: 기존 CUDA binary로 4,194,304-sample stability kernel과 8,192-sample CPU 교차검산 재실행
- Reason: CAD baseline을 계산 계약의 단일 source of truth로 연결하면서 contract SHA-256가 변경됨
- Result: RTX 3080 compute 8.6, kernel 0.929 ms, CPU/GPU 최대차 3.41e-13 N, p99 anchor-pair tension 509.3 N, 2 kN 후보 초과확률 0
- Scope: virtual simulation evidence이며 substrate pullout 또는 물리 전도시험이 아님

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

## 2026-08-28 — 현재 revision clean-clone 재현

- Nix FreeCAD 1.1.3과 Typst 0.15.1로 CAD→표준/review render→PDF→26-gate 전체 재실행 통과
- STEP/STL/DXF/PNG/PDF/계산 JSON/review JSON 변경 0건
- FCStd 51개는 생성시각·UUID·내부 ID 때문에 container hash가 달라지며 shape/object-set gate로 검증
- Docker Typst 0.13.1 임시 PDF는 폐기하고 Nix Typst 0.15.1 고정 CreationDate 산출물로 교체
