#include <cassert>
#include <iostream>

#include "calibration_record.h"

int main() {
  CalibrationRecord record{};
  record.readiness_flags = CALIBRATION_HAS_GAUGE;
  record.gauge = {100, 0.002f, 100, 0.002f, 0.02f, true};
  finalizeCalibrationRecord(record);
  assert(calibrationRecordValid(record));
  record.readiness_flags |= CALIBRATION_HAS_PULLER;
  record.puller = {30.0f, 20.0f, 160.0f, 3.0f, 1.2f, 45, 255, 800, 600, 800, 2.0f};
  record.screw_tach_pulses_per_revolution = 1.0f;
  record.spooler_tach_pulses_per_revolution = 20.0f;
  record.traverse_steps_per_mm = 80.0f;
  finalizeCalibrationRecord(record);
  assert(calibrationRecordValid(record));
  CalibrationRecord motion_corrupt = record;
  motion_corrupt.puller.roller_diameter_mm = 99.0f;
  assert(!calibrationRecordValid(motion_corrupt));
  CalibrationRecord stale = record;
  stale.version = 1;
  stale.crc = calibrationRecordCrc(stale);
  assert(!calibrationRecordValid(stale));
  CalibrationRecord corrupt = record;
  corrupt.gauge.u95_mm = 0.5f;
  assert(!calibrationRecordValid(corrupt));
  CalibrationRecord garbage{};
  garbage.magic = 0xA5A5A5A5UL;
  garbage.version = 77;
  garbage.readiness_flags = CALIBRATION_HAS_GAUGE | CALIBRATION_HAS_DRIVE;
  garbage.gauge.x_mm_per_count = 123.0f;
  garbage.drive.motor_torque_per_amp_nm = 456.0f;
  assert(!sanitizeCalibrationRecord(garbage));
  assert(garbage.magic == 0 && garbage.version == 0 && garbage.readiness_flags == 0);
  assert(garbage.gauge.x_mm_per_count == 0 && garbage.drive.motor_torque_per_amp_nm == 0);
  garbage.readiness_flags |= CALIBRATION_HAS_COOLING;
  garbage.cooling_zero_adc = 100.0f;
  garbage.cooling_amps_per_count = 0.01f;
  finalizeCalibrationRecord(garbage);
  assert(calibrationRecordValid(garbage));
  assert(garbage.readiness_flags == CALIBRATION_HAS_COOLING);
  assert(garbage.gauge.x_mm_per_count == 0 && garbage.drive.motor_torque_per_amp_nm == 0);
  std::cout << "EEPROM_CALIBRATION_VERSION_CRC_REJECTION_OK\n";
}
