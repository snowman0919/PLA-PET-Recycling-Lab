#include <assert.h>
#include <math.h>
#include <stdint.h>

#include <fstream>
#include <iostream>
#include <string>

#include "tach_contract_generated.h"
#include "tach_estimator.h"

namespace {
constexpr float MICROS_PER_MINUTE = 60000000.0f;

const char *modeName(TachEstimateMode mode) {
  switch (mode) {
    case TachEstimateMode::NONE: return "NONE";
    case TachEstimateMode::PERIOD: return "PERIOD";
    case TachEstimateMode::COUNT: return "COUNT";
    case TachEstimateMode::TIMEOUT: return "TIMEOUT";
  }
  return "UNKNOWN";
}

struct TraceWriter {
  explicit TraceWriter(const char *path) {
    if (path != nullptr) {
      stream.open(path);
      stream << "channel,scenario,target_rpm,timestamp_us,estimate_rpm,valid,mode,pulse_age_us,"
                "accepted,bounce_rejected,outlier_rejected\n";
    }
  }

  void write(const char *channel, const char *scenario, float target, uint32_t timestamp,
             const TachEstimate &estimate) {
    if (!stream.is_open()) return;
    stream << channel << ',' << scenario << ',' << target << ',' << timestamp << ','
           << estimate.rpm << ',' << estimate.valid << ',' << modeName(estimate.mode) << ','
           << estimate.pulse_age_us << ',' << estimate.accepted_pulses << ','
           << estimate.rejected_bounce_pulses << ',' << estimate.rejected_outlier_periods << '\n';
  }

  std::ofstream stream;
};

uint32_t pulseInterval(const TachEstimatorConfig &config, float rpm, int index,
                       bool jitter) {
  const float nominal = MICROS_PER_MINUTE /
      (static_cast<float>(config.pulses_per_revolution) * rpm);
  static const float pattern[] = {-0.010f, 0.004f, 0.008f, -0.006f, 0.002f, 0.0f};
  const float scale = jitter ? 1.0f + pattern[index % 6] : 1.0f;
  return static_cast<uint32_t>(nominal * scale + 0.5f);
}

TachEstimate runTrain(TachEstimator &estimator, const TachEstimatorConfig &config,
                      const char *channel, const char *scenario, float rpm,
                      uint32_t &timestamp, int pulses, bool jitter, TraceWriter &trace,
                      int missing_index = -1, int bounce_index = -1) {
  TachEstimate estimate{};
  estimator.onPulse(timestamp);
  for (int pulse = 1; pulse < pulses; ++pulse) {
    timestamp += pulseInterval(config, rpm, pulse, jitter);
    if (pulse != missing_index) estimator.onPulse(timestamp);
    if (pulse == bounce_index)
      estimator.onPulse(timestamp + config.minimum_pulse_spacing_us / 2U);
    estimate = estimator.estimate(timestamp);
    trace.write(channel, scenario, rpm, timestamp, estimate);
  }
  return estimate;
}

void verifySpeed(const char *channel, const TachEstimatorConfig &config, float rpm,
                 TraceWriter &trace) {
  TachEstimator estimator;
  assert(estimator.configure(config));
  if (rpm == 0.0f) {
    const TachEstimate stopped = estimator.estimate(config.timeout_us + 1U);
    assert(!stopped.valid && stopped.rpm == 0.0f);
    trace.write(channel, "zero_no_pulse", rpm, config.timeout_us + 1U, stopped);
    return;
  }
  uint32_t timestamp = 1000U;
  TachEstimate estimate = runTrain(estimator, config, channel, "nominal_jitter", rpm,
                                    timestamp, 18, true, trace);
  assert(estimate.valid);
  const float relative_error = fabsf(estimate.rpm - rpm) / rpm;
  assert(relative_error <= 0.03f);

  // The minimum-speed interval remains valid until the contract timeout.
  const TachEstimate before_timeout = estimator.estimate(timestamp + config.timeout_us - 1U);
  assert(before_timeout.valid && before_timeout.rpm > 0.0f);
  trace.write(channel, "stale_before_timeout", rpm,
              timestamp + config.timeout_us - 1U, before_timeout);
  const TachEstimate timeout = estimator.estimate(timestamp + config.timeout_us + 1U);
  assert(!timeout.valid && timeout.rpm == 0.0f && timeout.mode == TachEstimateMode::TIMEOUT);
  trace.write(channel, "sudden_stop_timeout", rpm,
              timestamp + config.timeout_us + 1U, timeout);
}

void verifyFaultInjections(const char *channel, const TachEstimatorConfig &config,
                           float rpm, TraceWriter &trace) {
  uint32_t timestamp = 10000U;
  TachEstimator missing;
  assert(missing.configure(config));
  TachEstimate estimate = runTrain(missing, config, channel, "missing_pulse", rpm,
                                    timestamp, 20, false, trace, 9, -1);
  assert(estimate.valid && estimate.rpm > rpm * 0.7f && estimate.rpm < rpm * 1.1f);
  assert(estimate.rejected_outlier_periods >= 1U);

  timestamp = 20000U;
  TachEstimator bounce;
  assert(bounce.configure(config));
  estimate = runTrain(bounce, config, channel, "duplicate_bounce", rpm,
                      timestamp, 12, false, trace, -1, 5);
  assert(estimate.valid && estimate.rejected_bounce_pulses == 1U);
  assert(fabsf(estimate.rpm - rpm) / rpm <= 0.03f);

  timestamp = 30000U;
  TachEstimator load_step;
  assert(load_step.configure(config));
  runTrain(load_step, config, channel, "load_step_before", rpm, timestamp, 8, false, trace);
  const float reduced_rpm = rpm * 0.7f;
  estimate = runTrain(load_step, config, channel, "load_step_after", reduced_rpm,
                      timestamp, 18, false, trace);
  assert(estimate.valid && estimate.rpm <= rpm * 1.02f && estimate.rpm >= reduced_rpm * 0.8f);

  const uint32_t interval = pulseInterval(config, rpm, 0, false);
  timestamp = UINT32_MAX - interval / 2U;
  TachEstimator rollover;
  assert(rollover.configure(config));
  estimate = runTrain(rollover, config, channel, "timer_rollover", rpm,
                      timestamp, 12, false, trace);
  assert(estimate.valid && fabsf(estimate.rpm - rpm) / rpm <= 0.03f);

  TachEstimatorConfig mutated_config = config;
  ++mutated_config.pulses_per_revolution;
  TachEstimator mutation;
  assert(mutation.configure(mutated_config));
  timestamp = 50000U;
  estimate = runTrain(mutation, config, channel, "incorrect_ppr_mutation", rpm,
                      timestamp, 16, false, trace);
  assert(estimate.valid && fabsf(estimate.rpm - rpm) / rpm > 0.03f);
}
}  // namespace

int main(int argc, char **argv) {
  TraceWriter trace(argc > 1 ? argv[1] : nullptr);
  const float shredder_speeds[] = {0, 5, 24, 32, 40, 80};
  const float screw_speeds[] = {0, 1, 8, 16, 18, 25};
  const float puller_speeds[] = {0, 1, 3, 5.9f, 10, 30};
  const float spooler_speeds[] = {0, 0.5f, 0.9f, 3.4f, 10, 30};
  for (float rpm : shredder_speeds) verifySpeed("shredder", SHREDDER_TACH_CONFIG, rpm, trace);
  for (float rpm : screw_speeds) verifySpeed("screw", SCREW_TACH_CONFIG, rpm, trace);
  for (float rpm : puller_speeds) verifySpeed("puller", PULLER_TACH_CONFIG, rpm, trace);
  for (float rpm : spooler_speeds) verifySpeed("spooler", SPOOLER_TACH_CONFIG, rpm, trace);
  verifyFaultInjections("shredder", SHREDDER_TACH_CONFIG, 32.0f, trace);
  verifyFaultInjections("screw", SCREW_TACH_CONFIG, 18.0f, trace);
  verifyFaultInjections("puller", PULLER_TACH_CONFIG, 5.9f, trace);
  verifyFaultInjections("spooler", SPOOLER_TACH_CONFIG, 3.4f, trace);
  std::cout << "TACH_HYBRID_ALL_CHANNELS_OK\n";
  return 0;
}
