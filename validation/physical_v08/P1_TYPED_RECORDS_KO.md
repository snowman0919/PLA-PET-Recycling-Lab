# P1 의미 검사 R2 - 무전원 재고 기록

P1의 파일 해시는 내용의 진실성을 증명하지 않는다. 실제 식별·외관·수량 확인과 별도 검토자가 필요하다. 이 검사는 구조화된 선언의 수량·단위·일관성을 검사하며 구매·가공·통전을 승인하지 않는다.

`templates/p1_inventory_record.csv`의 30행을 유지한다. 확인하지 않은 행은 NOT_RUN, 미식별은 IDENTITY_PENDING, 손상·부재는 해당 부적합 상태로 남긴다. 자료 없이 PASS를 입력하지 않는다.

## PASS 행의 추가 필드

| 필드 | 조건 |
|---|---|
| manufacturer_model_marking | 실제 읽은 표기 또는 추적 가능한 재고 식별. 공란/UNKNOWN/N/A/미확인 금지 |
| identity_check | 사람이 해당 행의 요구사항과 비교한 경우에만 MATCHED_TO_REQUIREMENT |
| condition | GOOD, USABLE, NEW, USED_SERVICEABLE 중 실제 확인한 상태. 손상·혼합 자유서술은 거부 |
| inspection_power_state | NONE. USB 부팅·모터·히터·내전압 시험은 이 재고 조사에 포함하지 않음 |
| observed_quantity / quantity_unit | 유한한 양수 및 아래 단위. bool, 0, 음수, NaN, 무한대, 단위 섞인 숫자 거부 |
| detail_path / detail_sha256 | 비단순 수량 항목의 구조화된 JSON 근거. 원시 증거와 별도로 해시 결박 |

수량이 정수로 지정된 부품과 MAT-CUT는 `count` 단위의 정확한 배정 수량만 PASS한다. 예비·잉여 재고는 별도 재고 목록에 기록하며 필요한 수량과 혼합하지 않는다. 부족·초과·소수 수량은 거부한다.

프로파일은 `mm` 단위로 bar별 사용 가능 길이와 U95를 JSON entries에 적는다. 개별 길이에서 U95를 뺀 합계가 현행 절단표 순수 길이 이상이어야 한다. 이것만으로 절단 가능성을 보장하지 않는다. P2에서 실제 bar별 nesting과 kerf, 끝단 여유, 별도 승인 조건을 다시 확인한다.

PLA/ABS는 `kg` 단위의 실제 순재고를 기록한다. 약 10 kg/0.5 kg라는 과거 보유량 진술을 새 실측값으로 복사하지 않는다. 이 합격은 질량 재고 기록이며 최종 출력 소요량·건조·재료 적합성 합격이 아니다. K0/chain/fuse/hot coupon은 `set` 1개와 필수 구성품 전부를 열거한다. 테이프는 `roll` 1개, 25 mm/30 m 라벨을 대조하며 S4 열 시험 합격을 대신하지 않는다.

나사·판재·축재·가스켓은 `lot` 1개 아래 entries마다 식별·양·단위·치수/규격을 적고 사람이 검토한다. `ITEMIZED_STOCK_REVIEWED_NOT_FINAL_KITTING`은 재고 내용 검토이지 전체 부품 kitting 완료가 아니다. 상세 JSON은 `P1_INVENTORY_DETAIL`, schema_version 1, item_id, inventory_control_sha256, CSV와 같은 표기/상태/단위/작업자/검토자/시각, `raw_files`, `entries`를 포함한다. `content_review=ACCEPTED_FOR_UNPOWERED_INVENTORY_ONLY`, `physical_action_authorized=false`를 유지한다.

P1_STOCK_SURVEY_PASS_GGM_PENDING은 GGM 수령 미완료다. P1_RECORD_CHECK_PASS도 재고/수령 기록의 검사 결과이며 후속 제작·전력 인가 권한이 아니다. P2는 새 P1 분석기를 다시 호출하므로 오래된 PASS JSON만으로 R2를 우회할 수 없다.
