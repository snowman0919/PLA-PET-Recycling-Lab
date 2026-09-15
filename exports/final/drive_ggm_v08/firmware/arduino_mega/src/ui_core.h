#pragma once

#include <stdint.h>

#include "process_state.h"

enum class UiScreen : uint8_t { HOME, RUN, MATERIAL_CHANGE, CALIBRATION, MAINTENANCE, FAULT };
enum class UiIntent : uint8_t { NONE, SELECT_PLA, SELECT_PET, START_SHREDDING, START_EXTRUSION, APPROVE_PURGE_FEED, PAUSE, BACK, CONFIRM, CALIBRATE_GAUGE, CLEAR_FAULT };

struct UiEvent {
  int8_t encoder_delta;
  bool start_pressed;
  bool pause_pressed;
  bool back_pressed;
  bool confirm_pressed;
};

class UiController {
 public:
  UiIntent update(const UiEvent &event, MachineState phase, MaterialSession material_session, bool fault_latched);
  UiScreen screen() const { return screen_; }
  uint8_t selection() const { return selection_; }

 private:
  UiScreen screen_{UiScreen::HOME};
  uint8_t selection_{0};
};
