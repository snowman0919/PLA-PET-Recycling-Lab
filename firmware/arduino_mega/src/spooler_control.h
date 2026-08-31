#pragma once

#include <stdint.h>

struct SpoolerConfig {
  float core_radius_mm;
  float full_radius_mm;
  float spool_width_mm;
  float filament_diameter_mm;
  float dancer_target_rad;
  float kp;
  float ki;
  uint8_t minimum_useful_pwm;
  uint8_t maximum_pwm;
  uint16_t startup_ramp_ms;
  uint16_t jam_dwell_ms;
};

struct SpoolerOutput {
  int16_t pwm;
  float estimated_radius_mm;
  float target_rpm;
  float measured_rpm;
  float cumulative_turns;
  float wound_length_mm;
  bool tach_valid;
  bool jam;
  bool radius_is_estimated;
};

class SpoolerController {
 public:
  bool configure(const SpoolerConfig &config);
  SpoolerOutput update(float line_speed_mm_s, float dancer_angle_rad, float measured_rpm,
                       bool tach_valid, bool enabled, uint32_t now_ms);
  void reset();

 private:
  SpoolerConfig config_{};
  bool configured_{false};
  float integral_{0};
  float wound_length_mm_{0};
  float cumulative_turns_{0};
  uint32_t last_ms_{0};
  uint32_t enabled_since_ms_{0};
  uint32_t jam_since_ms_{0};
};
