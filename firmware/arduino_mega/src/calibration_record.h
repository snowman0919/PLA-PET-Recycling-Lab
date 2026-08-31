#pragma once

#include <math.h>
#include <stddef.h>
#include <stdint.h>

#include "gauge_control.h"
#include "material_profile.h"
#include "puller_speed_control.h"
#include "spooler_control.h"
#include "traverse_control.h"

constexpr uint32_t CALIBRATION_RECORD_MAGIC = 0x50505236UL;
// Version 4 deliberately invalidates the v3 shared-readiness layout.
constexpr uint16_t CALIBRATION_RECORD_VERSION = 4;

enum CalibrationId : uint8_t {
  CAL_SHREDDER_TACH = 0,
  CAL_SHREDDER_DRIVE,
  CAL_SCREW_TACH,
  CAL_PULLER_TACH,
  CAL_PULLER_DRIVE,
  CAL_SPOOLER_TACH,
  CAL_SPOOLER_DRIVE,
  CAL_TRAVERSE,
  CAL_GAUGE_XY,
  CAL_CURRENT_SENSOR,
  CAL_FAN1_TACH,
  CAL_FAN2_TACH,
  CAL_DANCER,
  CAL_COOLING_CURRENT,
  CAL_COUNT,
};

enum class CalibrationUnits : uint8_t {
  NONE = 0,
  PULSES_PER_REVOLUTION,
  RPM,
  STEPS_PER_MILLIMETRE,
  MILLIMETRES_PER_ADC_COUNT,
  AMPERES_PER_ADC_COUNT,
  RADIANS_PER_ADC_COUNT,
};

enum class CalibrationSource : uint8_t {
  REFERENCE_DEFAULT = 0,
  SIMULATION,
  COMMISSIONING_MEASUREMENT,
  FACTORY_CERTIFICATE,
};

struct CalibrationValueRecord {
  uint8_t id;
  CalibrationUnits units;
  CalibrationSource source;
  uint8_t verified;
  uint32_t revision;
  float value;
  float valid_min;
  float valid_max;
  uint32_t crc;
};

// Compatibility names remain one-to-one aliases. They are not a shared domain:
// in particular CALIBRATION_HAS_PULLER no longer approves screw, spooler, or traverse.
constexpr uint16_t CALIBRATION_HAS_DRIVE = 1U << CAL_SHREDDER_DRIVE;
constexpr uint16_t CALIBRATION_HAS_PULLER = 1U << CAL_PULLER_DRIVE;
constexpr uint16_t CALIBRATION_HAS_GAUGE = 1U << CAL_GAUGE_XY;
constexpr uint16_t CALIBRATION_HAS_CURRENT_SENSOR = 1U << CAL_CURRENT_SENSOR;
// Legacy cooling-current metadata is retained for the existing adapter, but fan
// tach readiness is represented only by CAL_FAN1_TACH and CAL_FAN2_TACH.
constexpr uint16_t CALIBRATION_HAS_COOLING = 1U << CAL_COOLING_CURRENT;

struct CalibrationRecord {
  uint32_t magic;
  uint16_t version;
  uint16_t readiness_flags;
  CalibrationValueRecord records[CAL_COUNT];
  GaugeCalibration gauge;
  DriveCalibration drive;
  float current_zero_adc;
  float current_amps_per_count;
  float cooling_zero_adc;
  float cooling_amps_per_count;
  PullerCalibration puller;
  SpoolerConfig spooler;
  TraverseConfig traverse;
  float shredder_tach_pulses_per_revolution;
  float screw_tach_pulses_per_revolution;
  float spooler_tach_pulses_per_revolution;
  float fan1_tach_pulses_per_revolution;
  float fan2_tach_pulses_per_revolution;
  float dancer_radians_per_count;
  // Retained as an adapter compatibility mirror of traverse.steps_per_mm.
  float traverse_steps_per_mm;
  uint32_t crc;
};

inline uint32_t calibrationBytesCrc(const uint8_t *bytes, size_t count) {
  uint32_t hash = 2166136261UL;
  for (size_t i = 0; i < count; ++i) hash = (hash ^ bytes[i]) * 16777619UL;
  return hash;
}

inline uint32_t calibrationValueRecordCrc(const CalibrationValueRecord &record) {
  return calibrationBytesCrc(reinterpret_cast<const uint8_t *>(&record),
                             offsetof(CalibrationValueRecord, crc));
}

inline CalibrationUnits calibrationUnitsForId(CalibrationId id) {
  switch (id) {
    case CAL_SHREDDER_TACH:
    case CAL_SCREW_TACH:
    case CAL_PULLER_TACH:
    case CAL_SPOOLER_TACH:
    case CAL_FAN1_TACH:
    case CAL_FAN2_TACH:
      return CalibrationUnits::PULSES_PER_REVOLUTION;
    case CAL_SHREDDER_DRIVE:
    case CAL_PULLER_DRIVE:
    case CAL_SPOOLER_DRIVE:
      return CalibrationUnits::RPM;
    case CAL_TRAVERSE:
      return CalibrationUnits::STEPS_PER_MILLIMETRE;
    case CAL_GAUGE_XY:
      return CalibrationUnits::MILLIMETRES_PER_ADC_COUNT;
    case CAL_CURRENT_SENSOR:
    case CAL_COOLING_CURRENT:
      return CalibrationUnits::AMPERES_PER_ADC_COUNT;
    case CAL_DANCER:
      return CalibrationUnits::RADIANS_PER_ADC_COUNT;
    case CAL_COUNT:
      break;
  }
  return CalibrationUnits::NONE;
}

inline bool calibrationValueRecordValid(const CalibrationValueRecord &record,
                                        CalibrationId expected_id) {
  if (record.id != static_cast<uint8_t>(expected_id) ||
      record.units > CalibrationUnits::RADIANS_PER_ADC_COUNT ||
      record.source > CalibrationSource::FACTORY_CERTIFICATE ||
      record.verified > 1 || !isfinite(record.value) || !isfinite(record.valid_min) ||
      !isfinite(record.valid_max) || record.valid_min > record.valid_max ||
      record.crc != calibrationValueRecordCrc(record)) return false;
  if (record.verified == 0) return true;
  const bool traceable_source = record.source == CalibrationSource::COMMISSIONING_MEASUREMENT ||
                                record.source == CalibrationSource::FACTORY_CERTIFICATE;
  return traceable_source && record.revision > 0 && record.units == calibrationUnitsForId(expected_id) &&
         record.value >= record.valid_min && record.value <= record.valid_max;
}

inline void initializeCalibrationValueRecord(CalibrationValueRecord &record, CalibrationId id) {
  record = CalibrationValueRecord{};
  record.id = static_cast<uint8_t>(id);
  record.units = CalibrationUnits::NONE;
  record.source = CalibrationSource::REFERENCE_DEFAULT;
  record.crc = calibrationValueRecordCrc(record);
}

inline bool setCalibrationValueRecord(CalibrationValueRecord &record, CalibrationId id,
                                      float value, CalibrationUnits units, uint32_t revision,
                                      CalibrationSource source, bool verified,
                                      float valid_min, float valid_max) {
  record = CalibrationValueRecord{};
  record.id = static_cast<uint8_t>(id);
  record.units = units;
  record.source = source;
  record.verified = verified ? 1 : 0;
  record.revision = revision;
  record.value = value;
  record.valid_min = valid_min;
  record.valid_max = valid_max;
  record.crc = calibrationValueRecordCrc(record);
  return calibrationValueRecordValid(record, id);
}

inline bool calibrationDomainReady(const CalibrationRecord &record, CalibrationId id) {
  return id < CAL_COUNT && calibrationValueRecordValid(record.records[id], id) &&
         record.records[id].verified != 0;
}

inline uint16_t calibrationReadinessMask(const CalibrationRecord &record) {
  uint16_t mask = 0;
  for (uint8_t id = 0; id < CAL_COUNT; ++id) {
    if (calibrationDomainReady(record, static_cast<CalibrationId>(id))) mask |= 1U << id;
  }
  return mask;
}

inline uint32_t calibrationRecordCrc(const CalibrationRecord &record) {
  return calibrationBytesCrc(reinterpret_cast<const uint8_t *>(&record),
                             offsetof(CalibrationRecord, crc));
}

inline bool calibrationRecordValid(const CalibrationRecord &record) {
  if (record.magic != CALIBRATION_RECORD_MAGIC || record.version != CALIBRATION_RECORD_VERSION ||
      record.readiness_flags != calibrationReadinessMask(record) ||
      record.crc != calibrationRecordCrc(record)) return false;
  for (uint8_t id = 0; id < CAL_COUNT; ++id) {
    if (!calibrationValueRecordValid(record.records[id], static_cast<CalibrationId>(id))) return false;
  }
  return true;
}

inline bool sanitizeCalibrationRecord(CalibrationRecord &record) {
  if (calibrationRecordValid(record)) return true;
  // Old schemas and any CRC failure are explicitly invalidated; defaults remain unverified.
  record = CalibrationRecord{};
  return false;
}

inline void finalizeCalibrationRecord(CalibrationRecord &record) {
  for (uint8_t id = 0; id < CAL_COUNT; ++id) {
    const CalibrationId calibration_id = static_cast<CalibrationId>(id);
    if (!calibrationValueRecordValid(record.records[id], calibration_id))
      initializeCalibrationValueRecord(record.records[id], calibration_id);
  }
  record.magic = CALIBRATION_RECORD_MAGIC;
  record.version = CALIBRATION_RECORD_VERSION;
  record.readiness_flags = calibrationReadinessMask(record);
  record.crc = calibrationRecordCrc(record);
}
