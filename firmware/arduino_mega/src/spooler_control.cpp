#include "spooler_control.h"

#include <math.h>

namespace {
constexpr float PI_F = 3.14159265358979323846f;
float clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}
}

bool SpoolerController::configure(const SpoolerConfig &c) {
  configured_ = c.core_radius_mm > 1 && c.full_radius_mm > c.core_radius_mm &&
      c.spool_width_mm > c.filament_diameter_mm && c.filament_diameter_mm > 0 &&
      c.kp >= 0 && c.ki >= 0 && c.minimum_useful_pwm < c.maximum_pwm &&
      c.startup_ramp_ms > 0 && c.jam_dwell_ms > 0;
  if (configured_) config_ = c;
  reset();
  return configured_;
}

void SpoolerController::reset() {
  integral_ = 0;
  wound_length_mm_ = 0;
  cumulative_turns_ = 0;
  last_ms_ = 0;
  enabled_since_ms_ = 0;
  jam_since_ms_ = 0;
}

SpoolerOutput SpoolerController::update(float line_speed, float dancer, float measured_rpm,
                                        bool tach_valid, bool enabled, uint32_t now_ms) {
  SpoolerOutput out{};
  out.radius_is_estimated = true;
  out.measured_rpm = measured_rpm > 0 ? measured_rpm : 0;
  if (!configured_ || !enabled || line_speed <= 0) {
    integral_ = 0;
    enabled_since_ms_ = 0;
    jam_since_ms_ = 0;
    out.estimated_radius_mm = config_.core_radius_mm;
    out.tach_valid = !enabled;
    return out;
  }
  if (enabled_since_ms_ == 0) enabled_since_ms_ = now_ms == 0 ? 1 : now_ms;
  const float dt = last_ms_ == 0 ? 0.02f : clampf((now_ms - last_ms_) / 1000.0f, 0.001f, 0.1f);
  last_ms_ = now_ms;
  if (tach_valid && measured_rpm > 0) {
    cumulative_turns_ += measured_rpm * dt / 60.0f;
    const float layer_area = wound_length_mm_ * config_.filament_diameter_mm * config_.filament_diameter_mm /
        config_.spool_width_mm;
    const float radius = sqrtf(config_.core_radius_mm * config_.core_radius_mm + layer_area / PI_F);
    wound_length_mm_ += measured_rpm * 2.0f * PI_F * clampf(radius, config_.core_radius_mm,
                                                            config_.full_radius_mm) * dt / 60.0f;
  }
  const float layer_area = wound_length_mm_ * config_.filament_diameter_mm * config_.filament_diameter_mm /
      config_.spool_width_mm;
  out.estimated_radius_mm = clampf(sqrtf(config_.core_radius_mm * config_.core_radius_mm + layer_area / PI_F),
                                   config_.core_radius_mm, config_.full_radius_mm);
  out.target_rpm = line_speed * 60.0f / (2.0f * PI_F * out.estimated_radius_mm);
  const float error = dancer - config_.dancer_target_rad;
  const float candidate_integral = clampf(integral_ + error * dt, -2.0f, 2.0f);
  const float feedforward = clampf(out.target_rpm / 120.0f * config_.maximum_pwm, 0.0f,
                                   config_.maximum_pwm);
  const float raw = feedforward + config_.kp * error + config_.ki * candidate_integral;
  const float ramp = clampf(static_cast<float>(now_ms - enabled_since_ms_) / config_.startup_ramp_ms,
                            0.05f, 1.0f);
  float pwm = clampf(raw, 0.0f, config_.maximum_pwm) * ramp;
  if (pwm > 0 && pwm < config_.minimum_useful_pwm) pwm = config_.minimum_useful_pwm * ramp;
  if (raw > 0 && raw < config_.maximum_pwm) integral_ = candidate_integral;
  out.pwm = static_cast<int16_t>(pwm + 0.5f);
  out.tach_valid = tach_valid || now_ms - enabled_since_ms_ < 1000;
  if (out.pwm >= config_.minimum_useful_pwm && (!tach_valid || measured_rpm < out.target_rpm * 0.2f)) {
    if (jam_since_ms_ == 0) jam_since_ms_ = now_ms == 0 ? 1 : now_ms;
    out.jam = now_ms - jam_since_ms_ >= config_.jam_dwell_ms;
  } else {
    jam_since_ms_ = 0;
  }
  out.cumulative_turns = cumulative_turns_;
  out.wound_length_mm = wound_length_mm_;
  return out;
}
