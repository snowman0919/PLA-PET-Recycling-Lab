#pragma once

#include <stdint.h>

#include "material_profile.h"

enum class ShredderCommand : uint8_t { STOP, FORWARD, OVERLOAD_DWELL, RETRY_STOP, REVERSE, FAULT_LATCHED };

struct ShredderInputs {
  uint32_t now_ms;
  float current_amp;
  float cutter_rpm;
  bool permission_chain_ok;
  bool heater_or_screw_enabled;
};

struct ShredderOutput {
  ShredderCommand command;
  uint8_t target_rpm;
  uint8_t retry_count;
  float estimated_cutter_torque_nm;
};

class ShredderController {
 public:
  bool configureDrive(const DriveCalibration& calibration);
  bool start(const ProcessProfile& profile, const ShredderInputs& inputs);
  ShredderOutput update(const ShredderInputs& inputs);
  void stop();
  bool clearFault(bool physical_lockout_confirmed, const ShredderInputs& inputs);

 private:
  void latchFault();
  float estimateCutterTorque(float current_amp) const;
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
};
