# 교차 solver 가정 계약

- OpenModelica: 제어·열·압력·구동·필라멘트·spool 동역학의 reduced-order model. 실제 재료 시험이 아니다.
- CalculiX: S275 bearing plate C3D8와 S45C cutter shaft B31의 선형 탄성 global screen. coarse/medium/fine 실제 mesh 실행.
- Fusion: 동일 FreeCAD STEP와 OpenModelica LC01–LC10을 독립 3D 해석하는 외부 검증자. 이 환경에서는 실행되지 않았다.
- 공통: source Git SHA, STEP SHA-256, load manifest SHA-256가 일치해야 correlation에 포함한다.
- 허용차: global displacement 15% 이내, reaction/load balance 5% 이내, stress는 동일 probe/averaging 정의에서 20% 이내. 두 solver가 모두 독립 합격 기준을 통과하는 것이 우선이다.

고정 경계의 peak stress, bonded contact edge, thermal contact conductance는 모델 의존성이 크므로 단일 숫자 상관을 강제하지 않고 sensitivity 범위를 병기한다. 실제 Fusion 결과가 없으면 correlation 상태는 `PENDING`이다.
