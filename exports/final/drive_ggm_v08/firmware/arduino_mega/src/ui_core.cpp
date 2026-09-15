#include "ui_core.h"

UiIntent UiController::update(const UiEvent &e, MachineState phase,
                              MaterialSession session, bool fault_latched) {
  if (fault_latched || phase == MachineState::FAULT || phase == MachineState::ESTOP) {
    screen_ = UiScreen::FAULT;
    return e.confirm_pressed ? UiIntent::CLEAR_FAULT : UiIntent::NONE;
  }
  if (e.pause_pressed) return UiIntent::PAUSE;
  if (session == MaterialSession::PURGE_PREHEAT_REQUIRED || session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED ||
      session == MaterialSession::PURGE_RUNNING || session == MaterialSession::SCREEN_CLEAN_REQUIRED ||
      session == MaterialSession::HOPPER_CLEAN_REQUIRED || session == MaterialSession::TEMPERATURE_TRANSITION_REQUIRED ||
      session == MaterialSession::FINAL_CONFIRM_REQUIRED) {
    screen_ = UiScreen::MATERIAL_CHANGE;
    if (e.back_pressed) return UiIntent::BACK;
    if (session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED && e.start_pressed)
      return UiIntent::APPROVE_PURGE_FEED;
    return e.confirm_pressed ? UiIntent::CONFIRM : UiIntent::NONE;
  }
  if (phase != MachineState::IDLE) {
    screen_ = UiScreen::RUN;
    return UiIntent::NONE;
  }
  if (e.back_pressed) {
    screen_ = UiScreen::HOME;
    selection_ = 0;
    return UiIntent::BACK;
  }
  if (e.encoder_delta != 0) selection_ = static_cast<uint8_t>((selection_ + (e.encoder_delta > 0 ? 1 : 5)) % 6);
  if (selection_ == 4) screen_ = UiScreen::CALIBRATION;
  else if (selection_ == 5) screen_ = UiScreen::MAINTENANCE;
  else screen_ = UiScreen::HOME;
  if (e.start_pressed) return selection_ == 3 ? UiIntent::START_EXTRUSION : UiIntent::START_SHREDDING;
  if (!e.confirm_pressed) return UiIntent::NONE;
  switch (selection_) {
    case 0: return UiIntent::SELECT_PLA;
    case 1: return UiIntent::SELECT_PET;
    case 2: return UiIntent::START_SHREDDING;
    case 3: return UiIntent::START_EXTRUSION;
    case 4: return UiIntent::CALIBRATE_GAUGE;
    default: return UiIntent::NONE;
  }
}
