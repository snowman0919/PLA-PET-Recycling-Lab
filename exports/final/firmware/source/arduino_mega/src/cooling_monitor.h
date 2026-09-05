#pragma once

#include <stdint.h>

enum CoolingFaultBits : uint8_t {
  COOLING_FAULT_NONE = 0,
  COOLING_FAN1_STOPPED = 1 << 0,
  COOLING_FAN2_STOPPED = 1 << 1,
  COOLING_IMPLAUSIBLE_WHILE_OFF = 1 << 2,
};

struct CoolingMonitorOutput {
  bool valid;
  bool fan1_running;
  bool fan2_running;
  uint8_t fault_bits;
  uint32_t invalid_duration_ms;
};

class CoolingMonitor {
 public:
  CoolingMonitorOutput update(uint8_t commanded_pwm, float fan1_rpm, bool fan1_valid,
                              float fan2_rpm, bool fan2_valid, uint32_t now_ms);
  void reset();

 private:
  uint32_t invalid_since_ms_{0};
  uint32_t off_feedback_since_ms_{0};
};
