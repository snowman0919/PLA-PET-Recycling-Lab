# P4 두-cutter coupon 물리 검증

P4의 목적은 full 12-disc stack 발주 전에 CUT-01 형상, screen, phase pair, GGM 구동/복구가 실제 PLA/PET에서 유효한지 확인하는 것이다. P3 GGM bench는 단순 PASS 문자열이 아니라 `validate_p3_stage_release.py`가 `P3_STAGE_RELEASE_VALIDATED`로 재검증한 release artifact여야 한다. 이 artifact도 P4 통전을 승인하지 않는다.

## 시험 구성

CUT-01은 축당 1장, 총 2장만 사용한다. CUT-03/CUT-05/CUT-05R/CUT-04/CUT-08/09/10, 61905 bearing, phase gear pair와 현 GGM shredder path를 사용한다. Chain path는 `GGM_SH_12T`가 4x4 key로 jackshaft에 직접 결합되고 `GGM_SH_30T`가 6x6x20 key로 CUT-05R에 직접 결합되는 12T:30T 구조다. `DRV-02`와 legacy DRV-01/Axx/F01 powered fixture는 사용하지 않는다. 두 sprocket의 key flank가 토크를 전달해야 하며 수령품 maker retention feature는 축방향 유지 전용이다. P4 preflight에서 두 sprocket의 radial TIR와 axial shift를 각각 실측하고 U95 포함 한계를 판정한다. 수령된 retention 체결 사양이 불명확하면 P4를 HOLD하고 임의 set-screw torque를 만들지 않는다.

## 판정 원칙

Quasi-static force/torque 측정은 형상 특성화와 모델 상관용이다. 과거 18/22/24 N·m 숫자를 P4 합격기준으로 재사용하지 않는다. 실제 powered run에서는 P3에서 보정한 software gearbox limit 8.0 N·m와 mechanical protection 8.8–9.3 N·m가 controlling이다.

Representative PLA/PET body feed에서 구조/guard 영구손상이 없어야 하고 반복적인 software torque-limit 동작이 정상 운전의 일부가 되어서는 안 된다. Controlled jam은 최대 3회 bounded reverse 안에 복구되거나, 복구 실패 시 latched fault로 종료되어야 하며 자동 재시작은 허용하지 않는다.

Chip-size는 5 mm screen, oversize recirculation 최대 1회 조건에서 3–6 mm 질량분율 70% 이상, >20 mm PET strip 2% 이하, fines 15% 이하, 회수율 95% 이상을 요구한다.

## 기록

실제 P4 기록은 `validation/physical_v08/templates/`의 `p4_preflight.csv`, `p4_quasistatic.csv`, `p4_jam.csv`, `p4_chip.csv` 네 파일을 별도 run directory에 복사해 작성한다. `exports/jigs/gate1/*_template.csv`는 legacy Gate-1 형상/시험 참고자료이며 P4 authoritative record 형식이 아니다. 각 실제 행은 작업자와 독립 검토자, timezone 포함 시각, 계측기/교정 참조가 필요한 경우 해당 ID, repository 내부 raw evidence 경로와 SHA-256을 가진다.

`analyze_p4_records.py <run-dir> --p3-release <P3 release.json>`는 먼저 네 P4 파일의 raw evidence hash를 검증하고, 19개 atomic preflight 조건, 25개 quasi-static specimen의 `F*r*cos(theta)`와 U95, 6개 jam trial, PLA/PET raw chip mass를 다시 계산한다. Chip fraction은 입력 percentage를 믿지 않고 질량과 U95에서 보수적으로 산출하며, representative feed에서 software torque-limit event가 있거나 mechanical protection 8.8 N.m 하한에 닿으면 거부한다. 그 뒤 P3 release의 packet/report SHA-256, 독립 검토자, inspector provenance와 현재 P3 domain PASS도 재검증한다. 출력은 `stage_p4_pass=false`, `hardware_authorization=false`, `fabrication_authorized=false`를 유지하므로 남은 CUT-01 10장 제작이나 추가 통전을 자동 승인하지 않는다.

## P4 완료 release와 남은 cutter 잠금

`analyze_p4_records.py`의 결과를 저장한 뒤 사람이 exact result와 raw evidence를 검토한다. `templates/p4_stage_release.json`을 run directory에 복사해 `approved_by`, 서로 다른 `independent_reviewer`, timezone 포함 `reviewed_at`, `p4_result`, `p4_result_sha256`을 채운다. `validate_p4_stage_release.py <release.json>`는 현재 P4 analyzer로 네 raw CSV와 P3 prerequisite를 다시 계산하고, result/analyzer/source hash가 모두 동일할 때만 `P4_STAGE_RELEASE_VALIDATED`를 낸다.

이 상태의 의미는 **남은 CUT-01 10장의 제작 요청을 별도로 검토할 수 있다**는 것뿐이다. validator 출력의 `remaining_cut01_fabrication_authorized`, `downstream_energization_authorized`는 계속 false이며 machine release는 HOLD다. 실제 10장 제작은 `fabrication_sequence.csv` S7의 별도 사용자 full-shredder fabrication approval 없이는 시작하지 않는다.
