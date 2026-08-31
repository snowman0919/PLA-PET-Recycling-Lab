#pragma once

#include <math.h>
#include <stdint.h>

struct DriveSpeedConfig {
  float minimum_stable_rpm;
  float maximum_rpm;
  uint8_t pwm_dead_zone;
  uint8_t maximum_pwm;
  float kp_pwm_per_rpm;
  float ki_pwm_per_rpm_s;
  uint16_t startup_ramp_ms;
  uint32_t tach_loss_timeout_ms;
  uint16_t saturation_dwell_ms;
  float saturation_error_rpm;
};

struct DriveSpeedOutput {
  float requested_rpm;
  float target_rpm;
  float measured_rpm;
  float error_rpm;
  int16_t pwm;
  bool tach_valid;
  bool tach_loss;
  bool limited;
  bool saturated;
  uint32_t saturation_duration_ms;
};

// Shared signed PI used by all four production drive classes. Definitions are
// inline so the AVR sketch and small host targets cannot accidentally omit a
// second translation unit from their link manifest.
class DriveSpeedController {
 public:
  bool configure(const DriveSpeedConfig &c) {
    configured_ = c.minimum_stable_rpm > 0 && c.maximum_rpm > c.minimum_stable_rpm &&
        c.pwm_dead_zone > 0 && c.pwm_dead_zone < c.maximum_pwm &&
        c.kp_pwm_per_rpm >= 0 && c.ki_pwm_per_rpm_s >= 0 && c.startup_ramp_ms > 0 &&
        c.tach_loss_timeout_ms > 0 && c.saturation_dwell_ms > 0 &&
        c.saturation_error_rpm > 0;
    if (configured_) config_ = c;
    reset();
    return configured_;
  }

  DriveSpeedOutput update(float requested_rpm, float measured_rpm, bool tach_sample_valid,
                          bool enabled, uint32_t now_ms, float load_bias_pwm = 0.0f) {
    DriveSpeedOutput out{};
    out.requested_rpm = configured_ && enabled ? requested_rpm : 0.0f;
    out.measured_rpm = measured_rpm;
    if (!configured_ || !enabled || requested_rpm == 0.0f) {
      reset();
      out.tach_valid = !enabled;
      return out;
    }

    if (!enabled_) {
      enabled_ = true;
      enabled_since_ms_ = now_ms;
    }
    const uint32_t enabled_elapsed_ms = now_ms - enabled_since_ms_;
    const float ramp = clampf(static_cast<float>(enabled_elapsed_ms) /
                                  static_cast<float>(config_.startup_ramp_ms),
                              0.05f, 1.0f);
    out.target_rpm = requested_rpm * ramp;
    const float direction = out.target_rpm >= 0 ? 1.0f : -1.0f;
    const float target_magnitude = fabsf(out.target_rpm);
    const float measured_in_direction = measured_rpm * direction;
    out.error_rpm = target_magnitude - measured_in_direction;

    if (tach_sample_valid) {
      has_valid_tach_ = true;
      last_valid_tach_ms_ = now_ms;
    }
    const uint32_t tach_age_ms = has_valid_tach_ ? now_ms - last_valid_tach_ms_
                                                 : enabled_elapsed_ms;
    out.tach_valid = tach_sample_valid || tach_age_ms < config_.tach_loss_timeout_ms;
    out.tach_loss = !out.tach_valid;

    const float dt_s = last_update_valid_
        ? clampf(static_cast<float>(now_ms - last_ms_) / 1000.0f, 0.001f, 0.1f)
        : 0.02f;
    last_ms_ = now_ms;
    last_update_valid_ = true;

    const float ff_span_rpm = config_.maximum_rpm - config_.minimum_stable_rpm;
    float feedforward = config_.pwm_dead_zone;
    if (target_magnitude > config_.minimum_stable_rpm) {
      feedforward += (target_magnitude - config_.minimum_stable_rpm) / ff_span_rpm *
          (config_.maximum_pwm - config_.pwm_dead_zone);
    }
    const float candidate_integral = clampf(integral_ + out.error_rpm * dt_s,
                                             -config_.maximum_pwm,
                                             config_.maximum_pwm);
    const float raw = feedforward + load_bias_pwm + config_.kp_pwm_per_rpm * out.error_rpm +
        config_.ki_pwm_per_rpm_s * candidate_integral;
    float bounded = clampf(raw, 0.0f, static_cast<float>(config_.maximum_pwm));
    if (bounded > 0 && bounded < config_.pwm_dead_zone) bounded = config_.pwm_dead_zone;
    out.limited = raw <= config_.pwm_dead_zone || raw >= config_.maximum_pwm;
    const bool drives_further_into_limit =
        (raw >= config_.maximum_pwm && out.error_rpm > 0) ||
        (raw <= config_.pwm_dead_zone && out.error_rpm < 0);
    if (!drives_further_into_limit && out.tach_valid) integral_ = candidate_integral;
    if (out.tach_loss) bounded = 0.0f;
    out.pwm = static_cast<int16_t>(direction * (bounded + 0.5f));

    const bool saturation_candidate = ramp >= 1.0f && out.limited &&
        fabsf(out.error_rpm) >= config_.saturation_error_rpm;
    if (saturation_candidate) {
      if (!saturation_active_) {
        saturation_active_ = true;
        saturation_since_ms_ = now_ms;
      }
      out.saturation_duration_ms = now_ms - saturation_since_ms_;
      out.saturated = out.saturation_duration_ms >= config_.saturation_dwell_ms;
    } else {
      saturation_active_ = false;
      saturation_since_ms_ = 0;
    }
    return out;
  }

  void reset() {
    integral_ = 0;
    last_ms_ = 0;
    enabled_since_ms_ = 0;
    last_valid_tach_ms_ = 0;
    saturation_since_ms_ = 0;
    enabled_ = false;
    has_valid_tach_ = false;
    last_update_valid_ = false;
    saturation_active_ = false;
  }

  bool configured() const { return configured_; }

 private:
  static float clampf(float value, float low, float high) {
    return value < low ? low : (value > high ? high : value);
  }

  DriveSpeedConfig config_{};
  bool configured_{false};
  bool enabled_{false};
  bool has_valid_tach_{false};
  bool last_update_valid_{false};
  bool saturation_active_{false};
  float integral_{0};
  uint32_t last_ms_{0};
  uint32_t enabled_since_ms_{0};
  uint32_t last_valid_tach_ms_{0};
  uint32_t saturation_since_ms_{0};
};
