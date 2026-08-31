#pragma once

#include <stdint.h>

struct TraverseConfig {
  float usable_width_mm;
  float winding_pitch_mm;
  float steps_per_mm;
  uint16_t missed_limit_timeout_ms;
};

struct TraverseOutput {
  bool enable;
  bool direction;
  bool step;
  float target_position_mm;
  float estimated_position_mm;
  bool hard_fault;
  bool pitch_synchronized;
};

class TraverseController {
 public:
  bool configure(const TraverseConfig &config);
  TraverseOutput update(float spool_turns, bool left_limit, bool right_limit,
                        bool enabled, uint32_t now_ms);
  void reset();

 private:
  TraverseConfig config_{};
  bool configured_{false};
  float estimated_position_mm_{0};
  uint32_t last_step_ms_{0};
  uint32_t endpoint_expected_since_ms_{0};
  bool has_seen_interior_{false};
  bool hard_fault_{false};
};
