# 재현 환경

우선순위는 Nix flake, 시스템 패키지, Python virtual environment 순이다. 현재 사전 점검에서 Git, GitHub CLI, Nix, KiCad CLI와 Python 3가 발견되었고 FreeCADCmd, Typst, PlatformIO/Arduino CLI는 발견되지 않았다.

패키지는 해당 단계의 생성·검증에 실제로 필요할 때만 추가한다. 설치 전후 버전과 저장공간 영향을 `environment/CHANGELOG.md`에 기록한다.
