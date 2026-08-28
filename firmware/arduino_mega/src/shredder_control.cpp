#include "shredder_control.h"

bool ShredderController::start(const ProcessProfile& profile,
                               const ShredderInputs& inputs) {
  if (!inputs.permission_chain_ok || inputs.heater_or_screw_enabled ||
      command_ == ShredderCommand::FAULT_LATCHED) {
    return false;
  }
  profile_ = &profile;
  command_ = ShredderCommand::FORWARD;
  retries_ = 0;
  overload_active_ = false;
  return true;
}

ShredderOutput ShredderController::update(const ShredderInputs& inputs) {
  if (command_ == ShredderCommand::STOP || command_ == ShredderCommand::FAULT_LATCHED) {
    return {command_, 0, retries_};
  }
  if (!inputs.permission_chain_ok || inputs.heater_or_screw_enabled || profile_ == nullptr) {
    latchFault();
    return {command_, 0, retries_};
  }
  if (command_ == ShredderCommand::REVERSE) {
    if (inputs.now_ms >= reverse_until_ms_) {
      if (retries_ >= profile_->retry_count) {
        latchFault();
      } else {
        command_ = ShredderCommand::FORWARD;
        overload_active_ = false;
      }
    }
    const uint8_t target = command_ == ShredderCommand::REVERSE
                               ? static_cast<uint8_t>(profile_->shredder_rpm / 2)
                               : profile_->shredder_rpm;
    return {command_, target, retries_};
  }

  const bool current_over = inputs.current_amp >= profile_->shredder_trip_amp;
  const bool speed_drop = inputs.cutter_rpm < 0.65f * profile_->shredder_rpm;
  const bool overload = current_over || speed_drop;
  if (!overload) {
    overload_active_ = false;
    return {command_, profile_->shredder_rpm, retries_};
  }
  if (!overload_active_) {
    overload_active_ = true;
    overload_since_ms_ = inputs.now_ms;
  } else if (inputs.now_ms - overload_since_ms_ >= profile_->overload_ms) {
    ++retries_;
    command_ = ShredderCommand::REVERSE;
    reverse_until_ms_ = inputs.now_ms + profile_->reverse_ms;
    overload_active_ = false;
  }
  const uint8_t target = command_ == ShredderCommand::REVERSE
                             ? static_cast<uint8_t>(profile_->shredder_rpm / 2)
                             : profile_->shredder_rpm;
  return {command_, target, retries_};
}

void ShredderController::stop() {
  command_ = ShredderCommand::STOP;
  profile_ = nullptr;
  overload_active_ = false;
}

bool ShredderController::clearFault(bool physical_lockout_confirmed,
                                    const ShredderInputs& inputs) {
  if (command_ != ShredderCommand::FAULT_LATCHED || !physical_lockout_confirmed ||
      !inputs.permission_chain_ok || inputs.heater_or_screw_enabled) {
    return false;
  }
  stop();
  retries_ = 0;
  return true;
}

void ShredderController::latchFault() {
  command_ = ShredderCommand::FAULT_LATCHED;
  overload_active_ = false;
}
