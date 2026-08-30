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
  bool driver_fault_free;
  bool heater_permission_feedback;
};

class ProcessController {
 public:
  bool selectMaterial(MaterialProfile next);
  bool requestMaterialChange(MaterialProfile next, const SafetyInputs &inputs);
  bool acknowledgeMaterialStep(MaterialSession expected, bool explicit_confirmation);
  bool requestState(MachineState next, const SafetyInputs &inputs);
  void reportFault();
  bool clearFault(const SafetyInputs &inputs, bool physical_lockout_confirmed);
  MachineState state() const { return state_; }
  MaterialProfile material() const { return material_; }
  MaterialProfile pendingMaterial() const { return pending_material_; }
  MaterialSession materialSession() const { return material_session_; }
  bool materialReady() const;
  const StatePermissions &permissions() const;
  bool arbitrationSafe() const;

 private:
  bool transitionAllowed(MachineState next) const;
  MachineState state_{MachineState::IDLE};
  MaterialProfile material_{MaterialProfile::NONE};
  MaterialProfile pending_material_{MaterialProfile::NONE};
  MaterialSession material_session_{MaterialSession::CLEAN};
};
