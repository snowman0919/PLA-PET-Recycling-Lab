#include "traverse_homing.h"

#include <math.h>

bool TraverseHomingController::configure(const TraverseHomingConfig &config) {
  configured_ = isfinite(config.steps_per_mm) && isfinite(config.backoff_mm) &&
      config.steps_per_mm > 1.0f && config.backoff_mm > 0.0f &&
      config.step_interval_ms > 0 && config.home_timeout_ms > config.switch_release_timeout_ms &&
      config.switch_release_timeout_ms > 0;
  if (configured_) {
    config_ = config;
    required_backoff_steps_ = static_cast<uint32_t>(ceilf(config.backoff_mm * config.steps_per_mm));
    if (required_backoff_steps_ == 0) required_backoff_steps_ = 1;
  }
  losePosition();
  if (!configured_) enterFault(TraverseHomingFault::CONFIGURATION);
  return configured_;
}

void TraverseHomingController::losePosition() {
  state_ = TraverseHomingState::TRAVERSE_UNHOMED;
  fault_ = TraverseHomingFault::NONE;
  state_started_ms_ = 0;
  last_step_ms_ = 0;
  backoff_steps_ = 0;
  right_active_at_start_ = false;
  estimated_position_mm_ = 0;
}

void TraverseHomingController::resetFault() {
  if (state_ == TraverseHomingState::TRAVERSE_FAULT) losePosition();
}

void TraverseHomingController::enterFault(TraverseHomingFault fault) {
  state_ = TraverseHomingState::TRAVERSE_FAULT;
  fault_ = fault;
}

bool TraverseHomingController::stepDue(uint32_t now_ms) {
  if (last_step_ms_ != 0 && now_ms - last_step_ms_ < config_.step_interval_ms) return false;
  last_step_ms_ = now_ms == 0 ? 1 : now_ms;
  return true;
}

TraverseHomingOutput TraverseHomingController::output(bool enable, bool direction, bool step) const {
  return {enable, direction, step, homed(), estimated_position_mm_, state_, fault_};
}

TraverseHomingOutput TraverseHomingController::update(bool left_limit, bool right_limit,
                                                      bool permission, uint32_t now_ms) {
  if (!configured_) return output(false, false, false);
  if (state_ == TraverseHomingState::TRAVERSE_FAULT ||
      state_ == TraverseHomingState::TRAVERSE_READY ||
      state_ == TraverseHomingState::TRAVERSE_RUNNING)
    return output(false, false, false);
  if (!permission) return output(false, false, false);
  if (left_limit && right_limit) {
    enterFault(TraverseHomingFault::LIMIT_CONFLICT);
    return output(false, false, false);
  }

  if (state_ == TraverseHomingState::TRAVERSE_UNHOMED) {
    state_started_ms_ = now_ms;
    last_step_ms_ = 0;
    if (left_limit) {
      state_ = TraverseHomingState::TRAVERSE_BACKOFF;
      estimated_position_mm_ = 0;
      backoff_steps_ = 0;
    } else {
      state_ = TraverseHomingState::TRAVERSE_HOME_LEFT;
      right_active_at_start_ = right_limit;
    }
  }

  if (state_ == TraverseHomingState::TRAVERSE_HOME_LEFT) {
    if (left_limit) {
      state_ = TraverseHomingState::TRAVERSE_BACKOFF;
      state_started_ms_ = now_ms;
      last_step_ms_ = 0;
      backoff_steps_ = 0;
      estimated_position_mm_ = 0;
      return output(true, true, false);
    }
    if (right_limit && !right_active_at_start_) {
      enterFault(TraverseHomingFault::WRONG_DIRECTION);
      return output(false, false, false);
    }
    if (right_limit && now_ms - state_started_ms_ >= config_.switch_release_timeout_ms) {
      enterFault(TraverseHomingFault::RIGHT_SWITCH_STUCK);
      return output(false, false, false);
    }
    if (!right_limit) right_active_at_start_ = false;
    if (now_ms - state_started_ms_ >= config_.home_timeout_ms) {
      enterFault(TraverseHomingFault::HOME_TIMEOUT);
      return output(false, false, false);
    }
    return output(true, false, stepDue(now_ms));
  }

  if (state_ == TraverseHomingState::TRAVERSE_BACKOFF) {
    if (right_limit) {
      enterFault(TraverseHomingFault::WRONG_DIRECTION);
      return output(false, true, false);
    }
    if (left_limit && now_ms - state_started_ms_ >= config_.switch_release_timeout_ms) {
      enterFault(TraverseHomingFault::LEFT_SWITCH_STUCK);
      return output(false, true, false);
    }
    if (left_limit) return output(true, true, stepDue(now_ms));
    const bool step = stepDue(now_ms);
    if (step) {
      ++backoff_steps_;
      estimated_position_mm_ = static_cast<float>(backoff_steps_) / config_.steps_per_mm;
    }
    if (backoff_steps_ >= required_backoff_steps_) {
      state_ = TraverseHomingState::TRAVERSE_READY;
      estimated_position_mm_ = config_.backoff_mm;
      return output(false, true, false);
    }
    return output(true, true, step);
  }
  return output(false, false, false);
}

void TraverseHomingController::setRunning(bool running) {
  if (running && state_ == TraverseHomingState::TRAVERSE_READY)
    state_ = TraverseHomingState::TRAVERSE_RUNNING;
  else if (!running && state_ == TraverseHomingState::TRAVERSE_RUNNING)
    state_ = TraverseHomingState::TRAVERSE_READY;
}
