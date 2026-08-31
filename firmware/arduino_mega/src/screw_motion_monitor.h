#pragma once

#include <stdint.h>

struct ScrewMotionOutput {
  float actual_rpm;
  float cumulative_revolutions;
  bool tach_valid;
  bool command_motion_mismatch;
  uint32_t mismatch_duration_ms;
};

class ScrewMotionMonitor {
 public:
  ScrewMotionOutput update(float commanded_rpm, float actual_rpm, bool tach_sample_valid,
                           uint32_t now_ms);
  void reset();

 private:
  float cumulative_revolutions_{0};
  uint32_t last_ms_{0};
  uint32_t mismatch_since_ms_{0};
  uint32_t last_valid_tach_ms_{0};
};
