#pragma once

#include <stdint.h>

struct TachEstimatorConfig {
  uint16_t pulses_per_revolution;
  float expected_min_rpm;
  float expected_max_rpm;
  float period_count_crossover_rpm;
  uint32_t count_window_us;
  uint8_t count_min_intervals;
  uint32_t timeout_us;
  uint32_t minimum_pulse_spacing_us;
  uint32_t filter_time_constant_us;
  float maximum_plausible_acceleration_rpm_s;
  float outlier_relative_tolerance;
};

enum class TachEstimateMode : uint8_t { NONE, PERIOD, COUNT, TIMEOUT };

struct TachEstimate {
  float rpm;
  bool valid;
  TachEstimateMode mode;
  uint32_t pulse_age_us;
  uint32_t accepted_pulses;
  uint32_t rejected_bounce_pulses;
  uint32_t rejected_outlier_periods;
};

// Timestamp-only production estimator. `onPulse()` is suitable for an ISR as
// long as the adapter protects `estimate()` with its platform atomic section.
// All timestamp subtraction intentionally uses uint32_t modular arithmetic.
class TachEstimator {
 public:
  bool configure(const TachEstimatorConfig &config);
  bool onPulse(uint32_t timestamp_us);
  TachEstimate estimate(uint32_t now_us);
  void reset();
  bool configured() const { return configured_; }

 private:
  float periodRpm(uint32_t period_us) const;
  void acceptPeriod(uint32_t period_us);

  TachEstimatorConfig config_{};
  bool configured_{false};
  bool has_pulse_{false};
  bool has_period_{false};
  bool has_filtered_{false};
  bool pending_outlier_{false};
  uint32_t last_pulse_us_{0};
  uint32_t period_us_{0};
  uint32_t pending_period_us_{0};
  uint32_t count_window_start_us_{0};
  uint32_t count_intervals_{0};
  bool count_estimate_valid_{false};
  float count_rpm_{0};
  float filtered_rpm_{0};
  uint32_t last_estimate_us_{0};
  uint32_t accepted_pulses_{0};
  uint32_t rejected_bounce_pulses_{0};
  uint32_t rejected_outlier_periods_{0};
};
