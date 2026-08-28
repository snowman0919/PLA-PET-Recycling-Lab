# Compact Single-Path PLA/PET Recycler v0.3

이 branch의 active revision은 `compact-single-path-v0.3`이다. PLA와 PET는 hopper부터 spooler까지 하나의 기계 경로를 공유하며, 한 batch에는 한 재질만 허용한다. 운전 중 재질 변경은 금지되고 전환 wizard가 purge, screen·hopper 청소와 작업자 확인을 강제한다.

```text
수동 검사/세척/재질 확인 -> 공용 hopper -> 공용 dual-shaft hook cutter
-> removable 5 mm screen/flake bin -> 외부 pre-dry -> sealed feed hopper
-> 공용 16 mm single screw -> 90 degree metal down-die -> vertical air cooling
-> X/Y shadow gauge -> puller -> solid guide -> dancer/traverse/1 kg spool
```

설계 envelope는 `470 x 700 x 930 mm`이고 hard limit `500 x 750 x 1000 mm` 안에 lid, guard, 1 kg spool, dancer/traverse 전 운동, motor, duct, panel과 cable bend keep-out을 포함한다. Cutter는 76% cycloidal capture flank/24% 빠른 hook relief를 쓴다. `MY1016Z-24V-250W-75RPM` geared brushed-DC motor가 KTR ROTEX19 98ShA bore17/20 coupling으로 오른쪽 shaft를 직접 구동하고, hardened M3 Z16 gear pair가 두 shaft의 반대회전/phase를 유지한다. 한 phase gear의 6 x 6 x 4 mm brass key가 24 N·m nominal sacrificial relief다. PLA/PET 명령은 32/24 rpm이다.

정확 모터·driver·current sensor·hardened phase gear/coupling을 신규 구매하는 현재 cash rollup은 **309,900 KRW**로 hard cap을 109,900 KRW 초과한다. 따라서 이 revision은 자동검증에서 의도적으로 budget FAIL이며 main 승격·구매·full CNC 발주가 금지된다. 고토크 donor motor/gear의 label·shaft·current 확인 또는 실제 RFQ value engineering으로 200,000 KRW 이하가 입증되어야 release할 수 있다. 출력물 계산 질량은 `exports/print/total_material_report.md`에 기록한다.

200 g/h는 stretch target이다. 16 mm, 16 L/D screw의 screening model은 이를 허용하지만 실제 안정 처리량은 cutter/feed/hot extrusion coupon 전 미검증이다. 현재 release claim은 계산 기반 `120–220 g/h commissioning window`뿐이며 물리 gate를 통과하지 않은 처리량·직경·안전 성능을 달성했다고 표시하지 않는다.

## 재현

```bash
nix develop --command bash -lc 'FreeCADCmd -c "import runpy; runpy.run_path(\"cad/generation/generate_all.py\", run_name=\"__main__\")"'
nix develop --command bash -lc 'FreeCADCmd -c "import runpy; runpy.run_path(\"cad/generation/render_views.py\", run_name=\"__main__\")"'
nix develop --command bash -lc 'typst compile --root . docs/build_manual_ko.typ docs/build_manual_ko.pdf && typst compile --root . docs/design_report_ko.typ docs/design_report_ko.pdf'
python3 validation/run_all.py
```

구매·CNC·heater energization은 사용자 승인 전 금지한다. Cutter, screw, heater, mains/high-current의 물리 시험은 `validation/release_checklist.md`의 lockout과 gate를 따른다.

## 동결본

이전 연구 snapshot의 immutable tag/branch와 정확한 SHA는 `docs/archive_index.md`에 기록했다.
