#pragma once

#include <stddef.h>
#include <stdint.h>

namespace recycler {

enum class SafetyState : uint8_t {
  SAFE_OFF,
  SELF_TEST,
  READY,
  RUNNING,
  PAUSED,
  FAULT_LATCHED,
  ESTOP_LATCHED,
};

enum class Phase : uint8_t {
  IDLE,
  SHRED,
  DRY_PREHEAT,
  EXTRUDE_SPOOL,
  COOLDOWN_CLEAN,
};

enum Fault : uint32_t {
  FAULT_NONE = 0,
  FAULT_ESTOP = 1UL << 0,
  FAULT_LID = 1UL << 1,
  FAULT_SERVICE = 1UL << 2,
  FAULT_THERMAL_CHAIN = 1UL << 3,
  FAULT_SENSOR = 1UL << 4,
  FAULT_HEARTBEAT = 1UL << 5,
  FAULT_PRESSURE = 1UL << 6,
  FAULT_AIRFLOW = 1UL << 7,
  FAULT_CONTACTOR = 1UL << 8,
  FAULT_JAM = 1UL << 9,
  FAULT_POWER_BUDGET = 1UL << 10,
  FAULT_PROTOCOL = 1UL << 11,
};

struct SafetyInputs {
  uint32_t now_ms;
  uint32_t heartbeat_age_ms;
  bool estop_loop_closed;
  bool lid_loop_closed;
  bool service_loop_closed;
  bool thermal_chain_closed;
  bool sensors_plausible;
  bool airflow_ok;
  bool contactor_feedback_on;
  bool reset_requested;
  bool start_requested;
  bool pause_requested;
  bool injected_jam_fault;
  bool injected_power_fault;
  bool injected_protocol_fault;
  float melt_pressure_mpa;
  Phase requested_phase;
};

struct SafetyOutputs {
  SafetyState state;
  Phase active_phase;
  uint32_t latched_faults;
  bool contactor_request;
  bool heater_master_enable;
  bool motor_master_enable;
  bool cooldown_fan_request;
};

class SafetyCore {
 public:
  SafetyCore();
  SafetyOutputs tick(const SafetyInputs& in);

 private:
  void latch(uint32_t faults, bool estop);
  bool reset_prerequisites(const SafetyInputs& in) const;
  SafetyOutputs outputs_for(const SafetyInputs& in) const;

  SafetyState state_;
  Phase phase_;
  uint32_t faults_;
  uint32_t state_since_ms_;
  uint32_t contactor_request_since_ms_;
  bool prior_contactor_request_;
};

struct HeaterConfig {
  float kp;
  float ki_per_s;
  float minimum_valid_c;
  float maximum_valid_c;
  float independent_limit_c;
  float maximum_rise_c_per_s;
  float minimum_expected_rise_c;
  uint32_t rise_window_ms;
};

struct HeaterResult {
  float duty;
  bool sensor_plausible;
  bool runaway_fault;
  bool overtemperature_fault;
};

class HeaterController {
 public:
  explicit HeaterController(const HeaterConfig& config);
  HeaterResult update(uint32_t now_ms, float setpoint_c, float measured_c, bool enabled);
  void reset(uint32_t now_ms, float measured_c);

 private:
  HeaterConfig config_;
  float integral_;
  float previous_temperature_c_;
  float rise_window_start_c_;
  uint32_t previous_ms_;
  uint32_t rise_window_start_ms_;
  bool initialized_;
};

struct PowerRequest {
  Phase phase;
  float non_heater_w;
  float extruder_heater_w;
  float dryer_pla_heater_w;
  float dryer_pet_heater_w;
};

struct PowerGrant {
  bool valid;
  float heater_scale;
  float extruder_heater_w;
  float dryer_pla_heater_w;
  float dryer_pet_heater_w;
  float total_w;
};

PowerGrant arbitrate_power(const PowerRequest& request, float derated_limit_w);

enum class JamState : uint8_t {
  NORMAL,
  FEED_LIMIT,
  STOP,
  REVERSE,
  RETRY,
  FAULT,
};

struct JamOutput {
  JamState state;
  bool feed_enable;
  bool drive_enable;
  bool reverse;
  uint8_t retry_count;
};

struct LoadFeatures {
  bool valid;
  float rms_current_a;
  float peak_current_a;
  float positive_current_derivative_a_per_s;
  float speed_ratio;
  float vibration_peak_g;
};

struct AdaptiveLoadConfig {
  float rms_limit_a;
  float peak_limit_a;
  float derivative_limit_a_per_s;
  float minimum_speed_ratio;
  float vibration_limit_g;
  float feed_limit_score;
  float overload_score;
};

struct AdaptiveLoadResult {
  bool sensor_plausible;
  bool overload;
  bool speed_drop;
  float score;
  float feed_scale;
  float drive_scale;
};

AdaptiveLoadResult evaluate_adaptive_load(const LoadFeatures& features,
                                          const AdaptiveLoadConfig& config);

class JamController {
 public:
  JamController();
  JamOutput update(uint32_t now_ms, bool overload, bool speed_drop);
  void reset(uint32_t now_ms);

 private:
  JamState state_;
  uint32_t state_since_ms_;
  uint32_t overload_since_ms_;
  uint8_t retry_count_;
};

}  // namespace recycler
