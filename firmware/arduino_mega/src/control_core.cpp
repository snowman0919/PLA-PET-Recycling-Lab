#include "control_core.h"

#include <math.h>

namespace recycler {

namespace {
constexpr uint32_t kSelfTestStableMs = 500;
constexpr uint32_t kContactorCloseTimeoutMs = 250;
constexpr float kPressureTripMpa = 8.0F;

float clamp01(float value) {
  if (value < 0.0F) return 0.0F;
  if (value > 1.0F) return 1.0F;
  return value;
}
}  // namespace

SafetyCore::SafetyCore()
    : state_(SafetyState::SAFE_OFF),
      phase_(Phase::IDLE),
      faults_(FAULT_NONE),
      state_since_ms_(0),
      contactor_request_since_ms_(0),
      prior_contactor_request_(false) {}

void SafetyCore::latch(uint32_t faults, bool estop) {
  faults_ |= faults;
  phase_ = Phase::IDLE;
  state_ = estop ? SafetyState::ESTOP_LATCHED : SafetyState::FAULT_LATCHED;
}

bool SafetyCore::reset_prerequisites(const SafetyInputs& in) const {
  return in.estop_loop_closed && in.lid_loop_closed && in.service_loop_closed &&
         in.thermal_chain_closed && in.sensors_plausible && !in.contactor_feedback_on &&
         in.melt_pressure_mpa < kPressureTripMpa;
}

SafetyOutputs SafetyCore::outputs_for(const SafetyInputs& in) const {
  const bool running = state_ == SafetyState::RUNNING;
  const bool local_chain = in.estop_loop_closed && in.lid_loop_closed &&
                           in.service_loop_closed && in.thermal_chain_closed;
  const bool energize = running && local_chain && faults_ == FAULT_NONE;
  const bool cooldown_allowed = in.estop_loop_closed && in.thermal_chain_closed &&
                                (state_ == SafetyState::PAUSED ||
                                 state_ == SafetyState::FAULT_LATCHED ||
                                 phase_ == Phase::COOLDOWN_CLEAN);
  return {state_, phase_, faults_, energize, energize, energize, cooldown_allowed};
}

SafetyOutputs SafetyCore::tick(const SafetyInputs& in) {
  if (!in.estop_loop_closed) latch(FAULT_ESTOP, true);

  uint32_t injected = FAULT_NONE;
  if (in.injected_jam_fault) injected |= FAULT_JAM;
  if (in.injected_power_fault) injected |= FAULT_POWER_BUDGET;
  if (in.injected_protocol_fault) injected |= FAULT_PROTOCOL;
  if (injected != FAULT_NONE) latch(injected, false);

  const bool active_or_arming = state_ == SafetyState::SELF_TEST ||
                                state_ == SafetyState::READY ||
                                state_ == SafetyState::RUNNING ||
                                state_ == SafetyState::PAUSED;
  if (active_or_arming) {
    uint32_t faults = FAULT_NONE;
    if (!in.lid_loop_closed) faults |= FAULT_LID;
    if (!in.service_loop_closed) faults |= FAULT_SERVICE;
    if (!in.thermal_chain_closed) faults |= FAULT_THERMAL_CHAIN;
    if (!in.sensors_plausible) faults |= FAULT_SENSOR;
    if (in.melt_pressure_mpa >= kPressureTripMpa) faults |= FAULT_PRESSURE;
    if ((phase_ == Phase::EXTRUDE_SPOOL || phase_ == Phase::DRY_PREHEAT) &&
        !in.airflow_ok)
      faults |= FAULT_AIRFLOW;
    if (faults != FAULT_NONE) latch(faults, false);
  }

  const bool expected_contactor = state_ == SafetyState::RUNNING && faults_ == FAULT_NONE;
  if (!expected_contactor && in.contactor_feedback_on) {
    latch(FAULT_CONTACTOR, false);
  } else if (expected_contactor) {
    if (!prior_contactor_request_) contactor_request_since_ms_ = in.now_ms;
    if (!in.contactor_feedback_on &&
        in.now_ms - contactor_request_since_ms_ > kContactorCloseTimeoutMs) {
      latch(FAULT_CONTACTOR, false);
    }
  }

  if ((state_ == SafetyState::FAULT_LATCHED || state_ == SafetyState::ESTOP_LATCHED ||
       state_ == SafetyState::SAFE_OFF) &&
      in.reset_requested && reset_prerequisites(in)) {
    faults_ = FAULT_NONE;
    phase_ = Phase::IDLE;
    state_ = SafetyState::SELF_TEST;
    state_since_ms_ = in.now_ms;
  } else if (state_ == SafetyState::SELF_TEST &&
             in.now_ms - state_since_ms_ >= kSelfTestStableMs) {
    state_ = SafetyState::READY;
    state_since_ms_ = in.now_ms;
  } else if (state_ == SafetyState::READY && in.start_requested &&
             in.requested_phase != Phase::IDLE) {
    phase_ = in.requested_phase;
    if ((phase_ == Phase::EXTRUDE_SPOOL || phase_ == Phase::DRY_PREHEAT) &&
        !in.airflow_ok) {
      latch(FAULT_AIRFLOW, false);
    } else {
      state_ = SafetyState::RUNNING;
      state_since_ms_ = in.now_ms;
    }
  } else if (state_ == SafetyState::RUNNING && in.pause_requested) {
    state_ = SafetyState::PAUSED;
    state_since_ms_ = in.now_ms;
  } else if (state_ == SafetyState::PAUSED && in.start_requested &&
             in.requested_phase == phase_) {
    state_ = SafetyState::RUNNING;
    state_since_ms_ = in.now_ms;
  }

  SafetyOutputs out = outputs_for(in);
  prior_contactor_request_ = out.contactor_request;
  return out;
}

HeaterController::HeaterController(const HeaterConfig& config)
    : config_(config),
      integral_(0.0F),
      previous_temperature_c_(0.0F),
      rise_window_start_c_(0.0F),
      previous_ms_(0),
      rise_window_start_ms_(0),
      initialized_(false) {}

void HeaterController::reset(uint32_t now_ms, float measured_c) {
  integral_ = 0.0F;
  previous_temperature_c_ = measured_c;
  rise_window_start_c_ = measured_c;
  previous_ms_ = now_ms;
  rise_window_start_ms_ = now_ms;
  initialized_ = true;
}

HeaterResult HeaterController::update(uint32_t now_ms, float setpoint_c,
                                      float measured_c, bool enabled) {
  if (!initialized_) reset(now_ms, measured_c);
  const uint32_t elapsed_ms = now_ms - previous_ms_;
  const float elapsed_s = elapsed_ms > 0 ? elapsed_ms / 1000.0F : 0.0F;
  const bool finite = isfinite(measured_c);
  bool plausible = finite && measured_c >= config_.minimum_valid_c &&
                   measured_c <= config_.maximum_valid_c;
  if (plausible && elapsed_s > 0.0F) {
    const float rate = fabsf(measured_c - previous_temperature_c_) / elapsed_s;
    plausible = rate <= config_.maximum_rise_c_per_s;
  }
  const bool overtemperature = finite && measured_c >= config_.independent_limit_c;
  if (!enabled || !plausible || overtemperature) {
    integral_ = 0.0F;
    rise_window_start_c_ = measured_c;
    rise_window_start_ms_ = now_ms;
    previous_temperature_c_ = measured_c;
    previous_ms_ = now_ms;
    return {0.0F, plausible, false, overtemperature};
  }

  const float error = setpoint_c - measured_c;
  const float proportional = config_.kp * error;
  const float candidate_integral = integral_ + config_.ki_per_s * error * elapsed_s;
  const float unclamped = proportional + candidate_integral;
  const float duty = clamp01(unclamped);
  if ((unclamped >= 0.0F && unclamped <= 1.0F) ||
      (unclamped < 0.0F && error > 0.0F) || (unclamped > 1.0F && error < 0.0F)) {
    integral_ = candidate_integral;
  }

  bool runaway = false;
  if (duty >= 0.40F && now_ms - rise_window_start_ms_ >= config_.rise_window_ms) {
    runaway = measured_c - rise_window_start_c_ < config_.minimum_expected_rise_c;
    rise_window_start_c_ = measured_c;
    rise_window_start_ms_ = now_ms;
  } else if (duty < 0.40F) {
    rise_window_start_c_ = measured_c;
    rise_window_start_ms_ = now_ms;
  }
  previous_temperature_c_ = measured_c;
  previous_ms_ = now_ms;
  return {runaway ? 0.0F : duty, plausible, runaway, overtemperature};
}

PowerGrant arbitrate_power(const PowerRequest& request, float derated_limit_w) {
  PowerGrant out{true, 1.0F, 0.0F, 0.0F, 0.0F, request.non_heater_w};
  if (request.non_heater_w < 0.0F || derated_limit_w <= 0.0F ||
      request.non_heater_w > derated_limit_w) {
    out.valid = false;
    out.heater_scale = 0.0F;
    return out;
  }

  float ext = request.extruder_heater_w > 0.0F ? request.extruder_heater_w : 0.0F;
  float pla = request.dryer_pla_heater_w > 0.0F ? request.dryer_pla_heater_w : 0.0F;
  float pet = request.dryer_pet_heater_w > 0.0F ? request.dryer_pet_heater_w : 0.0F;
  if (pla > 0.0F && pet > 0.0F) out.valid = false;
  if (request.phase == Phase::SHRED || request.phase == Phase::COOLDOWN_CLEAN ||
      request.phase == Phase::IDLE) {
    ext = pla = pet = 0.0F;
  } else if (request.phase == Phase::EXTRUDE_SPOOL) {
    pla = pet = 0.0F;
  } else if (request.phase == Phase::DRY_PREHEAT && ext > 0.0F && (pla > 0.0F || pet > 0.0F)) {
    out.valid = false;
  }
  if (!out.valid) {
    out.heater_scale = 0.0F;
    return out;
  }

  const float requested_heater = ext + pla + pet;
  const float available = derated_limit_w - request.non_heater_w;
  out.heater_scale = requested_heater > 0.0F ? clamp01(available / requested_heater) : 1.0F;
  out.extruder_heater_w = ext * out.heater_scale;
  out.dryer_pla_heater_w = pla * out.heater_scale;
  out.dryer_pet_heater_w = pet * out.heater_scale;
  out.total_w = request.non_heater_w + out.extruder_heater_w +
                out.dryer_pla_heater_w + out.dryer_pet_heater_w;
  return out;
}

AdaptiveLoadResult evaluate_adaptive_load(const LoadFeatures& features,
                                          const AdaptiveLoadConfig& config) {
  const bool config_valid = config.rms_limit_a > 0.0F && config.peak_limit_a > 0.0F &&
                            config.derivative_limit_a_per_s > 0.0F &&
                            config.minimum_speed_ratio > 0.0F &&
                            config.minimum_speed_ratio < 1.0F &&
                            config.vibration_limit_g > 0.0F &&
                            config.feed_limit_score > 0.0F &&
                            config.overload_score > config.feed_limit_score;
  const bool feature_valid = features.valid && isfinite(features.rms_current_a) &&
                             isfinite(features.peak_current_a) &&
                             isfinite(features.positive_current_derivative_a_per_s) &&
                             isfinite(features.speed_ratio) &&
                             isfinite(features.vibration_peak_g) &&
                             features.rms_current_a >= 0.0F &&
                             features.peak_current_a >= features.rms_current_a &&
                             features.positive_current_derivative_a_per_s >= 0.0F &&
                             features.speed_ratio >= 0.0F && features.speed_ratio <= 1.5F &&
                             features.vibration_peak_g >= 0.0F;
  if (!config_valid || !feature_valid) return {false, false, false, 0.0F, 0.0F, 0.0F};

  const float speed_deficit = clamp01(
      (1.0F - features.speed_ratio) / (1.0F - config.minimum_speed_ratio));
  const float score =
      0.30F * features.rms_current_a / config.rms_limit_a +
      0.20F * features.peak_current_a / config.peak_limit_a +
      0.15F * features.positive_current_derivative_a_per_s /
          config.derivative_limit_a_per_s +
      0.25F * speed_deficit +
      0.10F * features.vibration_peak_g / config.vibration_limit_g;
  const bool speed_drop = features.speed_ratio < config.minimum_speed_ratio;
  const bool overload = score >= config.overload_score ||
                        features.peak_current_a >= 1.20F * config.peak_limit_a ||
                        features.speed_ratio <= 0.35F;
  float feed_scale = 1.0F;
  if (score >= config.feed_limit_score) {
    feed_scale = 1.0F - (score - config.feed_limit_score) /
                            (config.overload_score - config.feed_limit_score);
    feed_scale = clamp01(feed_scale);
  }
  const float drive_scale = overload ? 0.0F : (speed_drop ? 0.85F : 1.0F);
  return {true, overload, speed_drop, score, feed_scale, drive_scale};
}

JamController::JamController() { reset(0); }

void JamController::reset(uint32_t now_ms) {
  state_ = JamState::NORMAL;
  state_since_ms_ = now_ms;
  overload_since_ms_ = now_ms;
  retry_count_ = 0;
}

JamOutput JamController::update(uint32_t now_ms, bool overload, bool speed_drop) {
  const bool jam_signal = overload && speed_drop;
  switch (state_) {
    case JamState::NORMAL:
      if (jam_signal) {
        if (now_ms - overload_since_ms_ >= 250) {
          state_ = JamState::FEED_LIMIT;
          state_since_ms_ = now_ms;
        }
      } else {
        overload_since_ms_ = now_ms;
      }
      break;
    case JamState::FEED_LIMIT:
      if (!jam_signal) {
        state_ = JamState::NORMAL;
        state_since_ms_ = now_ms;
        overload_since_ms_ = now_ms;
      } else if (now_ms - state_since_ms_ >= 500) {
        state_ = JamState::STOP;
        state_since_ms_ = now_ms;
      }
      break;
    case JamState::STOP:
      if (now_ms - state_since_ms_ >= 300) {
        if (retry_count_ >= 3) {
          state_ = JamState::FAULT;
        } else {
          ++retry_count_;
          state_ = JamState::REVERSE;
        }
        state_since_ms_ = now_ms;
      }
      break;
    case JamState::REVERSE:
      if (now_ms - state_since_ms_ >= 800) {
        state_ = JamState::RETRY;
        state_since_ms_ = now_ms;
      }
      break;
    case JamState::RETRY:
      if (now_ms - state_since_ms_ >= 1000) {
        if (jam_signal) {
          state_ = JamState::STOP;
        } else {
          state_ = JamState::NORMAL;
          overload_since_ms_ = now_ms;
        }
        state_since_ms_ = now_ms;
      }
      break;
    case JamState::FAULT:
      break;
  }
  const bool drive = state_ == JamState::NORMAL || state_ == JamState::FEED_LIMIT ||
                     state_ == JamState::REVERSE || state_ == JamState::RETRY;
  const bool feed = state_ == JamState::NORMAL || state_ == JamState::RETRY;
  return {state_, feed, drive, state_ == JamState::REVERSE, retry_count_};
}

}  // namespace recycler
