#include "traverse_control.h"

#include <math.h>

bool TraverseController::configure(const TraverseConfig &c) {
  configured_ = c.usable_width_mm > 1 && c.winding_pitch_mm > 0 &&
      c.steps_per_mm > 1 && c.missed_limit_timeout_ms > 0;
  if (configured_) config_ = c;
  reset();
  return configured_;
}

void TraverseController::reset() {
  estimated_position_mm_ = 0;
  last_step_ms_ = 0;
  endpoint_expected_since_ms_ = 0;
  has_seen_interior_ = false;
  hard_fault_ = false;
  position_valid_ = true;
}

void TraverseController::setHomedPosition(float position_mm) {
  if (!configured_ || !isfinite(position_mm)) return;
  if (position_mm < 0) position_mm = 0;
  if (position_mm > config_.usable_width_mm) position_mm = config_.usable_width_mm;
  estimated_position_mm_ = position_mm;
  endpoint_expected_since_ms_ = 0;
  has_seen_interior_ = position_mm > config_.winding_pitch_mm &&
                       position_mm < config_.usable_width_mm - config_.winding_pitch_mm;
  hard_fault_ = false;
  position_valid_ = true;
}

void TraverseController::invalidatePosition() {
  position_valid_ = false;
  endpoint_expected_since_ms_ = 0;
  has_seen_interior_ = false;
}

TraverseOutput TraverseController::update(float spool_turns, bool left_limit, bool right_limit,
                                          bool enabled, uint32_t now_ms) {
  TraverseOutput out{};
  out.estimated_position_mm = estimated_position_mm_;
  out.position_valid = position_valid_;
  if (!configured_ || !enabled || hard_fault_ || !position_valid_) {
    out.hard_fault = hard_fault_;
    return out;
  }
  const float period = 2.0f * config_.usable_width_mm;
  float phase = fmodf(spool_turns * config_.winding_pitch_mm, period);
  if (phase < 0) phase += period;
  out.target_position_mm = phase <= config_.usable_width_mm ? phase : period - phase;
  out.direction = out.target_position_mm >= estimated_position_mm_;
  const float error = out.target_position_mm - estimated_position_mm_;
  const uint32_t interval_ms = 2;
  if (fabsf(error) >= 0.5f / config_.steps_per_mm && now_ms - last_step_ms_ >= interval_ms) {
    const bool blocked = (out.direction && right_limit) || (!out.direction && left_limit);
    if (!blocked) {
      out.step = true;
      estimated_position_mm_ += (out.direction ? 1.0f : -1.0f) / config_.steps_per_mm;
      last_step_ms_ = now_ms;
    }
  }
  const bool near_left = out.target_position_mm <= config_.winding_pitch_mm;
  const bool near_right = out.target_position_mm >= config_.usable_width_mm - config_.winding_pitch_mm;
  const float endpoint_tolerance = 1.0f / config_.steps_per_mm;
  if (estimated_position_mm_ > config_.winding_pitch_mm &&
      estimated_position_mm_ < config_.usable_width_mm - config_.winding_pitch_mm)
    has_seen_interior_ = true;
  // Do not accuse an unhomed carriage at boot. Once motion has crossed the
  // interior, however, reaching a commanded endpoint without its hard limit
  // is a real missed-limit condition and must latch after the configured dwell.
  const bool expected_limit_missing = has_seen_interior_ &&
      ((near_left && !left_limit && estimated_position_mm_ <= endpoint_tolerance) ||
       (near_right && !right_limit &&
        estimated_position_mm_ >= config_.usable_width_mm - endpoint_tolerance));
  if (expected_limit_missing) {
    if (endpoint_expected_since_ms_ == 0) endpoint_expected_since_ms_ = now_ms == 0 ? 1 : now_ms;
    if (now_ms - endpoint_expected_since_ms_ >= config_.missed_limit_timeout_ms) hard_fault_ = true;
  } else {
    endpoint_expected_since_ms_ = 0;
  }
  if (left_limit) estimated_position_mm_ = 0;
  if (right_limit) estimated_position_mm_ = config_.usable_width_mm;
  out.enable = !hard_fault_;
  out.estimated_position_mm = estimated_position_mm_;
  out.hard_fault = hard_fault_;
  out.pitch_synchronized = true;
  out.position_valid = position_valid_;
  return out;
}
