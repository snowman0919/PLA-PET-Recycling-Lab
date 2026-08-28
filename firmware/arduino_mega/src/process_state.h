#pragma once

#include "material_profile.h"

enum class ProcessState : uint8_t {
  HOME,
  READY,
  RUNNING,
  PAUSED,
  PURGE_REQUIRED,
  SCREEN_CLEAN_REQUIRED,
  HOPPER_CLEAN_REQUIRED,
  CHANGE_CONFIRM_REQUIRED,
  FAULT_LATCHED
};

struct SafetyInputs {
  bool estop_ok;
  bool lid_closed;
  bool service_guard_closed;
  bool thermal_chain_ok;
  bool predry_confirmed;
};

class ProcessController {
 public:
  bool selectMaterial(MaterialProfile next);
  bool start(const SafetyInputs &inputs);
  void pause();
  void requestMaterialChange(MaterialProfile next);
  bool confirmPurge(uint16_t purge_grams);
  bool confirmScreenClean();
  bool confirmHopperClean();
  bool confirmMaterialChange();
  void reportJam();
  void clearFault(bool physical_lockout_confirmed);
  ProcessState state() const { return state_; }
  MaterialProfile material() const { return material_; }
  bool materialLocked() const { return locked_; }
  uint8_t jamRetries() const { return jam_retries_; }

 private:
  ProcessState state_{ProcessState::HOME};
  MaterialProfile material_{MaterialProfile::NONE};
  MaterialProfile pending_{MaterialProfile::NONE};
  bool locked_{false};
  uint8_t jam_retries_{0};
};
