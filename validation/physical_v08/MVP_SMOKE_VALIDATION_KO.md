# MVP = 최종 제품: 최소 smoke 검증 운용 계약

이 프로젝트에서 MVP는 별도 시제품이 아니다. **MVP와 최종 제품은 동일한 PPR 물리 산출물**이며, MVP는 그 최종 기계가 최소한의 기능을 안전하게 증명한 중간 commissioning 상태를 뜻한다. 별도 throwaway prototype으로 합격한 결과를 최종 기계에 전이하지 않는다.

## 실행 원칙

- P1~P12 stage 체계를 유지하고 `mvp_smoke_contract.json`의 S0~S5 checkpoint를 병행한다.
- smoke checkpoint는 기존 P gate를 우회하거나 energization 권한을 만들지 않는다. 각 실제 통전은 기존 P-stage의 별도 사용자 승인 조건을 그대로 따른다.
- 가능한 모든 시험은 최종 장착될 부품과 최종 배선/구조에서 수행한다. 재료 coupon은 소재·접착제·전단핀·가공공정처럼 final hardware 자체에서 파괴시험을 할 수 없는 특성만 검증한다.
- 실패하면 현장에서 acceptance limit을 완화하거나 임의 가공으로 숨기지 않는다. raw evidence를 보존하고 repository 설계를 수정한 뒤 영향받는 release artifact를 재생성한다.

## 최소 smoke checkpoint

1. **S0 Receipt/Identity**: P1과 함께 라벨·정격·치수·손상을 식별한다.
2. **S1 Cold Geometry/Motion**: P2/P6과 함께 최종 frame/hot path의 fit, hand rotation, travel, TIR/alignment를 본다.
3. **S2 Logic/Safety**: P7에서 logic-only/current-limited 상태로 K0, interlock, PE, reset fail-safe를 본다.
4. **S3 Single-axis Drive**: P3/P8에서 heater를 격리하고 final GGM path를 한 축씩 bounded run한다.
5. **S4 Thermal Barrier Tape**: 현재 수령한 TH-INS-01은 `PI 골드 핑거 테이프`, polyimide film, 25 mm × 30 m이며 제품 정보에는 장기 220–280 °C/단기 300 °C가 표기되어 있다. 제조사/lot와 접착제 화학종은 아직 확정하지 않는다. 동일 30 m roll에서 coupon을 잘라 대표 금속 shield 면에 부착하고 접착 interface가 `180 °C <= peak-U95`, `peak+U95 <=190 °C`인 상태를 최소 600 s 유지한 뒤 연기·탄화·용융·접착제 유동·들뜸을 확인한다. 220 °C는 보수적 continuous design basis이고 300 °C 단기 표기는 정상 운전 설계값으로 쓰지 않는다.
6. **S5 Empty Hot Zone**: P9에서 final hot shield/tape configuration으로 heater-only bounded run을 수행한다.

## 실패 후 설계 feedback

실패한 checkpoint의 raw evidence와 exact configuration을 고정하고, 가장 이른 영향 P-stage를 찾는다. CAD/BOM/electrical/firmware의 source-of-truth를 수정한 후 digital validator와 release artifact를 다시 생성한다. source binding이 바뀐 downstream physical release는 폐기하고, 같은 최종 기계를 수정한 뒤 실패 checkpoint부터 다시 시작한다.

따라서 제작과 검증은 병렬로 진행할 수 있지만, **검증보다 제작이 앞서 downstream 형상을 고정하지 않는다.** 값싼/비파괴 smoke에서 불확실성을 먼저 줄이고, 그 결과를 다음 가공·조달 결정에 반영한다.
