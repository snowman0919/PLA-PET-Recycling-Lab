# Autodesk Fusion 교차 검증 중립 패키지

- revision: `implementation-crosssolver-v0.6`
- 제어 형상: `cad/freecad/compact/geometry.py`, `manufacturing.py`
- 생성 명령: `nix develop -c freecadcmd cad/freecad/compact/generate_fusion_validation.py --source-sha <40자리 커밋 SHA>`
- 상태: `PENDING_EXTERNAL_EXECUTION`

`geometry/*.step`은 위 FreeCAD Python 형상에서 직접 생성된다. `model_manifest.csv`는 각 STEP의 SHA-256, 원본 Git SHA, source-tree hash, bounding box와 체적을 고정한다. `load_case_manifest.csv`와 `run_binding.json`은 OpenModelica envelope와 LC01–LC10을 같은 실행에 결박한다.

Fusion에서 형상을 재작성하지 않는다. STEP를 기준으로 재료, 접촉, 구속, 하중을 각 study 문서대로 설정하고 `results/fusion_result_template.csv` 및 result manifest를 반환한다. 실제 결과가 없는 행은 빈 값으로 둔다. 템플릿·예상값은 Fusion 결과가 아니다.

## 합격 경계

1. 제출 결과의 `source_git_sha`, `step_sha256`, `load_case_manifest_sha256`가 `run_binding.json`과 일치해야 한다.
2. Static stress와 thermal stress는 명시 허용치 대비 SF 2.0 이상, modal은 운전 자극 주파수에서 20% 이상 분리, buckling은 eigenvalue factor 2.0 이상을 사용한다.
3. 메쉬는 coarse/medium/fine 3단계로 하고 decision metric의 medium→fine 변화가 5% 이하여야 한다.
4. Fusion 실행이 없으면 전체 상태는 계속 `PENDING`이다. CalculiX/OpenModelica 통과를 Fusion 통과로 대체 표기하지 않는다.
