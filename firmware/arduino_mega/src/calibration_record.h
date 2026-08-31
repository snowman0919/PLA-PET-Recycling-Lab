#pragma once

#include <stddef.h>
#include <stdint.h>

#include "gauge_control.h"
#include "material_profile.h"
#include "puller_speed_control.h"

constexpr uint32_t CALIBRATION_RECORD_MAGIC = 0x50505236UL;
constexpr uint16_t CALIBRATION_RECORD_VERSION = 3;
constexpr uint8_t CALIBRATION_HAS_GAUGE = 1 << 0;
constexpr uint8_t CALIBRATION_HAS_DRIVE = 1 << 1;
constexpr uint8_t CALIBRATION_HAS_CURRENT_SENSOR = 1 << 2;
constexpr uint8_t CALIBRATION_HAS_COOLING = 1 << 3;
constexpr uint8_t CALIBRATION_HAS_PULLER = 1 << 4;

struct CalibrationRecord {
  uint32_t magic;
  uint16_t version;
  uint8_t readiness_flags;
  uint8_t reserved;
  GaugeCalibration gauge;
  DriveCalibration drive;
  float current_zero_adc;
  float current_amps_per_count;
  float cooling_zero_adc;
  float cooling_amps_per_count;
  PullerCalibration puller;
  float screw_tach_pulses_per_revolution;
  float spooler_tach_pulses_per_revolution;
  float traverse_steps_per_mm;
  uint32_t crc;
};

inline uint32_t calibrationRecordCrc(const CalibrationRecord &record) {
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&record);
  uint32_t hash = 2166136261UL;
  for (size_t i = 0; i < offsetof(CalibrationRecord, crc); ++i) hash = (hash ^ bytes[i]) * 16777619UL;
  return hash;
}

inline bool calibrationRecordValid(const CalibrationRecord &record) {
  constexpr uint8_t known = CALIBRATION_HAS_GAUGE | CALIBRATION_HAS_DRIVE |
      CALIBRATION_HAS_CURRENT_SENSOR | CALIBRATION_HAS_COOLING | CALIBRATION_HAS_PULLER;
  return record.magic == CALIBRATION_RECORD_MAGIC && record.version == CALIBRATION_RECORD_VERSION &&
         (record.readiness_flags & static_cast<uint8_t>(~known)) == 0 &&
         record.crc == calibrationRecordCrc(record);
}

inline bool sanitizeCalibrationRecord(CalibrationRecord &record) {
  if (calibrationRecordValid(record)) return true;
  record = CalibrationRecord{};
  return false;
}

inline void finalizeCalibrationRecord(CalibrationRecord &record) {
  record.magic = CALIBRATION_RECORD_MAGIC;
  record.version = CALIBRATION_RECORD_VERSION;
  record.reserved = 0;
  record.crc = calibrationRecordCrc(record);
}
