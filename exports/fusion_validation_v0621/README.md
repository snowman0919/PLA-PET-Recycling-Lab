# LC11 feeder attachment Fusion 패키지

이 디렉터리는 v0.6.2.1에서 새로 생긴 `LC11_FEEDER_ATTACHMENT`만 다룬다. 기존
`exports/fusion_validation/` 패키지와 LC02/LC04/LC05/LC07/LC08/LC10은 동결된
상태로 참조만 하며, 이 디렉터리에서 복제하거나 변경하지 않는다. 기존 필수 case의
상태는 여전히 `PENDING_EXTERNAL_EXECUTION`이다.

현재 상태는 `AWAITING_ENGINEERING_SOURCE_COMMIT`이다. dirty worktree의 현재 HEAD를
engineering source로 간주하지 않았으며, 이 상태에서는 Fusion 실행 결과를 release
증거로 접수할 수 없다. 구현 source commit이 생성된 뒤 다음 명령으로 결박한다.

```bash
python3 exports/fusion_validation_v0621/scripts/finalize_engineering_binding.py \
  --repo-root . --engineering-source-sha <40자리-구현-source-commit-SHA>
python3 fusion_worker/result_validation/validate_fusion_v0621_package.py \
  exports/fusion_validation_v0621
```

결박 스크립트는 지정 commit의 PF-04/PF-05 STEP, process feed assembly STEP 및 원본
manifest 바이트가 이 패키지와 정확히 같은지 Git object에서 검증한다. 일치하지 않으면
아무 파일도 쓰지 않고 실패한다.

## 해석 범위

- PF-05 하우징/플랜지의 국부 구조 스크리닝이 주 해석이다.
- PF-04는 2.2 N·m 정상/정지 반력의 원천 형상과 축을 고정하는 참조 body이다.
- PF-05 하단 플랜지의 실제 볼트 구멍·브래킷 형상은 아직 CAD에 없으므로 annular face
  fixed constraint를 사용한다. 따라서 결과는 하우징 자체와 이상화된 플랜지의 screen일
  뿐, 볼트/브래킷/알루미늄 프로파일/테이블 load path의 실제 검증이 아니다.
- 5.4 N은 0.55 kg의 bounded feed inventory를 `0.55 × 9.80665`에서 반올림한 하향
  하중이다. 2.2 N·m는 feeder actuator의 최대 반력 envelope이다.
- 본 결과는 시뮬레이션이며 실제 체결 토크, 베어링/부싱, 진동, jam 및 물리 proof test를
  대체하지 않는다.

## 실행 순서

1. `geometry/PF-05.step`과 `geometry/PF-04.step`을 같은 component에 삽입한다.
2. `coordinate_system.md`의 +3 mm 상대 배치를 적용해 assembly STEP과 대조한다.
3. PF-04는 reference/suppressed body로 유지하고 PF-05만 structural mesh에 포함한다.
4. `materials.csv`, `constraints.csv`, `contact_pairs.csv`, `loads/LC11.json`을 그대로 적용한다.
5. `mesh_plan.csv`의 coarse→medium→fine 세 study를 독립 실행한다.
6. `results/fusion_result_template.csv` 형식으로 결과와 원본 evidence hash를 기록한다.

합격 screen은 medium→fine 최대 변위 변화 ≤5%, force/moment reaction imbalance 각각
≤2%, 그리고 AISI 304 허용응력 107.5 MPa 기준 safety factor ≥2.0이다. 고정 경계 바로
인접한 singular peak는 별도 태그하고, 경계로부터 두 local fine element 이상 떨어진
구간의 linearized/equivalent stress를 판정값으로 사용한다.
