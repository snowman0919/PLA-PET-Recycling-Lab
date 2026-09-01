#include "puller_speed_control.h"

#include <math.h>

namespace {
constexpr float PI_F = 3.14159265358979323846f;
}

bool PullerSpeedController::configure(const PullerCalibration &c) {
  const float circumference = PI_F * c.roller_diameter_mm;
  configured_ = c.roller_diameter_mm > 1.0f && c.tach_pulses_per_revolution >= 1.0f &&
      c.maximum_rpm > c.minimum_stable_rpm && c.minimum_stable_rpm > 0 &&
      c.kp >= 0 && c.ki >= 0 &&
      c.minimum_useful_pwm < c.maximum_pwm &&
      c.startup_ramp_ms > 0 && c.tach_loss_timeout_ms > 0 &&
      c.saturation_dwell_ms > 0 && c.saturation_error_mm_s > 0;
  if (configured_) {
    calibration_ = c;
    configured_ = speed_controller_.configure({
        c.minimum_stable_rpm, c.maximum_rpm, c.minimum_useful_pwm, c.maximum_pwm,
        c.kp * circumference / 60.0f, c.ki * circumference / 60.0f,
        c.startup_ramp_ms, c.tach_loss_timeout_ms, c.saturation_dwell_ms,
        c.saturation_error_mm_s * 60.0f / circumference});
  }
  reset();
  return configured_;
}

void PullerSpeedController::reset() {
  speed_controller_.reset();
}

PullerSpeedOutput PullerSpeedController::update(float target_mm_s, float measured_rpm,
                                                bool tach_sample_valid, bool enabled,
                                                uint32_t now_ms) {
  PullerSpeedOutput out{};
  out.target_mm_s = enabled && configured_ ? target_mm_s : 0;
  out.measured_rpm = measured_rpm > 0 ? measured_rpm : 0;
  if (!configured_ || !enabled || target_mm_s <= 0) {
    reset();
    out.tach_valid = !enabled;
    return out;
  }

  const float circumference = PI_F * calibration_.roller_diameter_mm;
  const float requested_rpm = out.target_mm_s * 60.0f / circumference;
  const DriveSpeedOutput speed = speed_controller_.update(
      requested_rpm, out.measured_rpm, tach_sample_valid, true, now_ms);
  out.target_rpm = speed.target_rpm;
  out.target_mm_s = out.target_rpm * circumference / 60.0f;
  out.measured_mm_s = out.measured_rpm * circumference / 60.0f;
  out.speed_error_mm_s = speed.error_rpm * circumference / 60.0f;
  out.pwm = speed.pwm;
  out.pwm_limited = speed.limited;
  out.saturated = speed.saturated;
  out.saturation_duration_ms = speed.saturation_duration_ms;
  out.tach_valid = speed.tach_valid;
  return out;
}
