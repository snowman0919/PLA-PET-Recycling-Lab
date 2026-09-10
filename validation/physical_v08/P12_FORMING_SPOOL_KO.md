# P12 forming·spool 전체 경로 검증

P12는 P10 또는 P11에서 안정 strand를 확보한 뒤 gauge→puller→dancer→traverse→spool 전체 경로를 검증하는 마지막 물리 gate다. 안정 strand가 없으면 dummy filament/cord로 기구 동작만 확인할 수 있지만, 최종 P12 PASS에는 실제 안정 strand run이 필요하다.

## 순서

1. Gauge X/Y를 traceable pin/wire로 보정한 뒤 puller inlet부터 spool까지 strand path를 hand-feed해 guide/guard 접촉을 확인한다.
2. Stable interval에서 commanded surface speed와 실제 strand speed를 비교해 puller slip을 계산한다. 1% 이하여야 한다.
3. Traverse는 HOME 후 실제 usable width를 측정한다. U95 포함 68 mm 이상이어야 하며 좌우 end collision이 없어야 한다.
4. Dancer를 전체 sweep해 control stop이 0.36 rad 이전에 발생하는지 측정한다. U95를 포함해 0.36 rad 미만이어야 하고 0.4363 rad hard stop에는 접촉하지 않아야 한다.
5. 1 kg nominal spool dummy 또는 실제 spool loading condition으로 full winding path를 완료한다. Spill, guard contact, traverse jam은 0이어야 한다.
6. 실제 filament run에서는 P10/P11 diameter acceptance를 유지하는지 동시에 기록한다. P12가 diameter 문제를 숨기기 위해 puller speed를 과도하게 보정하는 방식은 허용하지 않는다.

`templates/p12_forming_spool.csv`에 계측값과 증거를 기록하고 `analyze_p12_records.py`로 판정한다. P12 PASS는 생산 인증이나 안전 인증이 아니라 프로젝트의 물리 검증 완료 후보 상태다.
