#pragma once

#include <stdint.h>

enum class MaterialProfile : uint8_t { NONE, PLA, PET };

struct ProcessProfile {
  MaterialProfile material;
  uint8_t shredder_rpm;
  float shredder_trip_amp;
  uint16_t overload_ms;
  uint16_t reverse_ms;
  uint8_t retry_count;
  uint8_t maintenance_c;
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

constexpr ProcessProfile PLA_PROFILE{
    MaterialProfile::PLA, 32, 4.8f, 650, 800, 3, 45, 300, 2.2f, 7.0f,
    {180, 195, 205}, 200, 65, 18.6f, 0.40f, 0.025f, 80};

constexpr ProcessProfile PET_PROFILE{
    MaterialProfile::PET, 24, 5.4f, 850, 1100, 3, 60, 420, 1.8f, 6.0f,
    {245, 260, 270}, 265, 85, 16.7f, 0.30f, 0.018f, 120};

inline const ProcessProfile &profileFor(MaterialProfile material) {
  return material == MaterialProfile::PET ? PET_PROFILE : PLA_PROFILE;
}
