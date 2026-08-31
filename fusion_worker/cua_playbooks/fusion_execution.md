# Fusion 실행 playbook

1. 해당 case의 `prepare_run.py --dry-run` PASS를 확인한다. source commit과 현재 checkout은
   같을 필요가 없지만 source commit이 현재 HEAD의 ancestor여야 하며, STEP Git object와
   package/model/load manifest hash가 모두 일치해야 한다.
2. 새 design에 해당 LC의 STEP만 import하고 단위를 mm로 확인한다. bounding box를 `model_manifest.csv`와 비교한다.
3. study 문서에 따라 material/contact/constraint/load를 이름으로 설정한다. UI selection screenshot을 증거로 남긴다.
4. coarse/medium/fine mesh에서 같은 metric probe를 사용한다. medium→fine 변화율을 기록한다.
5. report/CSV/screenshot을 export하고 각각 SHA-256를 기록한다.
6. `prepare_run.py`가 만든 manifest를 사용한다. result CSV를 채우고 run manifest를
   `PASS` 또는 `FAIL`로 완료한다. solve 미실행은 `PENDING`, login/license/cloud 승인은
   `BLOCKED_EXTERNAL`이다. LC08 pressure-coupled thermal stress는
   `--related-case-id LC06` 결박이 있는 manifest만 사용한다.
7. validation script가 통과한 결과만 parent에게 반환한다.

CUA는 로그인·cloud solve 비용 동의·외부 공유를 자동 승인하지 않는다. UI가 예상과 다르면 screenshot과 함께 중지한다.
