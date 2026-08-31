#pragma once

#include <stdint.h>

enum class TraverseHomingState : uint8_t {
  TRAVERSE_UNHOMED = 0,
  TRAVERSE_HOME_LEFT,
  TRAVERSE_BACKOFF,
  TRAVERSE_READY,
  TRAVERSE_RUNNING,
  TRAVERSE_FAULT,
};

enum class TraverseHomingFault : uint8_t {
  NONE = 0,
  CONFIGURATION,
  LIMIT_CONFLICT,
  HOME_TIMEOUT,
  LEFT_SWITCH_STUCK,
  RIGHT_SWITCH_STUCK,
  WRONG_DIRECTION,
};

struct TraverseHomingConfig {
  float steps_per_mm;
  float backoff_mm;
  uint16_t step_interval_ms;
  uint32_t home_timeout_ms;
  uint16_t switch_release_timeout_ms;
};

struct TraverseHomingOutput {
  bool enable;
  bool direction;
  bool step;
  bool homed;
  float estimated_position_mm;
  TraverseHomingState state;
  TraverseHomingFault fault;
};

class TraverseHomingController {
 public:
  bool configure(const TraverseHomingConfig &config);
  TraverseHomingOutput update(bool left_limit, bool right_limit, bool permission,
                              uint32_t now_ms);
  void setRunning(bool running);
  void losePosition();
  void resetFault();

  bool homed() const {
    return state_ == TraverseHomingState::TRAVERSE_READY ||
           state_ == TraverseHomingState::TRAVERSE_RUNNING;
  }
  TraverseHomingState state() const { return state_; }
  TraverseHomingFault fault() const { return fault_; }
  float estimatedPositionMm() const { return estimated_position_mm_; }

 private:
  void enterFault(TraverseHomingFault fault);
  bool stepDue(uint32_t now_ms);
  TraverseHomingOutput output(bool enable, bool direction, bool step) const;

  TraverseHomingConfig config_{};
  bool configured_{false};
  TraverseHomingState state_{TraverseHomingState::TRAVERSE_UNHOMED};
  TraverseHomingFault fault_{TraverseHomingFault::NONE};
  uint32_t state_started_ms_{0};
  uint32_t last_step_ms_{0};
  uint32_t backoff_steps_{0};
  uint32_t required_backoff_steps_{0};
  bool right_active_at_start_{false};
  float estimated_position_mm_{0};
};
