#pragma once

#include <stdint.h>

#include "material_profile.h"
#include "drive_speed_control.h"

enum class ShredderCommand : uint8_t { STOP, FORWARD, OVERLOAD_DWELL, RETRY_STOP, REVERSE, FAULT_LATCHED };

struct ShredderInputs {
  uint32_t now_ms;
  float current_amp;
  float cutter_rpm;
  bool permission_chain_ok;
  bool heater_or_screw_enabled;
  bool tach_valid{true};
};

struct ShredderOutput {
  ShredderCommand command;
  uint8_t target_rpm;
  uint8_t retry_count;
  float estimated_cutter_torque_nm;
  int16_t pwm;
  bool tach_valid;
  bool speed_saturated;
};

class ShredderController {
 public:
  bool configureDrive(const DriveCalibration& calibration);
  bool start(const ProcessProfile& profile, const ShredderInputs& inputs);
  ShredderOutput update(const ShredderInputs& inputs);
  void stop();
  bool canClearFault(bool physical_lockout_confirmed, const ShredderInputs& inputs) const;
  bool clearFault(bool physical_lockout_confirmed, const ShredderInputs& inputs);
  bool faultLatched() const { return command_ == ShredderCommand::FAULT_LATCHED; }
  bool calibrationValid() const { return calibration_configured_; }
  ShredderCommand command() const { return command_; }

 private:
  friend class MachineSupervisor;
  void commitFaultClear();
  void latchFault();
  float estimateCutterTorque(float current_amp) const;
  ShredderOutput outputFor(const ShredderInputs &inputs, uint8_t target_rpm);
  const ProcessProfile* profile_{nullptr};
  DriveCalibration calibration_{};
  bool calibration_configured_{false};
  ShredderCommand command_{ShredderCommand::STOP};
  uint8_t retries_{0};
  uint32_t overload_since_ms_{0};
  uint32_t forward_started_ms_{0};
  uint32_t stop_until_ms_{0};
  uint32_t reverse_until_ms_{0};
  bool overload_active_{false};
  DriveSpeedController speed_controller_{};
};
