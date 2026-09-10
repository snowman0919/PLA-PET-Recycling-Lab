#include "feed_delivery_control.h"

#include <math.h>

bool FeedDeliveryController::configure(const FeedDeliveryConfig& c) {
  const bool valid = c.calibration_verified && c.minimum_mass_flow_g_h > 0.0f &&
      c.maximum_mass_flow_g_h >= c.minimum_mass_flow_g_h && c.auger_rpm_per_g_h > 0.0f &&
      c.agitator_to_auger_ratio > 0.0f && c.auger_max_rpm > 0.0f &&
      c.agitator_max_rpm > 0.0f && c.auger_jam_current_a > 0.0f &&
      c.agitator_bridge_current_a > 0.0f && c.auger_trip_current_a > c.auger_jam_current_a &&
      c.agitator_trip_current_a > c.agitator_bridge_current_a && c.low_speed_ratio > 0.0f &&
      c.low_speed_ratio < 1.0f && c.degraded_flow_ratio > 0.0f &&
      c.degraded_flow_ratio < 1.0f && c.auger_minimum_pwm > 0 &&
      c.agitator_minimum_pwm > 0 && c.maximum_pwm > c.auger_minimum_pwm &&
      c.maximum_pwm > c.agitator_minimum_pwm && c.startup_grace_ms > 0 &&
      c.anomaly_dwell_ms > 0 && c.retry_stop_ms > 0 && c.reverse_ms > 0 &&
      c.tach_loss_timeout_ms > 0 && c.degraded_stop_ms > 0 && c.maximum_retries > 0;
  if (!valid || state_ != FeedDeliveryState::STOPPED) return false;
  config_ = c;
  configured_ = true;
  return true;
}

bool FeedDeliveryController::start(float requested_mass_flow_g_h,
                                   const FeedDeliveryInputs& inputs) {
  if (!configured_ || state_ == FeedDeliveryState::FAULT_LATCHED ||
      !inputs.permission_chain_ok ||
      requested_mass_flow_g_h < config_.minimum_mass_flow_g_h ||
      requested_mass_flow_g_h > config_.maximum_mass_flow_g_h) {
    return false;
  }
  requested_mass_flow_g_h_ = requested_mass_flow_g_h;
  retry_count_ = 0;
  fault_ = FeedDeliveryFault::NONE;
  pending_anomaly_ = FeedDeliveryFault::NONE;
  phase_started_ms_ = inputs.now_ms;
  forward_started_ms_ = inputs.now_ms;
  saw_auger_tach_ = inputs.auger_tach_valid;
  saw_agitator_tach_ = inputs.agitator_tach_valid;
  last_auger_tach_ms_ = inputs.now_ms;
  last_agitator_tach_ms_ = inputs.now_ms;
  state_ = FeedDeliveryState::STARTING;
  return true;
}

FeedDeliveryOutput FeedDeliveryController::update(const FeedDeliveryInputs& inputs) {
  if (state_ == FeedDeliveryState::STOPPED || state_ == FeedDeliveryState::FAULT_LATCHED) {
    return makeOutput(inputs);
  }

  // E-stop, guard, or upstream permission removal is an immediate hardware-command inhibit.
  if (!inputs.permission_chain_ok) {
    latchFault(FeedDeliveryFault::PERMISSION_LOSS);
    return makeOutput(inputs);
  }
  if (inputs.auger_current_a >= config_.auger_trip_current_a ||
      inputs.agitator_current_a >= config_.agitator_trip_current_a) {
    latchFault(FeedDeliveryFault::OVERCURRENT);
    return makeOutput(inputs);
  }

  if (inputs.auger_tach_valid) {
    saw_auger_tach_ = true;
    last_auger_tach_ms_ = inputs.now_ms;
  }
  if (inputs.agitator_tach_valid) {
    saw_agitator_tach_ = true;
    last_agitator_tach_ms_ = inputs.now_ms;
  }

  const uint32_t running_ms = inputs.now_ms - forward_started_ms_;
  const uint32_t auger_tach_age = saw_auger_tach_ ? inputs.now_ms - last_auger_tach_ms_ : running_ms;
  const uint32_t agitator_tach_age = saw_agitator_tach_
      ? inputs.now_ms - last_agitator_tach_ms_ : running_ms;

  if (state_ == FeedDeliveryState::RETRY_STOP) {
    if (inputs.now_ms - phase_started_ms_ >= config_.retry_stop_ms) {
      if (retry_count_ >= config_.maximum_retries) {
        latchFault(FeedDeliveryFault::RETRY_EXHAUSTED);
      } else {
        ++retry_count_;
        state_ = FeedDeliveryState::REVERSING;
        phase_started_ms_ = inputs.now_ms;
      }
    }
    return makeOutput(inputs);
  }
  if (state_ == FeedDeliveryState::REVERSING) {
    if (auger_tach_age >= config_.tach_loss_timeout_ms ||
        agitator_tach_age >= config_.tach_loss_timeout_ms) {
      latchFault(FeedDeliveryFault::TACH_LOSS);
      return makeOutput(inputs);
    }
    if (inputs.now_ms - phase_started_ms_ >= config_.reverse_ms) {
      state_ = FeedDeliveryState::STARTING;
      phase_started_ms_ = inputs.now_ms;
      forward_started_ms_ = inputs.now_ms;
      pending_anomaly_ = FeedDeliveryFault::NONE;
    }
    return makeOutput(inputs);
  }

  if (running_ms >= config_.startup_grace_ms &&
      auger_tach_age >= config_.tach_loss_timeout_ms) {
    latchFault(FeedDeliveryFault::TACH_LOSS);
    return makeOutput(inputs);
  }

  if (running_ms >= config_.startup_grace_ms &&
      agitator_tach_age >= config_.tach_loss_timeout_ms) {
    if (state_ != FeedDeliveryState::DEGRADED_DERATE) {
      state_ = FeedDeliveryState::DEGRADED_DERATE;
      phase_started_ms_ = inputs.now_ms;
    } else if (inputs.now_ms - phase_started_ms_ >= config_.degraded_stop_ms) {
      latchFault(FeedDeliveryFault::TACH_LOSS);
      return makeOutput(inputs);
    }
  } else if (state_ == FeedDeliveryState::DEGRADED_DERATE) {
    state_ = FeedDeliveryState::FORWARD;
    phase_started_ms_ = inputs.now_ms;
  }

  if (state_ == FeedDeliveryState::STARTING && running_ms >= config_.startup_grace_ms) {
    state_ = FeedDeliveryState::FORWARD;
    phase_started_ms_ = inputs.now_ms;
  }

  const FeedDeliveryOutput command = makeOutput(inputs);
  const bool protection_active = state_ == FeedDeliveryState::FORWARD ||
      state_ == FeedDeliveryState::DEGRADED_DERATE || state_ == FeedDeliveryState::ANOMALY_DWELL;
  const bool jam = protection_active && inputs.auger_tach_valid &&
      inputs.auger_rpm < command.auger_target_rpm * config_.low_speed_ratio &&
      inputs.auger_current_a >= config_.auger_jam_current_a;
  const bool bridge = protection_active && inputs.agitator_tach_valid &&
      inputs.agitator_rpm < command.agitator_target_rpm * config_.low_speed_ratio &&
      inputs.agitator_current_a >= config_.agitator_bridge_current_a;

  if (jam || bridge) {
    const FeedDeliveryFault detected = jam ? FeedDeliveryFault::JAM : FeedDeliveryFault::BRIDGE;
    if (state_ != FeedDeliveryState::ANOMALY_DWELL || pending_anomaly_ != detected) {
      beginAnomaly(detected, inputs.now_ms);
    } else if (inputs.now_ms - phase_started_ms_ >= config_.anomaly_dwell_ms) {
      state_ = FeedDeliveryState::RETRY_STOP;
      phase_started_ms_ = inputs.now_ms;
    }
  } else if (state_ == FeedDeliveryState::ANOMALY_DWELL) {
    pending_anomaly_ = FeedDeliveryFault::NONE;
    state_ = FeedDeliveryState::FORWARD;
    phase_started_ms_ = inputs.now_ms;
  }
  return makeOutput(inputs);
}

void FeedDeliveryController::stop() {
  state_ = FeedDeliveryState::STOPPED;
  fault_ = FeedDeliveryFault::NONE;
  pending_anomaly_ = FeedDeliveryFault::NONE;
  requested_mass_flow_g_h_ = 0.0f;
  retry_count_ = 0;
  saw_auger_tach_ = false;
  saw_agitator_tach_ = false;
}

bool FeedDeliveryController::clearFault(bool physical_lockout_confirmed,
                                        const FeedDeliveryInputs& inputs) {
  if (state_ != FeedDeliveryState::FAULT_LATCHED || !physical_lockout_confirmed ||
      !inputs.permission_chain_ok || inputs.auger_current_a >= config_.auger_jam_current_a ||
      inputs.agitator_current_a >= config_.agitator_bridge_current_a) {
    return false;
  }
  stop();
  return true;
}

void FeedDeliveryController::latchFault(FeedDeliveryFault fault) {
  state_ = FeedDeliveryState::FAULT_LATCHED;
  fault_ = fault;
  pending_anomaly_ = FeedDeliveryFault::NONE;
}

void FeedDeliveryController::beginAnomaly(FeedDeliveryFault fault, uint32_t now_ms) {
  pending_anomaly_ = fault;
  state_ = FeedDeliveryState::ANOMALY_DWELL;
  phase_started_ms_ = now_ms;
}

FeedDeliveryOutput FeedDeliveryController::makeOutput(const FeedDeliveryInputs& inputs) const {
  FeedDeliveryOutput out{};
  out.state = state_;
  out.fault = fault_;
  out.requested_mass_flow_g_h = requested_mass_flow_g_h_;
  out.retry_count = retry_count_;
  out.jam_detected = pending_anomaly_ == FeedDeliveryFault::JAM;
  out.bridge_detected = pending_anomaly_ == FeedDeliveryFault::BRIDGE;
  out.derated = state_ == FeedDeliveryState::DEGRADED_DERATE;
  out.inhibited = state_ == FeedDeliveryState::STOPPED ||
      state_ == FeedDeliveryState::RETRY_STOP || state_ == FeedDeliveryState::FAULT_LATCHED;
  if (out.inhibited) return out;

  if (state_ == FeedDeliveryState::REVERSING) {
    out.auger_target_rpm = -config_.auger_max_rpm * 0.35f;
    out.agitator_target_rpm = -config_.agitator_max_rpm * 0.35f;
    out.auger_pwm = -static_cast<int16_t>(config_.auger_minimum_pwm);
    out.agitator_pwm = -static_cast<int16_t>(config_.agitator_minimum_pwm);
    return out;
  }

  out.commanded_mass_flow_g_h = out.derated
      ? requested_mass_flow_g_h_ * config_.degraded_flow_ratio : requested_mass_flow_g_h_;
  out.auger_target_rpm = out.commanded_mass_flow_g_h * config_.auger_rpm_per_g_h;
  out.agitator_target_rpm = out.derated
      ? 0.0f : out.auger_target_rpm * config_.agitator_to_auger_ratio;
  const float auger_fraction = clampf(out.auger_target_rpm / config_.auger_max_rpm, 0.0f, 1.0f);
  const float agitator_fraction = clampf(out.agitator_target_rpm / config_.agitator_max_rpm, 0.0f, 1.0f);
  const float auger_error = out.auger_target_rpm - inputs.auger_rpm;
  const float agitator_error = out.agitator_target_rpm - inputs.agitator_rpm;
  const float auger_pwm = config_.auger_minimum_pwm + auger_fraction *
      (config_.maximum_pwm - config_.auger_minimum_pwm) + 2.0f * auger_error;
  const float agitator_pwm = config_.agitator_minimum_pwm + agitator_fraction *
      (config_.maximum_pwm - config_.agitator_minimum_pwm) + 1.0f * agitator_error;
  out.auger_pwm = static_cast<int16_t>(clampf(auger_pwm, config_.auger_minimum_pwm,
                                              config_.maximum_pwm) + 0.5f);
  out.agitator_pwm = out.derated ? 0 : static_cast<int16_t>(clampf(
      agitator_pwm, config_.agitator_minimum_pwm, config_.maximum_pwm) + 0.5f);
  return out;
}

float FeedDeliveryController::clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}
