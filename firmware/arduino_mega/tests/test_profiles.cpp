#include <cassert>
#include <iostream>
#include "process_state.h"

int main() {
  ProcessController c;
  SafetyInputs safe{true, true, true, true, true, true, true, true, true};
  assert(c.selectMaterial(MaterialProfile::PLA));
  assert(c.requestState(MachineState::SHREDDING, safe));
  assert(c.permissions().shredder && !c.permissions().screw && !c.permissions().process_heaters);
  assert(c.arbitrationSafe());
  assert(!c.selectMaterial(MaterialProfile::PET));
  assert(c.requestState(MachineState::PREHEATING, safe));
  assert(c.permissions().process_heaters && !c.permissions().shredder && !c.permissions().screw);
  assert(c.requestState(MachineState::EXTRUSION, safe));
  assert(c.permissions().screw && c.permissions().process_heaters && !c.permissions().shredder);
  assert(c.requestState(MachineState::COOLDOWN, safe));
  assert(c.permissions().cooling && !c.permissions().screw && !c.permissions().process_heaters);
  assert(c.requestState(MachineState::IDLE, safe));
  assert(c.requestMaterialChange(MaterialProfile::PET, safe));
  assert(c.materialSession() == MaterialSession::PURGE_REQUIRED);
  assert(!c.requestState(MachineState::PREHEATING, safe));
  assert(!c.acknowledgeMaterialStep(MaterialSession::PURGE_REQUIRED, false));
  assert(c.acknowledgeMaterialStep(MaterialSession::PURGE_REQUIRED, true));
  assert(c.acknowledgeMaterialStep(MaterialSession::SCREEN_CLEAN_REQUIRED, true));
  assert(c.acknowledgeMaterialStep(MaterialSession::HOPPER_CLEAN_REQUIRED, true));
  assert(c.acknowledgeMaterialStep(MaterialSession::TEMPERATURE_TRANSITION_REQUIRED, true));
  assert(c.acknowledgeMaterialStep(MaterialSession::FINAL_CONFIRM_REQUIRED, true));
  assert(c.material() == MaterialProfile::PET && c.materialReady());
  c.reportFault();
  assert(c.state() == MachineState::FAULT);
  assert(!c.clearFault(safe, false));
  assert(c.clearFault(safe, true));
  SafetyInputs unsafe{true, false, true, true, true, true, true, true, true};
  assert(!c.requestState(MachineState::SHREDDING, unsafe));
  assert(PLA_PROFILE.zone_c[2] < PET_PROFILE.zone_c[2]);
  assert(PLA_PROFILE.shredder_rpm == 32 && PET_PROFILE.shredder_rpm == 24);
  assert(PLA_PROFILE.screw_rpm == 16.0f);
  assert(PET_PROFILE.screw_rpm == 18.0f);
  assert(PLA_PROFILE.fan_percent == 100 && PET_PROFILE.fan_percent == 100);
  assert(!PLA_PROFILE.external_predry_qualified);
  assert(!PET_PROFILE.external_predry_qualified);
  assert(INPUT_MECHANICAL_FUSE_NM < PHASE_DRIVETRAIN_ALLOWABLE_NM);
  assert(PHASE_DRIVETRAIN_ALLOWABLE_NM < SHAFT_CUTTER_ALLOWABLE_NM);
  std::cout << "PROCESS_PHASE_MATERIAL_SESSION_ARBITRATION_OK\n";
}
