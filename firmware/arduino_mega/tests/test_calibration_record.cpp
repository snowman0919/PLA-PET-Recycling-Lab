#include <cassert>
#include <iostream>

#include "calibration_record.h"

int main() {
  CalibrationRecord defaults{};
  finalizeCalibrationRecord(defaults);
  assert(calibrationRecordValid(defaults));
  assert(defaults.readiness_flags == 0);
  for (uint8_t id = 0; id < CAL_COUNT; ++id) {
    const auto calibration_id = static_cast<CalibrationId>(id);
    assert(!calibrationDomainReady(defaults, calibration_id));
    assert(defaults.records[id].source == CalibrationSource::REFERENCE_DEFAULT);
    assert(defaults.records[id].verified == 0);
  }

  CalibrationRecord record{};
  record.gauge = {100, 0.002f, 100, 0.002f, 0.02f, true};
  assert(setCalibrationValueRecord(record.records[CAL_GAUGE_XY], CAL_GAUGE_XY,
      0.002f, CalibrationUnits::MILLIMETRES_PER_ADC_COUNT, 7,
      CalibrationSource::COMMISSIONING_MEASUREMENT, true, 0.0001f, 0.01f));
  finalizeCalibrationRecord(record);
  assert(calibrationRecordValid(record));
  assert(calibrationDomainReady(record, CAL_GAUGE_XY));
  assert(!calibrationDomainReady(record, CAL_PULLER_TACH));

  // Independent domains: puller drive must not approve puller tach, screw,
  // spooler, fan, dancer, or traverse calibration.
  assert(setCalibrationValueRecord(record.records[CAL_PULLER_DRIVE], CAL_PULLER_DRIVE,
      160.0f, CalibrationUnits::RPM, 8, CalibrationSource::FACTORY_CERTIFICATE,
      true, 10.0f, 300.0f));
  record.puller = {30.0f, 20.0f, 160.0f, 3.0f, 1.2f, 45, 255, 800, 600, 800, 2.0f};
  finalizeCalibrationRecord(record);
  assert(calibrationDomainReady(record, CAL_PULLER_DRIVE));
  assert(!calibrationDomainReady(record, CAL_PULLER_TACH));
  assert(!calibrationDomainReady(record, CAL_SCREW_TACH));
  assert(!calibrationDomainReady(record, CAL_SPOOLER_TACH));
  assert(!calibrationDomainReady(record, CAL_TRAVERSE));

  assert(setCalibrationValueRecord(record.records[CAL_TRAVERSE], CAL_TRAVERSE,
      80.0f, CalibrationUnits::STEPS_PER_MILLIMETRE, 9,
      CalibrationSource::COMMISSIONING_MEASUREMENT, true, 10.0f, 1000.0f));
  record.traverse_steps_per_mm = 80.0f;
  finalizeCalibrationRecord(record);
  assert(calibrationDomainReady(record, CAL_TRAVERSE));
  assert((record.readiness_flags & (1U << CAL_TRAVERSE)) != 0);

  CalibrationRecord domain_corrupt = record;
  domain_corrupt.records[CAL_TRAVERSE].value = 40.0f;
  domain_corrupt.crc = calibrationRecordCrc(domain_corrupt);
  assert(!calibrationRecordValid(domain_corrupt));  // Per-domain CRC is mandatory.

  CalibrationRecord payload_corrupt = record;
  payload_corrupt.puller.roller_diameter_mm = 99.0f;
  assert(!calibrationRecordValid(payload_corrupt));  // Aggregate CRC covers applied payloads.

  CalibrationRecord stale = record;
  stale.version = 3;
  stale.crc = calibrationRecordCrc(stale);
  assert(!calibrationRecordValid(stale));
  assert(!sanitizeCalibrationRecord(stale));
  assert(stale.magic == 0 && stale.version == 0 && stale.readiness_flags == 0);

  CalibrationRecord simulated{};
  assert(!setCalibrationValueRecord(simulated.records[CAL_SCREW_TACH], CAL_SCREW_TACH,
      1.0f, CalibrationUnits::PULSES_PER_REVOLUTION, 1,
      CalibrationSource::SIMULATION, true, 0.1f, 100.0f));
  finalizeCalibrationRecord(simulated);
  assert(calibrationRecordValid(simulated));
  assert(!calibrationDomainReady(simulated, CAL_SCREW_TACH));

  CalibrationRecord garbage{};
  garbage.magic = 0xA5A5A5A5UL;
  garbage.version = 77;
  garbage.readiness_flags = 0xFFFF;
  garbage.gauge.x_mm_per_count = 123.0f;
  garbage.drive.motor_torque_per_amp_nm = 456.0f;
  assert(!sanitizeCalibrationRecord(garbage));
  assert(garbage.magic == 0 && garbage.version == 0 && garbage.readiness_flags == 0);
  assert(garbage.gauge.x_mm_per_count == 0 && garbage.drive.motor_torque_per_amp_nm == 0);

  std::cout << "EEPROM_INDEPENDENT_CALIBRATION_VERSION_CRC_INVALIDATION_OK\n";
}
