#pragma once
// Generated from control/tach_contract.json. Do not hand-edit channel values.

#include <stdint.h>

#include "tach_estimator.h"

enum class TachChannel : uint8_t { SHREDDER, SCREW, PULLER, SPOOLER };

constexpr TachEstimatorConfig SHREDDER_TACH_CONFIG{
    6, 5.0f, 80.0f, 40.0f, 1000000UL, 4, 2500000UL, 20000UL,
    250000UL, 120.0f, 0.35f};
constexpr TachEstimatorConfig SCREW_TACH_CONFIG{
    12, 1.0f, 25.0f, 16.0f, 1000000UL, 3, 6500000UL, 30000UL,
    350000UL, 30.0f, 0.35f};
constexpr TachEstimatorConfig PULLER_TACH_CONFIG{
    20, 1.0f, 30.0f, 10.0f, 1000000UL, 3, 4000000UL, 15000UL,
    250000UL, 45.0f, 0.35f};
constexpr TachEstimatorConfig SPOOLER_TACH_CONFIG{
    20, 0.5f, 30.0f, 10.0f, 1000000UL, 3, 7500000UL, 15000UL,
    300000UL, 40.0f, 0.35f};

inline const TachEstimatorConfig &tachConfig(TachChannel channel) {
  switch (channel) {
    case TachChannel::SHREDDER: return SHREDDER_TACH_CONFIG;
    case TachChannel::SCREW: return SCREW_TACH_CONFIG;
    case TachChannel::PULLER: return PULLER_TACH_CONFIG;
    case TachChannel::SPOOLER: return SPOOLER_TACH_CONFIG;
  }
  return SHREDDER_TACH_CONFIG;
}
