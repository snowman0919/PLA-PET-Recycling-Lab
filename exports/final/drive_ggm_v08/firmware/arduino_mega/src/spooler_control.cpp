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
      c.startup_ramp_ms > 0 && c.jam_dwell_ms > 0 &&
      c.packing_factor >= 0.5f && c.packing_factor <= 0.95f &&
      c.minimum_stable_rpm > 0 && c.maximum_rpm > c.minimum_stable_rpm &&
      c.speed_kp >= 0 && c.speed_ki >= 0 && c.tach_loss_timeout_ms > 0;
  if (configured_) {
    config_ = c;
    configured_ = speed_controller_.configure({
        c.minimum_stable_rpm, c.maximum_rpm, c.minimum_useful_pwm, c.maximum_pwm,
        c.speed_kp, c.speed_ki, c.startup_ramp_ms, c.tach_loss_timeout_ms,
        c.saturation_dwell_ms, c.saturation_error_rpm});
  }
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
  speed_controller_.reset();
}

float SpoolerController::estimatedRadiusMm() const {
  if (!configured_) return 0.0f;
  const float radius_squared = config_.core_radius_mm * config_.core_radius_mm +
      wound_length_mm_ * config_.filament_diameter_mm * config_.filament_diameter_mm /
          (4.0f * config_.packing_factor * config_.spool_width_mm);
  return clampf(sqrtf(radius_squared), config_.core_radius_mm, config_.full_radius_mm);
}

bool SpoolerController::applyMeasuredLengthCorrection(float signed_length_mm) {
  if (!configured_) return false;
  const float full_length_mm =
      (config_.full_radius_mm * config_.full_radius_mm -
       config_.core_radius_mm * config_.core_radius_mm) *
      (4.0f * config_.packing_factor * config_.spool_width_mm) /
      (config_.filament_diameter_mm * config_.filament_diameter_mm);
  wound_length_mm_ = clampf(wound_length_mm_ + signed_length_mm, 0.0f, full_length_mm);
  return true;
}

SpoolerOutput SpoolerController::update(float line_speed, float dancer, float measured_rpm,
                                        bool tach_valid, bool enabled, uint32_t now_ms) {
  SpoolerOutput out{};
  out.radius_is_estimated = true;
  out.measured_rpm = measured_rpm;
  out.estimated_radius_mm = estimatedRadiusMm();
  if (!configured_ || !enabled || line_speed <= 0) {
    integral_ = 0;
    enabled_since_ms_ = 0;
    jam_since_ms_ = 0;
    speed_controller_.update(0, measured_rpm, tach_valid, false, now_ms);
    out.tach_valid = !enabled;
    return out;
  }
  if (enabled_since_ms_ == 0) enabled_since_ms_ = now_ms == 0 ? 1 : now_ms;
  const float dt = last_ms_ == 0 ? 0.02f : clampf((now_ms - last_ms_) / 1000.0f, 0.001f, 0.1f);
  last_ms_ = now_ms;
  if (tach_valid && measured_rpm != 0) {
    const float turns_delta = measured_rpm * dt / 60.0f;
    const float length_delta = turns_delta * 2.0f * PI_F * estimatedRadiusMm();
    cumulative_turns_ += turns_delta;
    applyMeasuredLengthCorrection(length_delta);
    out.actual_length_delta_mm = length_delta;
    out.unwinding = length_delta < 0;
  }
  out.estimated_radius_mm = estimatedRadiusMm();
  const float error = dancer - config_.dancer_target_rad;
  const float candidate_integral = clampf(integral_ + error * dt, -2.0f, 2.0f);
  const float target_surface_speed = clampf(
      line_speed + config_.kp * error + config_.ki * candidate_integral, 0.0f,
      2.0f * PI_F * out.estimated_radius_mm * config_.maximum_rpm / 60.0f);
  const float requested_rpm = target_surface_speed * 60.0f /
      (2.0f * PI_F * out.estimated_radius_mm);
  const DriveSpeedOutput speed = speed_controller_.update(
      requested_rpm, measured_rpm, tach_valid, true, now_ms);
  out.target_rpm = speed.target_rpm;
  out.pwm = speed.pwm;
  out.tach_valid = speed.tach_valid;
  out.speed_saturated = speed.saturated;
  if (!speed.limited && speed.tach_valid) integral_ = candidate_integral;
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
