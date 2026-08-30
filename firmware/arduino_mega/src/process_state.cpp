#include "process_state.h"

namespace {
bool guardsOk(const SafetyInputs &i) {
  return i.estop_ok && i.lid_closed && i.service_guard_closed && i.thermal_chain_ok;
}
}

bool ProcessController::selectMaterial(MaterialProfile next) {
  if (state_ != MachineState::IDLE || next == MaterialProfile::NONE) return false;
  material_ = next;
  return true;
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
  if ((next == MachineState::SHREDDING || next == MachineState::PREHEATING || next == MachineState::EXTRUSION) && !guardsOk(i)) return false;
  if (next == MachineState::EXTRUSION && (!i.temperatures_ready || !i.gauge_valid)) return false;
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
