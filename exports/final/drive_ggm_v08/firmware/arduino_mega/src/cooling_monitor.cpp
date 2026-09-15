#include "cooling_monitor.h"

namespace {
constexpr uint8_t COMMAND_THRESHOLD_PWM = 102;
constexpr float MIN_RUNNING_RPM = 300.0f;
constexpr uint32_t FEEDBACK_DWELL_MS = 1500;
}

void CoolingMonitor::reset() {
  invalid_since_ms_ = 0;
  off_feedback_since_ms_ = 0;
}

CoolingMonitorOutput CoolingMonitor::update(uint8_t command, float fan1_rpm, bool fan1_valid,
                                            float fan2_rpm, bool fan2_valid, uint32_t now_ms) {
  const bool commanded = command >= COMMAND_THRESHOLD_PWM;
  const bool fan1_running = fan1_valid && fan1_rpm >= MIN_RUNNING_RPM;
  const bool fan2_running = fan2_valid && fan2_rpm >= MIN_RUNNING_RPM;
  uint8_t bits = COOLING_FAULT_NONE;
  if (commanded && !fan1_running) bits |= COOLING_FAN1_STOPPED;
  if (commanded && !fan2_running) bits |= COOLING_FAN2_STOPPED;
  if (commanded && bits != COOLING_FAULT_NONE) {
    if (invalid_since_ms_ == 0) invalid_since_ms_ = now_ms == 0 ? 1 : now_ms;
  } else {
    invalid_since_ms_ = 0;
  }
  const bool feedback_while_off = !commanded && (fan1_rpm >= MIN_RUNNING_RPM || fan2_rpm >= MIN_RUNNING_RPM);
  if (feedback_while_off) {
    if (off_feedback_since_ms_ == 0) off_feedback_since_ms_ = now_ms == 0 ? 1 : now_ms;
    if (now_ms - off_feedback_since_ms_ >= FEEDBACK_DWELL_MS) bits |= COOLING_IMPLAUSIBLE_WHILE_OFF;
  } else {
    off_feedback_since_ms_ = 0;
  }
  const uint32_t invalid_ms = invalid_since_ms_ == 0 ? 0 : now_ms - invalid_since_ms_;
  const bool valid = commanded ? (bits == COOLING_FAULT_NONE && invalid_ms < FEEDBACK_DWELL_MS) :
      (bits & COOLING_IMPLAUSIBLE_WHILE_OFF) == 0;
  return {valid, fan1_running, fan2_running, bits, invalid_ms};
}
