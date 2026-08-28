#include "process_state.h"

bool ProcessController::selectMaterial(MaterialProfile next) {
  if (locked_ || state_ == ProcessState::RUNNING || next == MaterialProfile::NONE) return false;
  material_ = next; state_ = ProcessState::READY; return true;
}

bool ProcessController::start(const SafetyInputs &i) {
  if (state_ != ProcessState::READY && state_ != ProcessState::PAUSED) return false;
  if (material_ == MaterialProfile::NONE || !i.estop_ok || !i.lid_closed ||
      !i.service_guard_closed || !i.thermal_chain_ok || !i.predry_confirmed) return false;
  locked_ = true; state_ = ProcessState::RUNNING; return true;
}

void ProcessController::pause() {
  if (state_ == ProcessState::RUNNING) state_ = ProcessState::PAUSED;
}

void ProcessController::requestMaterialChange(MaterialProfile next) {
  if (next == MaterialProfile::NONE || next == material_) return;
  pending_ = next; locked_ = true; state_ = ProcessState::PURGE_REQUIRED;
}

bool ProcessController::confirmPurge(uint16_t grams) {
  if (state_ != ProcessState::PURGE_REQUIRED || grams < profileFor(material_).purge_grams) return false;
  state_ = ProcessState::SCREEN_CLEAN_REQUIRED; return true;
}

bool ProcessController::confirmScreenClean() {
  if (state_ != ProcessState::SCREEN_CLEAN_REQUIRED) return false;
  state_ = ProcessState::HOPPER_CLEAN_REQUIRED; return true;
}

bool ProcessController::confirmHopperClean() {
  if (state_ != ProcessState::HOPPER_CLEAN_REQUIRED) return false;
  state_ = ProcessState::CHANGE_CONFIRM_REQUIRED; return true;
}

bool ProcessController::confirmMaterialChange() {
  if (state_ != ProcessState::CHANGE_CONFIRM_REQUIRED || pending_ == MaterialProfile::NONE) return false;
  material_ = pending_; pending_ = MaterialProfile::NONE; locked_ = false; state_ = ProcessState::READY; return true;
}

void ProcessController::reportJam() {
  if (++jam_retries_ >= profileFor(material_).retry_count) state_ = ProcessState::FAULT_LATCHED;
}

void ProcessController::clearFault(bool lockout) {
  if (state_ == ProcessState::FAULT_LATCHED && lockout) { jam_retries_ = 0; locked_ = false; state_ = ProcessState::READY; }
}
