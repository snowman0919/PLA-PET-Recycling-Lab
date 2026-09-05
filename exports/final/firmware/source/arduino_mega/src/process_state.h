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
  bool requestPurgePreheat(const SafetyInputs &inputs);
  bool markPurgeReady(const SafetyInputs &inputs);
  bool startPurge(bool waste_path_confirmed, const SafetyInputs &inputs);
  bool completePurgeRun(bool completion_evidence_valid);
  bool abortPurge();
  bool acknowledgeMaterialStep(MaterialSession expected, bool explicit_confirmation);
  bool requestState(MachineState next, const SafetyInputs &inputs);
  void reportFault();
  bool canClearFault(const SafetyInputs &inputs, bool physical_lockout_confirmed) const;
  bool clearFault(const SafetyInputs &inputs, bool physical_lockout_confirmed);
  MachineState state() const { return state_; }
  MaterialProfile material() const { return material_; }
  MaterialProfile pendingMaterial() const { return pending_material_; }
  MaterialSession materialSession() const { return material_session_; }
  bool materialReady() const;
  bool purgeActive() const { return material_session_ == MaterialSession::PURGE_RUNNING; }
  const StatePermissions &permissions() const;
  bool arbitrationSafe() const;

 private:
  friend class MachineSupervisor;
  void commitFaultClear();
  bool transitionAllowed(MachineState next) const;
  MachineState state_{MachineState::IDLE};
  MaterialProfile material_{MaterialProfile::NONE};
  MaterialProfile pending_material_{MaterialProfile::NONE};
  MaterialSession material_session_{MaterialSession::CLEAN};
};
