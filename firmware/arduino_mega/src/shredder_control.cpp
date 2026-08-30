#include "shredder_control.h"

bool ShredderController::configureDrive(const DriveCalibration& calibration) {
  const bool valid = calibration.verified && calibration.no_load_current_a >= 0.0f &&
                     calibration.motor_torque_per_amp_nm > 0.0f &&
                     calibration.motor_to_cutter_ratio > 0.0f &&
                     calibration.drivetrain_efficiency > 0.0f &&
                     calibration.drivetrain_efficiency <= 1.0f &&
                     calibration.max_peak_current_a > calibration.no_load_current_a;
  if (!valid || command_ != ShredderCommand::STOP) return false;
  calibration_ = calibration;
  calibration_configured_ = true;
  return true;
}

bool ShredderController::start(const ProcessProfile& profile,
                               const ShredderInputs& inputs) {
  if (!calibration_configured_ || !inputs.permission_chain_ok || inputs.heater_or_screw_enabled ||
      command_ == ShredderCommand::FAULT_LATCHED) {
    return false;
  }
  profile_ = &profile;
  command_ = ShredderCommand::FORWARD;
  retries_ = 0;
  overload_active_ = false;
  forward_started_ms_ = inputs.now_ms;
  return true;
}

ShredderOutput ShredderController::update(const ShredderInputs& inputs) {
  if (command_ == ShredderCommand::STOP || command_ == ShredderCommand::FAULT_LATCHED) {
    return {command_, 0, retries_, estimateCutterTorque(inputs.current_amp)};
  }
  if (!inputs.permission_chain_ok || inputs.heater_or_screw_enabled || profile_ == nullptr) {
    latchFault();
    return {command_, 0, retries_, estimateCutterTorque(inputs.current_amp)};
  }
  if (command_ == ShredderCommand::RETRY_STOP) {
    if (inputs.now_ms >= stop_until_ms_) {
      ++retries_;
      command_ = ShredderCommand::REVERSE;
      reverse_until_ms_ = inputs.now_ms + profile_->reverse_ms;
    }
    return {command_, 0, retries_, estimateCutterTorque(inputs.current_amp)};
  }
  if (command_ == ShredderCommand::REVERSE) {
    if (inputs.now_ms >= reverse_until_ms_) {
      if (retries_ >= profile_->retry_count) {
        latchFault();
      } else {
        command_ = ShredderCommand::FORWARD;
        overload_active_ = false;
        forward_started_ms_ = inputs.now_ms;
      }
    }
    const uint8_t target = command_ == ShredderCommand::REVERSE
                               ? static_cast<uint8_t>(profile_->shredder_rpm / 2)
                               : profile_->shredder_rpm;
    return {command_, target, retries_, estimateCutterTorque(inputs.current_amp)};
  }

  const float estimated_torque = estimateCutterTorque(inputs.current_amp);
  const bool torque_over = estimated_torque >= profile_->shredder_jam_trip_torque_nm;
  const bool sensor_range_over = inputs.current_amp >= JAM_CURRENT_SENSOR_SATURATION_A;
  const bool speed_drop = inputs.cutter_rpm < JAM_RPM_DEFICIT_RATIO * profile_->shredder_rpm;
  const bool startup_grace_elapsed = inputs.now_ms - forward_started_ms_ >= JAM_STARTUP_GRACE_MS;
  const bool overload = startup_grace_elapsed && (torque_over || (sensor_range_over && speed_drop));
  if (!overload) {
    overload_active_ = false;
    if (command_ == ShredderCommand::OVERLOAD_DWELL) command_ = ShredderCommand::FORWARD;
    return {command_, profile_->shredder_rpm, retries_, estimated_torque};
  }
  if (!overload_active_) {
    overload_active_ = true;
    overload_since_ms_ = inputs.now_ms;
    command_ = ShredderCommand::OVERLOAD_DWELL;
  } else if (inputs.now_ms - overload_since_ms_ >= profile_->overload_ms) {
    command_ = ShredderCommand::RETRY_STOP;
    stop_until_ms_ = inputs.now_ms + JAM_STOP_MS;
    overload_active_ = false;
  }
  const uint8_t target = command_ == ShredderCommand::RETRY_STOP ? 0 : profile_->shredder_rpm;
  return {command_, target, retries_, estimated_torque};
}

float ShredderController::estimateCutterTorque(float current_amp) const {
  if (!calibration_configured_) return 0.0f;
  const float load_current = current_amp > calibration_.no_load_current_a
                                 ? current_amp - calibration_.no_load_current_a
                                 : 0.0f;
  return load_current * calibration_.motor_torque_per_amp_nm *
         calibration_.motor_to_cutter_ratio * calibration_.drivetrain_efficiency;
}

void ShredderController::stop() {
  command_ = ShredderCommand::STOP;
  profile_ = nullptr;
  overload_active_ = false;
}

bool ShredderController::canClearFault(bool physical_lockout_confirmed,
                                       const ShredderInputs& inputs) const {
  return physical_lockout_confirmed && inputs.permission_chain_ok &&
         !inputs.heater_or_screw_enabled;
}

bool ShredderController::clearFault(bool physical_lockout_confirmed,
                                    const ShredderInputs& inputs) {
  if (command_ != ShredderCommand::FAULT_LATCHED ||
      !canClearFault(physical_lockout_confirmed, inputs)) return false;
  commitFaultClear();
  return true;
}

void ShredderController::commitFaultClear() {
  stop();
  retries_ = 0;
}

void ShredderController::latchFault() {
  command_ = ShredderCommand::FAULT_LATCHED;
  overload_active_ = false;
}
