# Physical v0.8 raw record templates

All files in this directory are blank schemas. Copy a template into a dated physical-record directory only after the corresponding user-approved stage begins. Never prefill a measured value from simulation. Every nontrivial result should reference a raw photo/CSV/log and SHA-256.

P1 GGM receipt/alignment의 canonical schema는 `analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json`이다. P3 현장 측정은 이 디렉터리의 CSV에 직접 기록하고 `build_p3_inspection_packet.py`로 canonical packet의 protection/current domains를 생성한다. 수기로 JSON에 재입력하지 않는다. Builder는 source packet의 physical authorization을 그대로 보존하며 stage release를 만들지 않는다.
