#include "process_state.h"

namespace {
bool guardsOk(const SafetyInputs &i) {
  return i.estop_ok && i.lid_closed && i.service_guard_closed && i.thermal_chain_ok && i.driver_fault_free;
}
}

bool ProcessController::selectMaterial(MaterialProfile next) {
  if (state_ != MachineState::IDLE || next == MaterialProfile::NONE) return false;
  if (material_ != MaterialProfile::NONE && material_ != next) return false;
  material_ = next;
  pending_material_ = MaterialProfile::NONE;
  material_session_ = next == MaterialProfile::PLA ? MaterialSession::PLA_ACTIVE : MaterialSession::PET_ACTIVE;
  return true;
}

bool ProcessController::requestMaterialChange(MaterialProfile next, const SafetyInputs &i) {
  if (state_ != MachineState::IDLE || !guardsOk(i) || next == MaterialProfile::NONE || material_ == MaterialProfile::NONE || next == material_) return false;
  const auto &p = permissions();
  if (p.feeder || p.screw) return false;
  pending_material_ = next;
  material_session_ = MaterialSession::PURGE_REQUIRED;
  return true;
}

bool ProcessController::acknowledgeMaterialStep(MaterialSession expected, bool explicit_confirmation) {
  if (state_ != MachineState::IDLE || material_session_ != expected || !explicit_confirmation) return false;
  switch (material_session_) {
    case MaterialSession::PURGE_REQUIRED: material_session_ = MaterialSession::SCREEN_CLEAN_REQUIRED; return true;
    case MaterialSession::SCREEN_CLEAN_REQUIRED: material_session_ = MaterialSession::HOPPER_CLEAN_REQUIRED; return true;
    case MaterialSession::HOPPER_CLEAN_REQUIRED: material_session_ = MaterialSession::TEMPERATURE_TRANSITION_REQUIRED; return true;
    case MaterialSession::TEMPERATURE_TRANSITION_REQUIRED: material_session_ = MaterialSession::FINAL_CONFIRM_REQUIRED; return true;
    case MaterialSession::FINAL_CONFIRM_REQUIRED:
      material_ = pending_material_;
      pending_material_ = MaterialProfile::NONE;
      material_session_ = material_ == MaterialProfile::PLA ? MaterialSession::PLA_ACTIVE : MaterialSession::PET_ACTIVE;
      return true;
    default: return false;
  }
}

bool ProcessController::materialReady() const {
  return (material_ == MaterialProfile::PLA && material_session_ == MaterialSession::PLA_ACTIVE) ||
         (material_ == MaterialProfile::PET && material_session_ == MaterialSession::PET_ACTIVE);
}

bool ProcessController::transitionAllowed(MachineState next) const {
  switch (state_) {
    case MachineState::IDLE: return next == MachineState::SHREDDING || next == MachineState::PREHEATING || next == MachineState::FAULT || next == MachineState::ESTOP;
    case MachineState::SHREDDING: return next == MachineState::IDLE || next == MachineState::PREHEATING || next == MachineState::FAULT || next == MachineState::ESTOP;
    case MachineState::PREHEATING: return next == MachineState::EXTRUSION || next == MachineState::COOLDOWN || next == MachineState::FAULT || next == MachineState::ESTOP;
    case MachineState::EXTRUSION: return next == MachineState::COOLDOWN || next == MachineState::FAULT || next == MachineState::ESTOP;
    case MachineState::COOLDOWN: return next == MachineState::IDLE || next == MachineState::FAULT || next == MachineState::ESTOP;
    case MachineState::FAULT: return next == MachineState::IDLE || next == MachineState::ESTOP;
    case MachineState::ESTOP: return next == MachineState::IDLE;
  }
  return false;
}

bool ProcessController::requestState(MachineState next, const SafetyInputs &i) {
  if (!i.estop_ok) {
    state_ = MachineState::ESTOP;
    return next == MachineState::ESTOP;
  }
  if (!transitionAllowed(next) || material_ == MaterialProfile::NONE) return false;
  if ((next == MachineState::SHREDDING || next == MachineState::PREHEATING || next == MachineState::EXTRUSION) && !materialReady()) return false;
  if ((next == MachineState::SHREDDING || next == MachineState::PREHEATING || next == MachineState::EXTRUSION) && !guardsOk(i)) return false;
  if (next == MachineState::EXTRUSION && (!i.temperatures_ready || !i.gauge_valid || !i.heater_permission_feedback)) return false;
  if ((state_ == MachineState::FAULT || state_ == MachineState::ESTOP) && next == MachineState::IDLE && !i.restart_permission) return false;
  state_ = next;
  return arbitrationSafe();
}

void ProcessController::reportFault() { state_ = MachineState::FAULT; }

bool ProcessController::clearFault(const SafetyInputs &i, bool lockout) {
  if ((state_ != MachineState::FAULT && state_ != MachineState::ESTOP) || !lockout || !guardsOk(i) || !i.restart_permission) return false;
  state_ = MachineState::IDLE;
  return true;
}

const StatePermissions &ProcessController::permissions() const {
  return STATE_PERMISSIONS[static_cast<uint8_t>(state_)];
}

bool ProcessController::arbitrationSafe() const {
  const auto &p = permissions();
  return !(p.shredder && (p.screw || p.process_heaters));
}
