#pragma once

#include <stdint.h>

#include "drive_speed_control.h"

struct PullerCalibration {
  float roller_diameter_mm;
  float tach_pulses_per_revolution;
  float maximum_rpm;
  float kp;
  float ki;
  uint8_t minimum_useful_pwm;
  uint8_t maximum_pwm;
  uint16_t startup_ramp_ms;
  uint16_t tach_loss_timeout_ms;
  uint16_t saturation_dwell_ms;
  float saturation_error_mm_s;
  float minimum_stable_rpm{1.0f};
  float motor_to_roller_ratio{0.0f};
};

struct PullerSpeedOutput {
  float target_mm_s;
  float measured_mm_s;
  float target_rpm;
  float measured_rpm;
  float speed_error_mm_s;
  int16_t pwm;
  bool pwm_limited;
  bool saturated;
  uint32_t saturation_duration_ms;
  bool tach_valid;
};

class PullerSpeedController {
 public:
  bool configure(const PullerCalibration &calibration);
  PullerSpeedOutput update(float target_mm_s, float measured_rpm, bool tach_sample_valid,
                           bool enabled, uint32_t now_ms);
  void reset();
  bool configured() const { return configured_; }

 private:
  PullerCalibration calibration_{};
  bool configured_{false};
  DriveSpeedController speed_controller_{};
};
