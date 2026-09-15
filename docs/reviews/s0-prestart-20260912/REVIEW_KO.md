# S0 시작 전 최종 재검토 - 2026-09-12

검토 대상은 `v1.0.0-rc1`, 소스 `e323c54effa956b1b90ba586fdee8f9d89b447d1`, GitHub Release ID `387184669`다. 이 보고서는 해당 고정 스냅샷에 대한 후속 검토이며 원래 태그와 ZIP을 변경하지 않는다.

## 판정과 우선순위

**공개 범위: 알려진 결함을 명시한 디지털 설계 prerelease. S0 범위: 무전원 식별과 재고 기록만. P1 완료 판정 및 P2 절단·가공은 아래 R1/R2 해소 전 HOLD.**

기존 `25/25 PASS`는 정의된 검사 항목의 통과다. 모든 제조 입력의 정합성 또는 실물 안전성이 증명됐다는 뜻이 아니다. 이번 추가 교차검사에서 기존 검사 목록이 잡지 못한 결함을 확인했다. 과거의 '남은 디지털 작업은 공개 전환뿐'이라는 해석은 적용하지 않는다.

이 보고서의 보류사항은 해당 release의 일반적인 진행 안내보다 우선한다. 아직 원래 P1/P2 프로그램에 새 HOLD를 자동 강제하도록 수정한 것은 아니다. 원래 분석기의 PASS만으로 후속 작업을 승인하지 않는다.

## 다시 실행하여 확인한 것

| 검증 범위 | 결과 |
|---|---|
| draft 자산 6개 재다운로드 | 파일 크기, GitHub digest, 기존 SHA256SUMS 일치 |
| COMPLETE / 압축 해제본 | manifest 대상 3,004개 파일 무결성 PASS |
| repository 소스 | 2,922개 Git blob이 고정 태그와 바이트 단위 일치; 폰트 파일 없음 |
| 새 detached checkout의 light / CAD | 53개 명령, 49개 light 시험 모듈 / 6개 CAD 시험 모듈 PASS |
| 실제 배포 HEX clean rebuild | 기존 a47ff06b...3facf54f와 일치 |
| 기존 해석 증거의 재귀 source binding | 검사 대상 9개 보고서 CURRENT; 전체 해석 신규 solve 아님 |
| compliance / inventory / goal sections | 25/25, 13/13, 26/26 PASS |
| BOM / XLSX / PDF / HTML | 156행·active 114개, 6개 시트 CSV 일치, PDF164개/261쪽 파싱, 링크62개 존재 |
| 빈 P1 템플릿 | 종료코드2, P1_SURVEY_INCOMPLETE, 모든 물리 권한 false |

기존 GitHub의 exact-tag CI-LIGHT `34620746579`, CI-FULL `34619824641`도 성공 상태와 실제 head를 대조했다. 이번 검토는 같은 에이전트의 재검토이며 외부 독립 안전심사나 새로운 실물시험이 아니다.

## R1 - 최종 GGM 프로파일과 기본 절단표 불일치

`exports/fabrication/frame_cut_list.csv`는 2020 26개/13,348 mm, 2040 2개/1,320 mm다. 반면 배포된 `GGM-FULL-ASM.FCStd`에서 이름과 직사각형 단면으로 식별한 프로파일 외형은 2020 38개/15,567 mm, 2040 4개/2,180 mm다. 전자는 기존 기본 구성이고 후자는 추가 구동계 지지·분할된 rail 등을 포함한다. 예를 들어 `MidRail500`과 `GGM_ShredRail`은 각각 2040 L430이며, `FrameSpoolColumnFront`는 L295다.

이 차이는 단순 kerf 여유가 아니다. 근거는 `frame_profile_evidence.json`이다. CAD bounding box에서 추출한 후자의 숫자도 승인된 절단표는 아니며, 이것만 보고 재료를 주문하거나 자르면 안 된다. S0에서는 각 stock의 실제 사용 가능 길이를 자르지 않고 기록한다. P2 전에 부재 ID/단면/길이/수량, 재사용 여부, 끝단 가공·체결, kerf와 U95를 최종 GGM 모델에 1:1 대조한 절단표로 갱신하고 nesting·BOM·도면을 재검증해야 한다.

## R2 - P1 자유서술 필드의 의미 검증 부족

`analyze_p1_records.py`는 evidence 경로/해시·작성자/검토자·시각 등을 확인하지만 수량/정격/손상 문자열의 실질적인 적합성을 모두 판정하지 않는다. 합성 부정시험에서 조사 대상 행의 `result=PASS`, `observed_quantity=0`, 모델 표기 공란, `condition=DAMAGED`에 서로 다른 가상 검토자와 올바른 합성 파일 해시를 제공해도 `P1_STOCK_SURVEY_PASS_GGM_PENDING`이 나왔다.

이 시험은 실제 수령 데이터가 아니며, 완전한 P1 또는 통전 승인 우회를 증명한 것은 아니다. GGM receipt는 미입력 상태이고 hardware_authorization은 false였다. 그러나 개별 부품의 수량·손상이 부적합한데도 조사 PASS를 받는 문제는 실제다. `p1_semantic_negative.json`에 입력 조건과 반환값을 보존했다.

P1 완료 판정 전에 exact-quantity 항목의 수량, 필수 identity, 명시적인 부적합 condition을 거부하도록 수정하고 부족/초과/0/음수/비유한/공란/손상 사례를 시험해야 한다. `assorted`, stock 길이, 1 set처럼 자유서술이 필요한 항목은 별도 구조화된 근거와 사람의 내용 검토가 필요하다. 단순 해시 일치는 사진이나 기록의 내용이 사실임을 증명하지 않는다.

## R3 - S0의 무전원 경계

`mvp_smoke_contract.json`의 S0는 `power=NONE`이다. inventory의 일부 confirmation_action에 있는 Mega USB boot, BTS 전압강하/온도, 절연·내전압 시험은 S0 작업이 아니다. 해당 문구를 S0에서 실행하지 않는다. 전기 도면의 `S0 E-stop`이라는 부품 기호와 smoke checkpoint `S0`도 별개의 이름 공간이다.

## R4 - 안전회로 도면의 표시 품질

`safety_chain.pdf`를 렌더링하면 일부 wire ID와 선이 부품 글자를 덮는다. 이 도면 하나로 단자 연결을 판단하지 않는다. P7 전에 표시를 수정하고 `wire_schedule.csv`, fuse/connector schedule, 실제 수령품 단자와 함께 독립적인 전기 검토를 해야 한다. 이번 PDF 파싱 PASS는 모든 페이지의 가독성 PASS를 의미하지 않는다.

## S0를 시작할 때의 기록 순서

1. 동일한 최종 PPR에 사용할 부품을 대상으로 식별한다. 가공·조립·전원 연결 없이 포장, 제조사/모델/serial/lot, 실제 수량과 외관 상태를 기록한다. 미확인은 IDENTITY_PENDING 또는 SEEN_NOT_MEASURED로 남긴다.
2. 프로파일은 bar별 사용 가능 길이와 측정기/불확도를 기록한다. R1이 해소되기 전 기존 13.348 m/1.320 m를 최종 구매·절단 확정치로 사용하지 않는다.
3. PI 테이프는 같은 25 mm x30 m 롤의 포장·폭·두께·lot 식별을 기록하되, 길이 표기와 실측을 구분한다. 접착제·공식 연속 정격은 미확정이다. 220 C는 판매자 표기 하한에서 정한 잠정값이지 인증된 정격이 아니다. S0에서 부착하거나 180-190 C로 가열하지 않는다.
4. 원시 사진/기록은 수정본과 분리하여 보존하고 경로·SHA-256, 날짜/시간대, 작업자·별도 검토자를 기록한다. 30행 템플릿을 유지하되 자료 없이 PASS로 채우지 않는다. R2 수정 전 분석기 출력은 내용 합격의 대체물이 아니다.

완료가 필요한 후속 디지털 작업은 R2 P1 의미 검사와 R1 최종 프로파일 절단표의 우선 정리, R4 전기 도면 표기 정정이다. S0의 식별·재고 데이터는 이 정리에 사용할 입력이며, 그동안 P1 완료·P2 제작·통전은 해제하지 않는다.

## 여전히 필요한 실물 증거

SCM440 Q&T/질화/최종 가공과 같은 heat/process coupon, GGM 전류-토크/RPM 및 전단핀 교정, 냉·열간 fit과 누설, K0/PE/interlock/독립 thermal cutoff, 측경·PLA/PET·권취·내구성은 NOT_RUN이다. 판매자/도면의 정격을 실제 수령·시험 완료로 바꾸지 않는다. 검토/패키지 공개는 구매·가공·전원·양산 승인이 아니다.

## 공개 자료의 사용법

Release의 원래 COMPLETE/FABRICATION/LAUNCH ZIP은 고정 스냅샷 그대로 보존한다. **COMPLETE ZIP만으로 위 후속 단계의 준비가 끝났다고 판단하지 말고, 별도 첨부된 S0_PRESTART_REVIEW_KO.md와 S0_REVIEW_EVIDENCE.zip을 반드시 함께 확인한다.** 원본 SHA256SUMS는 원래 자산의 해시이고, 새 검토 자료의 해시는 S0_REVIEW_SHA256SUMS에 있다.

새 확인 결과는 `review.json`을 따른다. 추가 검토를 저장한 이후 커밋과 원본 release source commit이 다른 것은 의도적이며, 태그를 이동하거나 원본 패키지의 provenance를 위조하지 않는다. 실제 공개 완료 시각과 공개 URL의 재다운로드 해시는 publication audit에서 별도로 관측한다.
