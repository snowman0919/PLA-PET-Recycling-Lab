#include <cassert>
#include <iostream>
#include "process_state.h"

int main() {
  ProcessController c;
  SafetyInputs safe{true, true, true, true, true};
  assert(c.selectMaterial(MaterialProfile::PLA));
  assert(c.start(safe));
  assert(c.materialLocked());
  assert(!c.selectMaterial(MaterialProfile::PET));
  c.requestMaterialChange(MaterialProfile::PET);
  assert(c.state() == ProcessState::PURGE_REQUIRED);
  assert(!c.confirmPurge(79));
  assert(c.confirmPurge(PLA_PROFILE.purge_grams));
  assert(c.confirmScreenClean());
  assert(c.confirmHopperClean());
  assert(c.confirmMaterialChange());
  assert(c.material() == MaterialProfile::PET);
  assert(c.start(safe));
  c.reportJam(); c.reportJam();
  assert(c.state() == ProcessState::RUNNING);
  c.reportJam();
  assert(c.state() == ProcessState::FAULT_LATCHED);
  c.clearFault(false); assert(c.state() == ProcessState::FAULT_LATCHED);
  c.clearFault(true); assert(c.state() == ProcessState::READY);
  SafetyInputs unsafe{true, false, true, true, true};
  assert(!c.start(unsafe));
  assert(PLA_PROFILE.zone_c[2] < PET_PROFILE.zone_c[2]);
  std::cout << "MATERIAL_PROFILE_STATE_MACHINE_OK\n";
}
