#pragma once

#include <stdint.h>

class FeederMotionMonitor {
 public:
  explicit FeederMotionMonitor(uint32_t timeout_ms) : timeout_ms_(timeout_ms) {}

  bool update(bool commanded, bool tach_high, uint32_t now_ms) {
    const bool rising = tach_high && !previous_high_;
    previous_high_ = tach_high;
    if (!commanded) {
      running_ = false;
      last_motion_ms_ = now_ms;
      return true;
    }
    if (!running_ || rising) last_motion_ms_ = now_ms;
    running_ = true;
    return now_ms - last_motion_ms_ <= timeout_ms_;
  }

 private:
  uint32_t timeout_ms_;
  uint32_t last_motion_ms_{0};
  bool previous_high_{false};
  bool running_{false};
};
