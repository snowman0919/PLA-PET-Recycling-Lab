# P4 두-cutter coupon 물리 검증

P4의 목적은 full 12-disc stack 발주 전에 CUT-01 형상, screen, phase pair, GGM 구동/복구가 실제 PLA/PET에서 유효한지 확인하는 것이다. P3 GGM bench는 단순 PASS 문자열이 아니라 `validate_p3_stage_release.py`가 `P3_STAGE_RELEASE_VALIDATED`로 재검증한 release artifact여야 한다. 이 artifact도 P4 통전을 승인하지 않는다.

## 시험 구성

CUT-01은 축당 1장, 총 2장만 사용한다. CUT-03/CUT-05/CUT-05R/CUT-04/CUT-08/09/10, 61905 bearing, phase gear pair와 현 GGM shredder path를 사용한다. Legacy DRV-01/Axx/F01 powered fixture는 사용하지 않는다.

## 판정 원칙

Quasi-static force/torque 측정은 형상 특성화와 모델 상관용이다. 과거 18/22/24 N·m 숫자를 P4 합격기준으로 재사용하지 않는다. 실제 powered run에서는 P3에서 보정한 software gearbox limit 8.0 N·m와 mechanical protection 8.8–9.3 N·m가 controlling이다.

Representative PLA/PET body feed에서 구조/guard 영구손상이 없어야 하고 반복적인 software torque-limit 동작이 정상 운전의 일부가 되어서는 안 된다. Controlled jam은 최대 3회 bounded reverse 안에 복구되거나, 복구 실패 시 latched fault로 종료되어야 하며 자동 재시작은 허용하지 않는다.

Chip-size는 5 mm screen, oversize recirculation 최대 1회 조건에서 3–6 mm 질량분율 70% 이상, >20 mm PET strip 2% 이하, fines 15% 이하, 회수율 95% 이상을 요구한다.

## 기록

기존 `exports/jigs/gate1/`의 preflight, gate1_results, jam_recovery, chip_size CSV를 사용한다. 결과 파일은 template을 덮어쓰지 말고 별도 run directory에 복사해 작성한다. `analyze_p4_records.py --p3-release <P3 release.json>`가 네 CSV를 검사하기 전에 P3 release의 packet/report SHA-256, 독립 검토자, inspector provenance와 현재 P3 domain PASS를 다시 검증한다. P3 release가 stale하거나 조작되었으면 P4 numeric record check 자체가 거부된다. P4 통전은 별도 사용자 승인 사항이다.
