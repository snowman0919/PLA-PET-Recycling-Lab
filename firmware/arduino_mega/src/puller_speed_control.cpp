#include "puller_speed_control.h"

#include <math.h>

namespace {
constexpr float PI_F = 3.14159265358979323846f;
float clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}
}

bool PullerSpeedController::configure(const PullerCalibration &c) {
  configured_ = c.roller_diameter_mm > 1.0f && c.tach_pulses_per_revolution >= 1.0f &&
      c.maximum_rpm > 1.0f && c.kp >= 0 && c.ki >= 0 &&
      c.minimum_useful_pwm < c.maximum_pwm &&
      c.startup_ramp_ms > 0 && c.tach_loss_timeout_ms > 0 &&
      c.saturation_dwell_ms > 0 && c.saturation_error_mm_s > 0;
  if (configured_) calibration_ = c;
  reset();
  return configured_;
}

void PullerSpeedController::reset() {
  integral_ = 0;
  last_ms_ = 0;
  enabled_since_ms_ = 0;
  last_valid_tach_ms_ = 0;
  saturation_since_ms_ = 0;
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

  if (enabled_since_ms_ == 0) enabled_since_ms_ = now_ms == 0 ? 1 : now_ms;
  const uint32_t enabled_elapsed = now_ms >= enabled_since_ms_ ? now_ms - enabled_since_ms_ : 0;
  const float ramp = clampf(static_cast<float>(enabled_elapsed) / calibration_.startup_ramp_ms, 0.05f, 1.0f);
  out.target_mm_s *= ramp;
  const float circumference = PI_F * calibration_.roller_diameter_mm;
  out.target_rpm = out.target_mm_s * 60.0f / circumference;
  out.measured_mm_s = out.measured_rpm * circumference / 60.0f;
  // During startup, compare ramped demand with a ramped contribution from any
  // residual/stale tach reading; otherwise a stopped-to-running transition can
  // be misclassified as lower-bound saturation.
  out.speed_error_mm_s = out.target_mm_s - out.measured_mm_s * ramp;

  if (tach_sample_valid) last_valid_tach_ms_ = now_ms == 0 ? 1 : now_ms;
  const uint32_t since_valid = last_valid_tach_ms_ == 0 ? enabled_elapsed : now_ms - last_valid_tach_ms_;
  out.tach_valid = tach_sample_valid || enabled_elapsed < calibration_.tach_loss_timeout_ms ||
      since_valid < calibration_.tach_loss_timeout_ms;

  const float dt = last_ms_ == 0 ? 0.02f : clampf((now_ms - last_ms_) / 1000.0f, 0.001f, 0.1f);
  last_ms_ = now_ms;
  const float feedforward = out.target_rpm / calibration_.maximum_rpm * calibration_.maximum_pwm;
  const float candidate_integral = clampf(integral_ + out.speed_error_mm_s * dt, -200.0f, 200.0f);
  const float raw = feedforward + calibration_.kp * out.speed_error_mm_s + calibration_.ki * candidate_integral;
  float bounded = clampf(raw, 0.0f, calibration_.maximum_pwm);
  if (bounded > 0 && bounded < calibration_.minimum_useful_pwm) bounded = calibration_.minimum_useful_pwm;
  out.pwm_limited = raw <= calibration_.minimum_useful_pwm || raw >= calibration_.maximum_pwm;
  const bool drives_further_into_limit =
      (raw >= calibration_.maximum_pwm && out.speed_error_mm_s > 0) ||
      (raw <= calibration_.minimum_useful_pwm && out.speed_error_mm_s < 0);
  if (!drives_further_into_limit) integral_ = candidate_integral;
  out.pwm = static_cast<int16_t>(bounded + 0.5f);

  const bool saturation_candidate = ramp >= 1.0f && out.pwm_limited &&
      fabsf(out.speed_error_mm_s) >= calibration_.saturation_error_mm_s;
  if (saturation_candidate) {
    if (saturation_since_ms_ == 0) saturation_since_ms_ = now_ms == 0 ? 1 : now_ms;
    out.saturation_duration_ms = now_ms - saturation_since_ms_;
    out.saturated = out.saturation_duration_ms >= calibration_.saturation_dwell_ms;
  } else {
    saturation_since_ms_ = 0;
  }
  return out;
}
