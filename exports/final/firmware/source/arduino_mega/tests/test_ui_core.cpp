#include <cassert>
#include <iostream>

#include "ui_core.h"

int main() {
  UiController ui;
  UiEvent confirm{0, false, false, false, true};
  assert(ui.update(confirm, MachineState::IDLE, MaterialSession::CLEAN, false) == UiIntent::SELECT_PLA);
  UiEvent next{1, false, false, false, false};
  ui.update(next, MachineState::IDLE, MaterialSession::PLA_ACTIVE, false);
  assert(ui.update(confirm, MachineState::IDLE, MaterialSession::PLA_ACTIVE, false) == UiIntent::SELECT_PET);
  assert(ui.update(confirm, MachineState::IDLE, MaterialSession::PURGE_PREHEAT_REQUIRED, false) == UiIntent::CONFIRM);
  UiEvent start{0, true, false, false, false};
  assert(ui.update(start, MachineState::MAINTENANCE_PURGE,
                   MaterialSession::PURGE_READY_CONFIRM_REQUIRED, false) == UiIntent::APPROVE_PURGE_FEED);
  assert(ui.update(confirm, MachineState::MAINTENANCE_PURGE,
                   MaterialSession::PURGE_READY_CONFIRM_REQUIRED, false) == UiIntent::CONFIRM);
  UiEvent pause{0, false, true, false, false};
  assert(ui.update(pause, MachineState::EXTRUSION, MaterialSession::PLA_ACTIVE, false) == UiIntent::PAUSE);
  assert(ui.update(pause, MachineState::IDLE,
                   MaterialSession::PURGE_PREHEAT_REQUIRED, false) == UiIntent::PAUSE);
  assert(ui.update(pause, MachineState::MAINTENANCE_PURGE,
                   MaterialSession::PURGE_RUNNING, false) == UiIntent::PAUSE);
  UiEvent back{0, false, false, true, false};
  assert(ui.update(back, MachineState::MAINTENANCE_PURGE,
                   MaterialSession::PURGE_RUNNING, false) == UiIntent::BACK);
  assert(ui.update(confirm, MachineState::FAULT, MaterialSession::PLA_ACTIVE, true) == UiIntent::CLEAR_FAULT);
  std::cout << "UI_NAVIGATION_MATERIAL_WIZARD_FAULT_SEMANTICS_OK\n";
}
