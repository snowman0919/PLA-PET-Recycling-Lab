#pragma once

#include <stdint.h>

enum class FeedDeliveryState : uint8_t {
  STOPPED,
  STARTING,
  FORWARD,
  DEGRADED_DERATE,
  ANOMALY_DWELL,
  RETRY_STOP,
  REVERSING,
  FAULT_LATCHED,
};

enum class FeedDeliveryFault : uint8_t {
  NONE,
  PERMISSION_LOSS,
  TACH_LOSS,
  OVERCURRENT,
  BRIDGE,
  JAM,
  RETRY_EXHAUSTED,
  INVALID_COMMAND,
};

struct FeedDeliveryConfig {
  float minimum_mass_flow_g_h;
  float maximum_mass_flow_g_h;
  float auger_rpm_per_g_h;
  float agitator_to_auger_ratio;
  float auger_max_rpm;
  float agitator_max_rpm;
  float auger_jam_current_a;
  float agitator_bridge_current_a;
  float auger_trip_current_a;
  float agitator_trip_current_a;
  float low_speed_ratio;
  float degraded_flow_ratio;
  uint8_t auger_minimum_pwm;
  uint8_t agitator_minimum_pwm;
  uint8_t maximum_pwm;
  uint16_t startup_grace_ms;
  uint16_t anomaly_dwell_ms;
  uint16_t retry_stop_ms;
  uint16_t reverse_ms;
  uint16_t tach_loss_timeout_ms;
  uint16_t degraded_stop_ms;
  uint8_t maximum_retries;
  bool calibration_verified;
};

struct FeedDeliveryInputs {
  uint32_t now_ms;
  float auger_rpm;
  float agitator_rpm;
  float auger_current_a;
  float agitator_current_a;
  bool auger_tach_valid;
  bool agitator_tach_valid;
  bool permission_chain_ok;
};

struct FeedDeliveryOutput {
  FeedDeliveryState state;
  FeedDeliveryFault fault;
  float requested_mass_flow_g_h;
  float commanded_mass_flow_g_h;
  float auger_target_rpm;
  float agitator_target_rpm;
  int16_t auger_pwm;
  int16_t agitator_pwm;
  uint8_t retry_count;
  bool derated;
  bool jam_detected;
  bool bridge_detected;
  bool inhibited;
};

class FeedDeliveryController {
 public:
  bool configure(const FeedDeliveryConfig& config);
  bool start(float requested_mass_flow_g_h, const FeedDeliveryInputs& inputs);
  FeedDeliveryOutput update(const FeedDeliveryInputs& inputs);
  void stop();
  bool clearFault(bool physical_lockout_confirmed, const FeedDeliveryInputs& inputs);

  FeedDeliveryState state() const { return state_; }
  FeedDeliveryFault fault() const { return fault_; }
  bool configured() const { return configured_; }

 private:
  static float clampf(float value, float low, float high);
  void latchFault(FeedDeliveryFault fault);
  void beginAnomaly(FeedDeliveryFault fault, uint32_t now_ms);
  FeedDeliveryOutput makeOutput(const FeedDeliveryInputs& inputs) const;

  FeedDeliveryConfig config_{};
  bool configured_{false};
  FeedDeliveryState state_{FeedDeliveryState::STOPPED};
  FeedDeliveryFault fault_{FeedDeliveryFault::NONE};
  FeedDeliveryFault pending_anomaly_{FeedDeliveryFault::NONE};
  float requested_mass_flow_g_h_{0.0f};
  uint8_t retry_count_{0};
  uint32_t phase_started_ms_{0};
  uint32_t forward_started_ms_{0};
  uint32_t last_auger_tach_ms_{0};
  uint32_t last_agitator_tach_ms_{0};
  bool saw_auger_tach_{false};
  bool saw_agitator_tach_{false};
};
