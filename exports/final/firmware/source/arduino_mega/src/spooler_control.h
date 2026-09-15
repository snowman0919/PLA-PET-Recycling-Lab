#pragma once

#include <stdint.h>

#include "drive_speed_control.h"

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
  float packing_factor{0.87f};
  float minimum_stable_rpm{0.5f};
  // Legacy aggregate initializers retain a wide test/sensor range. Production
  // calibration must explicitly load the 8 rpm controllable output range.
  float maximum_rpm{30.0f};
  float speed_kp{4.0f};
  float speed_ki{1.0f};
  uint32_t tach_loss_timeout_ms{7500};
  uint16_t saturation_dwell_ms{1200};
  float saturation_error_rpm{1.0f};
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
  float actual_length_delta_mm;
  bool unwinding;
  bool speed_saturated;
};

class SpoolerController {
 public:
  bool configure(const SpoolerConfig &config);
  SpoolerOutput update(float line_speed_mm_s, float dancer_angle_rad, float measured_rpm,
                       bool tach_valid, bool enabled, uint32_t now_ms);
  bool applyMeasuredLengthCorrection(float signed_length_mm);
  float estimatedRadiusMm() const;
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
  DriveSpeedController speed_controller_{};
};
