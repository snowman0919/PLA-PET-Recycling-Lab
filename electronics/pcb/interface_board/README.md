# PPR monitor/interface board

`ppr_interface.kicad_sch`와 `ppr_interface.kicad_pcb`는 KiCad 9 네이티브 산출물이다. `generate.py`가 source of truth이며 `fill_zones.py`는 KiCad의 pcbnew 엔진으로 분리된 FIELD_0V/GND 존을 채운다.

이 보드는 **MONITOR ONLY / NO SAFETY CREDIT / NOT FOR FABRICATION** 상태다. 안전 릴레이, 접촉기, 퓨즈, thermal fuse, heater/motor driver를 대체하지 않는다.

## 재생성

```bash
python3 -m venv /tmp/ppr-kiutils-venv
/tmp/ppr-kiutils-venv/bin/pip install -r electronics/pcb/interface_board/requirements-authoring.txt
/tmp/ppr-kiutils-venv/bin/python electronics/pcb/interface_board/generate.py
kicad-cli sch erc --exit-code-violations electronics/pcb/interface_board/ppr_interface.kicad_sch
kicad-cli pcb drc --exit-code-violations electronics/pcb/interface_board/ppr_interface.kicad_pcb
```

필수 도구는 KiCad CLI/pcbnew 9.0.9와 `kiutils==1.4.8`이다. 회로·PCB 검토 결과는 `design_review_ko.md`, 공식 URL/로컬 검토 해시는 `datasheet_evidence.json`, 제조 출력은 `fabrication/`, 육안 검토 렌더는 `review/`에 있다. 제3자 PDF 자체는 루트 정책에 따라 Git에 넣지 않는다.

## 인터페이스

- J1: 8개 24 V dry-contact 보조 입력과 중복 +24V_SENSE/FIELD_0V
- J2: Mega D22–D29 진단 입력
- J3: Mega command 입력 8개
- J4: 외부 정격 드라이버로 가는 5 V 로직 출력 8개

정확한 케이블 결선은 `design_review_ko.md`와 `electronics/pinout/mega_pinout.csv`를 함께 사용한다. 현재 pin header footprint는 기구 proof용이며 keyed/latching 커넥터 MPN 확정 전 발주 금지다.
