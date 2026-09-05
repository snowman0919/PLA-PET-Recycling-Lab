#include "tach_estimator.h"

#include <math.h>

namespace {
constexpr float MICROS_PER_MINUTE = 60000000.0f;

float clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}

float relativeDifference(uint32_t a, uint32_t b) {
  const uint32_t larger = a > b ? a : b;
  if (larger == 0) return 0.0f;
  const uint32_t difference = a > b ? a - b : b - a;
  return static_cast<float>(difference) / static_cast<float>(larger);
}
}  // namespace

bool TachEstimator::configure(const TachEstimatorConfig &c) {
  const uint64_t slowest_period_us = c.pulses_per_revolution == 0 || c.expected_min_rpm <= 0
      ? 0
      : static_cast<uint64_t>(MICROS_PER_MINUTE /
                              (c.pulses_per_revolution * c.expected_min_rpm));
  configured_ = c.pulses_per_revolution > 0 && c.expected_min_rpm > 0 &&
      c.expected_max_rpm > c.expected_min_rpm &&
      c.period_count_crossover_rpm >= c.expected_min_rpm &&
      c.period_count_crossover_rpm <= c.expected_max_rpm && c.count_window_us > 0 &&
      c.count_min_intervals >= 2 && c.timeout_us > slowest_period_us &&
      c.minimum_pulse_spacing_us > 0 && c.filter_time_constant_us > 0 &&
      c.maximum_plausible_acceleration_rpm_s > 0 &&
      c.outlier_relative_tolerance > 0.0f && c.outlier_relative_tolerance < 1.0f;
  if (configured_) config_ = c;
  reset();
  return configured_;
}

void TachEstimator::reset() {
  has_pulse_ = false;
  has_period_ = false;
  has_filtered_ = false;
  pending_outlier_ = false;
  last_pulse_us_ = 0;
  period_us_ = 0;
  pending_period_us_ = 0;
  count_window_start_us_ = 0;
  count_intervals_ = 0;
  count_estimate_valid_ = false;
  count_rpm_ = 0;
  filtered_rpm_ = 0;
  last_estimate_us_ = 0;
  accepted_pulses_ = 0;
  rejected_bounce_pulses_ = 0;
  rejected_outlier_periods_ = 0;
}

float TachEstimator::periodRpm(uint32_t period_us) const {
  if (period_us == 0 || config_.pulses_per_revolution == 0) return 0.0f;
  return MICROS_PER_MINUTE /
      (static_cast<float>(config_.pulses_per_revolution) * static_cast<float>(period_us));
}

void TachEstimator::acceptPeriod(uint32_t pulse_period_us) {
  period_us_ = pulse_period_us;
  has_period_ = true;
  pending_outlier_ = false;
}

bool TachEstimator::onPulse(uint32_t timestamp_us) {
  if (!configured_) return false;
  if (!has_pulse_) {
    has_pulse_ = true;
    last_pulse_us_ = timestamp_us;
    count_window_start_us_ = timestamp_us;
    accepted_pulses_ = 1;
    return true;
  }

  const uint32_t pulse_period_us = timestamp_us - last_pulse_us_;
  if (pulse_period_us < config_.minimum_pulse_spacing_us) {
    ++rejected_bounce_pulses_;
    return false;
  }

  last_pulse_us_ = timestamp_us;
  ++accepted_pulses_;
  ++count_intervals_;

  const float candidate_rpm = periodRpm(pulse_period_us);
  const bool physically_plausible = candidate_rpm >= config_.expected_min_rpm * 0.5f &&
      candidate_rpm <= config_.expected_max_rpm * 1.25f;
  if (!physically_plausible) {
    ++rejected_outlier_periods_;
    pending_outlier_ = false;
    return true;
  }

  if (!has_period_) {
    acceptPeriod(pulse_period_us);
    return true;
  }

  if (relativeDifference(pulse_period_us, period_us_) <= config_.outlier_relative_tolerance) {
    acceptPeriod(pulse_period_us);
    return true;
  }

  // One discrepant interval is ignored (missing-pulse and edge-noise immunity).
  // A second consistent interval confirms a real speed/load step.
  if (pending_outlier_ &&
      relativeDifference(pulse_period_us, pending_period_us_) <= config_.outlier_relative_tolerance) {
    acceptPeriod(pulse_period_us);
  } else {
    pending_period_us_ = pulse_period_us;
    pending_outlier_ = true;
    ++rejected_outlier_periods_;
  }
  return true;
}

TachEstimate TachEstimator::estimate(uint32_t now_us) {
  TachEstimate out{};
  out.accepted_pulses = accepted_pulses_;
  out.rejected_bounce_pulses = rejected_bounce_pulses_;
  out.rejected_outlier_periods = rejected_outlier_periods_;
  if (!configured_ || !has_pulse_) return out;

  out.pulse_age_us = now_us - last_pulse_us_;
  if (out.pulse_age_us > config_.timeout_us) {
    out.mode = TachEstimateMode::TIMEOUT;
    has_filtered_ = false;
    filtered_rpm_ = 0;
    count_estimate_valid_ = false;
    count_intervals_ = 0;
    count_window_start_us_ = last_pulse_us_;
    return out;
  }
  if (!has_period_) return out;

  const uint32_t count_elapsed_us = last_pulse_us_ - count_window_start_us_;
  if (count_elapsed_us >= config_.count_window_us &&
      count_intervals_ >= config_.count_min_intervals) {
    count_rpm_ = MICROS_PER_MINUTE * static_cast<float>(count_intervals_) /
        (static_cast<float>(config_.pulses_per_revolution) *
         static_cast<float>(count_elapsed_us));
    count_estimate_valid_ = true;
    count_window_start_us_ = last_pulse_us_;
    count_intervals_ = 0;
  }

  const float reciprocal_rpm = periodRpm(period_us_);
  const bool use_count = count_estimate_valid_ &&
      reciprocal_rpm >= config_.period_count_crossover_rpm;
  const float raw_rpm = use_count ? count_rpm_ : reciprocal_rpm;
  out.mode = use_count ? TachEstimateMode::COUNT : TachEstimateMode::PERIOD;

  if (!has_filtered_) {
    filtered_rpm_ = raw_rpm;
    has_filtered_ = true;
  } else {
    uint32_t dt_us = now_us - last_estimate_us_;
    if (last_estimate_us_ == 0 || dt_us > config_.timeout_us) dt_us = config_.filter_time_constant_us;
    const float dt_s = static_cast<float>(dt_us) / 1000000.0f;
    const float maximum_change = config_.maximum_plausible_acceleration_rpm_s * dt_s;
    const float plausible_rpm = clampf(raw_rpm, filtered_rpm_ - maximum_change,
                                       filtered_rpm_ + maximum_change);
    const float alpha = static_cast<float>(dt_us) /
        static_cast<float>(config_.filter_time_constant_us + dt_us);
    filtered_rpm_ += alpha * (plausible_rpm - filtered_rpm_);
  }
  last_estimate_us_ = now_us;
  out.rpm = filtered_rpm_ < 0.0f ? 0.0f : filtered_rpm_;
  out.valid = true;
  return out;
}
