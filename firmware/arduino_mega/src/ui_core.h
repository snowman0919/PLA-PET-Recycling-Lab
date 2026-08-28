#pragma once

#include <stddef.h>
#include <stdint.h>

#include "control_core.h"

namespace recycler {

enum class UiPage : uint8_t {
  STARTUP_ACK,
  STATUS,
  MATERIAL,
  COLOR,
  BATCH,
  THERMAL_DRIVE,
  QUALITY,
  PRODUCTION,
  CALIBRATION,
  MAINTENANCE,
  FAULT,
};

enum class UiMaterial : uint8_t {
  UNKNOWN,
  AUTO,
  PLA,
  PET,
  REJECT,
};

enum class UiSeverity : uint8_t {
  NORMAL,
  CAUTION,
  STOP,
};

enum class UiEvent : uint8_t {
  NONE,
  ROTATE_CCW,
  ROTATE_CW,
  PUSH,
  BACK,
};

enum class UiActionType : uint8_t {
  NONE,
  ACK_STARTUP,
  SET_MATERIAL,
  SET_COLOR_BIN,
  SELECT_BATCH,
  REQUEST_CALIBRATION,
  REQUEST_MAINTENANCE,
};

struct UiAction {
  UiActionType type;
  int16_t value;
};

struct UiTelemetry {
  SafetyState state;
  Phase phase;
  uint32_t faults;
  UiMaterial selected_material;
  uint8_t color_bin;
  uint16_t batch_number;
  float temperatures_c[6];
  float motor_current_a[3];
  uint8_t hopper_fill_pct;
  float diameter_x_mm;
  float diameter_y_mm;
  float produced_length_m;
  float produced_weight_g;
  uint16_t eta_minutes;
  bool diameter_gauge_qualified;
  bool purge_required;
};

constexpr uint8_t kUiLineCount = 8;
constexpr uint8_t kUiLineBytes = 32;

struct UiFrame {
  UiPage page;
  UiSeverity severity;
  bool editing;
  char title[24];
  char lines[kUiLineCount][kUiLineBytes];
};

struct UiInputSample {
  uint32_t now_ms;
  bool rotary_a_high;
  bool rotary_b_high;
  bool push_pressed;
  bool back_pressed;
};

class UiInputFilter {
 public:
  UiInputFilter();
  UiEvent update(const UiInputSample& sample);

 private:
  uint8_t previous_ab_;
  int8_t rotary_accumulator_;
  bool initialized_;
  bool raw_push_;
  bool stable_push_;
  bool raw_back_;
  bool stable_back_;
  uint32_t push_changed_ms_;
  uint32_t back_changed_ms_;
};

class UiCore {
 public:
  UiCore();
  UiAction handle(UiEvent event, const UiTelemetry& telemetry);
  UiFrame compose(const UiTelemetry& telemetry) const;
  UiPage page(const UiTelemetry& telemetry) const;
  bool run_permitted(Phase requested_phase, const UiTelemetry& telemetry) const;
  bool startup_acknowledged() const { return startup_acknowledged_; }

 private:
  bool maintenance_allowed(const UiTelemetry& telemetry) const;
  UiPage visible_page(const UiTelemetry& telemetry) const;
  void rotate_page(bool clockwise);

  UiPage page_;
  bool editing_;
  bool startup_acknowledged_;
  int16_t edit_value_;
};

const char* ui_material_name(UiMaterial material);
const char* ui_fault_name(uint32_t faults);

}  // namespace recycler
