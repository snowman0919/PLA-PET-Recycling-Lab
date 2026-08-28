#include "ui_core.h"

#include <math.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>

namespace recycler {

namespace {
constexpr UiPage kPages[] = {
    UiPage::STATUS,       UiPage::MATERIAL,    UiPage::COLOR,
    UiPage::BATCH,        UiPage::THERMAL_DRIVE, UiPage::QUALITY,
    UiPage::PRODUCTION,
    UiPage::CALIBRATION,  UiPage::MAINTENANCE,
};
constexpr uint8_t kPageCount = sizeof(kPages) / sizeof(kPages[0]);

const char* state_name(SafetyState state) {
  switch (state) {
    case SafetyState::SAFE_OFF: return "SAFE OFF";
    case SafetyState::SELF_TEST: return "SELF TEST";
    case SafetyState::READY: return "READY";
    case SafetyState::RUNNING: return "RUNNING";
    case SafetyState::PAUSED: return "PAUSED";
    case SafetyState::FAULT_LATCHED: return "FAULT";
    case SafetyState::ESTOP_LATCHED: return "E-STOP";
  }
  return "UNKNOWN";
}

const char* phase_name(Phase phase) {
  switch (phase) {
    case Phase::IDLE: return "IDLE";
    case Phase::SHRED: return "2-STAGE SHRED";
    case Phase::DRY_PREHEAT: return "DRY/PREHEAT";
    case Phase::EXTRUDE_SPOOL: return "EXTRUDE/SPOOL";
    case Phase::COOLDOWN_CLEAN: return "COOLDOWN/CLEAN";
  }
  return "UNKNOWN";
}

void clear_frame(UiFrame* frame) {
  memset(frame->title, 0, sizeof(frame->title));
  memset(frame->lines, 0, sizeof(frame->lines));
}

void set_line(UiFrame* frame, uint8_t row, const char* text) {
  if (row >= kUiLineCount) return;
  snprintf(frame->lines[row], kUiLineBytes, "%s", text);
}

int32_t fixed_100(float value) {
  if (!isfinite(value) || value > 999999.0F || value < -999999.0F)
    return INT32_MIN;
  return static_cast<int32_t>(value * 100.0F +
                              (value >= 0.0F ? 0.5F : -0.5F));
}

void format_fixed(char* out, size_t capacity, const char* label, float value,
                  const char* unit) {
  const int32_t scaled = fixed_100(value);
  if (scaled == INT32_MIN) {
    snprintf(out, capacity, "%s -- %s", label, unit);
    return;
  }
  const int32_t magnitude = scaled < 0 ? -scaled : scaled;
  snprintf(out, capacity, "%s %s%ld.%02ld %s", label,
           scaled < 0 ? "-" : "", static_cast<long>(magnitude / 100),
           static_cast<long>(magnitude % 100), unit);
}

void format_pair(char* out, size_t capacity, const char* label,
                 float first, float second, const char* unit) {
  const int32_t a = fixed_100(first);
  const int32_t b = fixed_100(second);
  if (a == INT32_MIN || b == INT32_MIN) {
    snprintf(out, capacity, "%s --/-- %s", label, unit);
    return;
  }
  const int32_t magnitude_a = a < 0 ? -a : a;
  const int32_t magnitude_b = b < 0 ? -b : b;
  snprintf(out, capacity, "%s %s%ld.%02ld/%s%ld.%02ld %s", label,
           a < 0 ? "-" : "", static_cast<long>(magnitude_a / 100),
           static_cast<long>(magnitude_a % 100), b < 0 ? "-" : "",
           static_cast<long>(magnitude_b / 100),
           static_cast<long>(magnitude_b % 100), unit);
}

uint8_t page_index(UiPage page) {
  for (uint8_t i = 0; i < kPageCount; ++i)
    if (kPages[i] == page) return i;
  return 0;
}
}  // namespace

UiInputFilter::UiInputFilter()
    : previous_ab_(0),
      rotary_accumulator_(0),
      initialized_(false),
      raw_push_(false),
      stable_push_(false),
      raw_back_(false),
      stable_back_(false),
      push_changed_ms_(0),
      back_changed_ms_(0) {}

UiEvent UiInputFilter::update(const UiInputSample& sample) {
  constexpr uint32_t kDebounceMs = 40;
  constexpr int8_t transition_delta[16] = {
      0, -1, 1, 0, 1, 0, 0, -1,
      -1, 0, 0, 1, 0, 1, -1, 0,
  };
  const uint8_t current_ab = static_cast<uint8_t>(
      (sample.rotary_a_high ? 2U : 0U) | (sample.rotary_b_high ? 1U : 0U));
  if (!initialized_) {
    previous_ab_ = current_ab;
    raw_push_ = stable_push_ = sample.push_pressed;
    raw_back_ = stable_back_ = sample.back_pressed;
    push_changed_ms_ = back_changed_ms_ = sample.now_ms;
    initialized_ = true;
    return UiEvent::NONE;
  }

  rotary_accumulator_ += transition_delta[(previous_ab_ << 2U) | current_ab];
  previous_ab_ = current_ab;
  UiEvent rotary_event = UiEvent::NONE;
  if (rotary_accumulator_ >= 4) {
    rotary_accumulator_ = 0;
    rotary_event = UiEvent::ROTATE_CW;
  } else if (rotary_accumulator_ <= -4) {
    rotary_accumulator_ = 0;
    rotary_event = UiEvent::ROTATE_CCW;
  }

  if (sample.push_pressed != raw_push_) {
    raw_push_ = sample.push_pressed;
    push_changed_ms_ = sample.now_ms;
  }
  if (sample.back_pressed != raw_back_) {
    raw_back_ = sample.back_pressed;
    back_changed_ms_ = sample.now_ms;
  }
  if (raw_back_ != stable_back_ && sample.now_ms - back_changed_ms_ >= kDebounceMs) {
    stable_back_ = raw_back_;
    if (stable_back_) return UiEvent::BACK;
  }
  if (raw_push_ != stable_push_ && sample.now_ms - push_changed_ms_ >= kDebounceMs) {
    stable_push_ = raw_push_;
    if (stable_push_) return UiEvent::PUSH;
  }
  return rotary_event;
}

const char* ui_material_name(UiMaterial material) {
  switch (material) {
    case UiMaterial::UNKNOWN: return "UNKNOWN";
    case UiMaterial::AUTO: return "AUTO";
    case UiMaterial::PLA: return "PLA";
    case UiMaterial::PET: return "PET";
    case UiMaterial::REJECT: return "REJECT";
  }
  return "UNKNOWN";
}

const char* ui_fault_name(uint32_t faults) {
  if (faults & FAULT_ESTOP) return "E-STOP: inspect/reset";
  if (faults & FAULT_CONTACTOR) return "Contactor feedback";
  if (faults & FAULT_THERMAL_CHAIN) return "Thermal chain open";
  if (faults & FAULT_PRESSURE) return "Melt pressure trip";
  if (faults & FAULT_LID) return "Shredder lid open";
  if (faults & FAULT_SERVICE) return "Service guard open";
  if (faults & FAULT_SENSOR) return "Sensor invalid";
  if (faults & FAULT_AIRFLOW) return "Airflow missing";
  if (faults & FAULT_HEARTBEAT) return "Service link timeout";
  if (faults & FAULT_JAM) return "Jam retries exhausted";
  if (faults & FAULT_POWER_BUDGET) return "Power budget fault";
  if (faults & FAULT_PROTOCOL) return "Protocol fault";
  return "No decoded fault";
}

UiCore::UiCore()
    : page_(UiPage::STATUS),
      editing_(false),
      startup_acknowledged_(false),
      edit_value_(0) {}

bool UiCore::maintenance_allowed(const UiTelemetry& telemetry) const {
  return telemetry.state == SafetyState::SAFE_OFF ||
         telemetry.state == SafetyState::PAUSED;
}

UiPage UiCore::visible_page(const UiTelemetry& telemetry) const {
  if (telemetry.faults != FAULT_NONE ||
      telemetry.state == SafetyState::FAULT_LATCHED ||
      telemetry.state == SafetyState::ESTOP_LATCHED)
    return UiPage::FAULT;
  if (!startup_acknowledged_) return UiPage::STARTUP_ACK;
  return page_;
}

UiPage UiCore::page(const UiTelemetry& telemetry) const {
  return visible_page(telemetry);
}

bool UiCore::run_permitted(Phase requested_phase,
                           const UiTelemetry& telemetry) const {
  if (!startup_acknowledged_ || telemetry.faults != FAULT_NONE) return false;
  if (requested_phase == Phase::IDLE) return false;
  if (requested_phase == Phase::EXTRUDE_SPOOL && telemetry.purge_required)
    return false;
  return true;
}

void UiCore::rotate_page(bool clockwise) {
  uint8_t index = page_index(page_);
  index = clockwise ? static_cast<uint8_t>((index + 1U) % kPageCount)
                    : static_cast<uint8_t>((index + kPageCount - 1U) % kPageCount);
  page_ = kPages[index];
}

UiAction UiCore::handle(UiEvent event, const UiTelemetry& telemetry) {
  const UiPage visible = visible_page(telemetry);
  if (visible == UiPage::FAULT) {
    editing_ = false;
    return {UiActionType::NONE, 0};
  }
  if (visible == UiPage::STARTUP_ACK) {
    if (event == UiEvent::PUSH &&
        (telemetry.state == SafetyState::SAFE_OFF ||
         telemetry.state == SafetyState::READY)) {
      startup_acknowledged_ = true;
      return {UiActionType::ACK_STARTUP, 1};
    }
    return {UiActionType::NONE, 0};
  }
  if (event == UiEvent::BACK) {
    if (editing_) {
      editing_ = false;
    } else {
      page_ = UiPage::STATUS;
    }
    return {UiActionType::NONE, 0};
  }
  if (event == UiEvent::ROTATE_CCW || event == UiEvent::ROTATE_CW) {
    const int16_t step = event == UiEvent::ROTATE_CW ? 1 : -1;
    if (!editing_) {
      rotate_page(step > 0);
    } else if (page_ == UiPage::MATERIAL) {
      edit_value_ += step;
      if (edit_value_ < static_cast<int16_t>(UiMaterial::PLA))
        edit_value_ = static_cast<int16_t>(UiMaterial::PET);
      if (edit_value_ > static_cast<int16_t>(UiMaterial::PET))
        edit_value_ = static_cast<int16_t>(UiMaterial::PLA);
    } else if (page_ == UiPage::COLOR) {
      edit_value_ += step;
      if (edit_value_ < 0) edit_value_ = 7;
      if (edit_value_ > 7) edit_value_ = 0;
    } else if (page_ == UiPage::BATCH) {
      edit_value_ += step;
      if (edit_value_ < 1) edit_value_ = 999;
      if (edit_value_ > 999) edit_value_ = 1;
    }
    return {UiActionType::NONE, 0};
  }
  if (event != UiEvent::PUSH) return {UiActionType::NONE, 0};

  if (page_ == UiPage::MATERIAL) {
    if (!editing_) {
      editing_ = true;
      edit_value_ = telemetry.selected_material == UiMaterial::PLA ||
                            telemetry.selected_material == UiMaterial::PET
                        ? static_cast<int16_t>(telemetry.selected_material)
                        : static_cast<int16_t>(UiMaterial::PLA);
      return {UiActionType::NONE, 0};
    }
    editing_ = false;
    return {UiActionType::SET_MATERIAL, edit_value_};
  }
  if (page_ == UiPage::COLOR) {
    if (!editing_) {
      editing_ = true;
      edit_value_ = telemetry.color_bin <= 7 ? telemetry.color_bin : 7;
      return {UiActionType::NONE, 0};
    }
    editing_ = false;
    return {UiActionType::SET_COLOR_BIN, edit_value_};
  }
  if (page_ == UiPage::BATCH) {
    if (!editing_) {
      editing_ = true;
      edit_value_ = telemetry.batch_number > 0 && telemetry.batch_number <= 999
                        ? telemetry.batch_number
                        : 1;
      return {UiActionType::NONE, 0};
    }
    editing_ = false;
    return {UiActionType::SELECT_BATCH, edit_value_};
  }
  if (page_ == UiPage::CALIBRATION && maintenance_allowed(telemetry))
    return {UiActionType::REQUEST_CALIBRATION, 1};
  if (page_ == UiPage::MAINTENANCE && maintenance_allowed(telemetry))
    return {UiActionType::REQUEST_MAINTENANCE, 1};
  return {UiActionType::NONE, 0};
}

UiFrame UiCore::compose(const UiTelemetry& telemetry) const {
  UiFrame frame{visible_page(telemetry), UiSeverity::NORMAL, editing_, {}, {}};
  clear_frame(&frame);
  char line[kUiLineBytes];
  switch (frame.page) {
    case UiPage::STARTUP_ACK:
      frame.severity = UiSeverity::CAUTION;
      snprintf(frame.title, sizeof(frame.title), "STARTUP SAFETY");
      set_line(&frame, 0, "Ventilate indoor workspace");
      set_line(&frame, 1, "PLA + clean/dry PET only");
      set_line(&frame, 2, "NO PVC/ABS/TPU/unknown");
      set_line(&frame, 3, "Remove labels/metal/food");
      set_line(&frame, 4, "Guards + bins installed");
      set_line(&frame, 6, "PUSH = acknowledge");
      set_line(&frame, 7, "E-stop remains hardware");
      break;
    case UiPage::STATUS:
      snprintf(frame.title, sizeof(frame.title), "STATUS");
      snprintf(line, sizeof(line), "%s | %s", state_name(telemetry.state),
               phase_name(telemetry.phase));
      set_line(&frame, 0, line);
      snprintf(line, sizeof(line), "Manual material %s",
               ui_material_name(telemetry.selected_material));
      set_line(&frame, 1, line);
      snprintf(line, sizeof(line), "Color batch %u",
               static_cast<unsigned>(telemetry.color_bin));
      set_line(&frame, 2, line);
      snprintf(line, sizeof(line), "Batch %u | hopper %u%%",
               static_cast<unsigned>(telemetry.batch_number),
               static_cast<unsigned>(telemetry.hopper_fill_pct));
      set_line(&frame, 3, line);
      set_line(&frame, 5, "Manual inspection required");
      if (telemetry.purge_required) set_line(&frame, 6, "PURGE REQUIRED before run");
      set_line(&frame, 7, "START requires hard button");
      break;
    case UiPage::MATERIAL:
      snprintf(frame.title, sizeof(frame.title), "MATERIAL OVERRIDE");
      snprintf(line, sizeof(line), "Manual PLA/PET selection");
      set_line(&frame, 0, line);
      snprintf(line, sizeof(line), "%s %s", editing_ ? "Choose" : "Selected",
               ui_material_name(editing_ ? static_cast<UiMaterial>(edit_value_)
                                         : telemetry.selected_material));
      set_line(&frame, 2, line);
      set_line(&frame, 4, "Unknown/TPU => REJECT");
      set_line(&frame, 6, editing_ ? "PUSH commit / BACK cancel"
                                  : "PUSH edit (does not START)");
      break;
    case UiPage::COLOR:
      snprintf(frame.title, sizeof(frame.title), "COLOR BIN");
      snprintf(line, sizeof(line), "Color bin %d (7=Reject)",
               editing_ ? static_cast<int>(edit_value_) : telemetry.color_bin);
      set_line(&frame, 0, line);
      set_line(&frame, 1, "Manual batch label required");
      set_line(&frame, 6, editing_ ? "PUSH commit / BACK cancel"
                                  : "PUSH edit color mapping");
      break;
    case UiPage::BATCH:
      snprintf(frame.title, sizeof(frame.title), "BATCH SELECT");
      snprintf(line, sizeof(line), "Batch %d",
               editing_ ? static_cast<int>(edit_value_) : telemetry.batch_number);
      set_line(&frame, 0, line);
      set_line(&frame, 2, editing_ ? "Rotate to choose batch"
                                  : "PUSH edit batch");
      set_line(&frame, 6, editing_ ? "PUSH commit / BACK cancel"
                                  : "Selection cannot START");
      break;
    case UiPage::THERMAL_DRIVE:
      snprintf(frame.title, sizeof(frame.title), "HEATERS + MOTOR LOAD");
      format_pair(line, sizeof(line), "Z1/Z2", telemetry.temperatures_c[0],
                  telemetry.temperatures_c[1], "C");
      set_line(&frame, 0, line);
      format_pair(line, sizeof(line), "Z3/Die", telemetry.temperatures_c[2],
                  telemetry.temperatures_c[3], "C");
      set_line(&frame, 1, line);
      format_pair(line, sizeof(line), "Dry/Air", telemetry.temperatures_c[4],
                  telemetry.temperatures_c[5], "C");
      set_line(&frame, 2, line);
      format_pair(line, sizeof(line), "I shred/ext", telemetry.motor_current_a[0],
                  telemetry.motor_current_a[1], "A");
      set_line(&frame, 4, line);
      format_fixed(line, sizeof(line), "I form", telemetry.motor_current_a[2], "A");
      set_line(&frame, 5, line);
      break;
    case UiPage::QUALITY:
      snprintf(frame.title, sizeof(frame.title), "DIAMETER X/Y");
      format_pair(line, sizeof(line), "Gauge", telemetry.diameter_x_mm,
                  telemetry.diameter_y_mm, "mm");
      set_line(&frame, 0, line);
      set_line(&frame, 2, telemetry.diameter_gauge_qualified
                              ? "Gauge qualified"
                              : "Gauge NOT qualified");
      set_line(&frame, 3, "Target 1.70..1.80 mm");
      set_line(&frame, 4, "Ovality <= 0.05 mm");
      break;
    case UiPage::PRODUCTION:
      snprintf(frame.title, sizeof(frame.title), "PRODUCTION");
      format_fixed(line, sizeof(line), "Length", telemetry.produced_length_m, "m");
      set_line(&frame, 0, line);
      format_fixed(line, sizeof(line), "Weight", telemetry.produced_weight_g, "g");
      set_line(&frame, 1, line);
      snprintf(line, sizeof(line), "ETA %u min",
               static_cast<unsigned>(telemetry.eta_minutes));
      set_line(&frame, 2, line);
      snprintf(line, sizeof(line), "Batch %u",
               static_cast<unsigned>(telemetry.batch_number));
      set_line(&frame, 3, line);
      break;
    case UiPage::CALIBRATION:
      snprintf(frame.title, sizeof(frame.title), "CALIBRATION");
      set_line(&frame, 0, "Color / gauge / load / feed");
      set_line(&frame, 2, maintenance_allowed(telemetry)
                              ? "PUSH request wizard"
                              : "Pause or SAFE OFF first");
      set_line(&frame, 4, "Cannot unlock qualification");
      break;
    case UiPage::MAINTENANCE:
      snprintf(frame.title, sizeof(frame.title), "MAINTENANCE");
      set_line(&frame, 0, "Lockout before access");
      set_line(&frame, 1, "No guarded motion override");
      set_line(&frame, 3, maintenance_allowed(telemetry)
                              ? "PUSH request checklist"
                              : "Pause or SAFE OFF first");
      break;
    case UiPage::FAULT:
      frame.severity = UiSeverity::STOP;
      snprintf(frame.title, sizeof(frame.title), "STOP / FAULT");
      set_line(&frame, 0, ui_fault_name(telemetry.faults));
      snprintf(line, sizeof(line), "Fault mask 0x%08lX",
               static_cast<unsigned long>(telemetry.faults));
      set_line(&frame, 1, line);
      set_line(&frame, 3, "Use physical E-stop if risk");
      set_line(&frame, 4, "Inspect root cause + isolate");
      set_line(&frame, 6, "BACK cannot clear fault");
      set_line(&frame, 7, "RESET requires hard button");
      break;
  }
  return frame;
}

}  // namespace recycler
