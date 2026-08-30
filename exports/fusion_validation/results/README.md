# Fusion 결과 반환 위치

현재 실제 Fusion 결과는 없다. `fusion_result_template.csv`를 채우고 원본 report/CSV/image를 함께 두며, `fusion_result_manifest.json`의 `runs`에 파일 SHA-256을 추가한다. 세 binding hash가 일치하지 않거나 빈 값/NaN/단위 누락이 있으면 검증기는 거부한다. `PENDING` 파일을 PASS로 편집하지 말고 검증 스크립트를 사용한다.
