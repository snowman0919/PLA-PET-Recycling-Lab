# Forming-chain 공통 fault와 재자격

입력 fault는 gauge invalid/U95, cooling fan1·fan2, puller driver/tach/persistent saturation, spooler driver/jam, dancer stop/hard stop, traverse permission/hard fault, screw command-motion mismatch다.

공통 순서는 `FAULT_DETECTED → feeder 즉시 off → production spool 불가 → traverse off → spooler controlled stop → puller waste path → screw 10 s bounded rundown → bounded heater hold → requalification 또는 latch`다. 최초 fault timestamp와 상태 변경 timestamp를 runtime view/log에 남긴다.

복구는 원인 제거, physical lockout/restart permission, 센서 validity, 20개 연속 gauge sample, U95 ≤0.03 mm, diameter/ovality 10 s, transport delay, puller inner loop valid/not saturated, cooling valid, screw tach valid, 작업자 rethread 확인이 모두 필요하다. 그 전에는 `waste_path_active=true`, spooler/traverse off다.
