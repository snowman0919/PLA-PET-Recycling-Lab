#pragma once

#include <stdint.h>

enum class MaterialProfile : uint8_t { NONE, PLA, PET };

struct ProcessProfile {
  MaterialProfile material;
  uint8_t shredder_rpm;
  float shredder_continuous_torque_nm;
  float shredder_jam_trip_torque_nm;
  uint16_t overload_ms;
  uint16_t reverse_ms;
  uint8_t retry_count;
  uint8_t maintenance_c;
  bool external_predry_qualified;
  uint8_t predry_c;
  uint16_t predry_minutes;
  float feeder_rpm;
  float screw_rpm;
  uint16_t zone_c[3];
  uint16_t die_c;
  uint8_t fan_percent;
  float puller_feedforward_mm_s;
  float diameter_kp;
  float diameter_ki;
  uint16_t purge_grams;
};

struct DriveCalibration {
  float no_load_current_a;
  float motor_torque_per_amp_nm;
  float motor_to_cutter_ratio;
  float drivetrain_efficiency;
  float max_continuous_current_a;
  float max_peak_current_a;
  float no_load_cutter_rpm;
  float thermal_limit_c;
  bool verified;
};

#include "generated_profiles.h"

inline const ProcessProfile &profileFor(MaterialProfile material) {
  return material == MaterialProfile::PET ? PET_PROFILE : PLA_PROFILE;
}
