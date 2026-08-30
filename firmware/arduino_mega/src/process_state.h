#pragma once

#include "material_profile.h"

struct SafetyInputs {
  bool estop_ok;
  bool lid_closed;
  bool service_guard_closed;
  bool thermal_chain_ok;
  bool temperatures_ready;
  bool gauge_valid;
  bool restart_permission;
};

class ProcessController {
 public:
  bool selectMaterial(MaterialProfile next);
  bool requestState(MachineState next, const SafetyInputs &inputs);
  void reportFault();
  bool clearFault(const SafetyInputs &inputs, bool physical_lockout_confirmed);
  MachineState state() const { return state_; }
  MaterialProfile material() const { return material_; }
  const StatePermissions &permissions() const;
  bool arbitrationSafe() const;

 private:
  bool transitionAllowed(MachineState next) const;
  MachineState state_{MachineState::IDLE};
  MaterialProfile material_{MaterialProfile::NONE};
};
