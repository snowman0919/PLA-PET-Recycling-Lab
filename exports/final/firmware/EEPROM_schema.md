# EEPROM schema v4 — GGM drive variant

Magic `0x47474D31`; version `4`; 15 domains: `CAL_SHREDDER_TACH`, `CAL_SHREDDER_DRIVE`, `CAL_SCREW_TACH`, `CAL_PULLER_TACH`, `CAL_PULLER_DRIVE`, `CAL_SPOOLER_TACH`, `CAL_SPOOLER_DRIVE`, `CAL_TRAVERSE`, `CAL_GAUGE_XY`, `CAL_CURRENT_SENSOR`, `CAL_FAN1_TACH`, `CAL_FAN2_TACH`, `CAL_DANCER`, `CAL_COOLING_CURRENT`, `CAL_COUNT`.

Binary order and CRC boundaries are defined by `source/arduino_mega/src/calibration_record.h` (SHA-256 `a37b1471175750042922f44e735e2462e2bc52716d21027f34fb6b3671e15670`). Each domain carries id, units, source, verified, revision, value, valid range and FNV-1a CRC; the aggregate carries readiness mask and whole-record CRC. Raw offsets are compiler-layout dependent, so raw editing is forbidden.

Uninitialized, old-version, out-of-range or CRC-failed data is zeroed/unverified; boot material is `NONE` and production outputs remain inhibited. Only commissioning measurement or factory certificate may be verified. Hardware safety does not depend on EEPROM or firmware.
