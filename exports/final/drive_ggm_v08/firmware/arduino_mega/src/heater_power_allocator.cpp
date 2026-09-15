#include "heater_power_allocator.h"

namespace {
float clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}
}

HeaterAllocation HeaterPowerAllocator::allocate(const float requested[4], float phase_cap_w) {
  constexpr float watts[4] = {100.0f, 100.0f, 100.0f, 60.0f};
  HeaterAllocation out{};
  float requested_power = 0;
  for (uint8_t i = 0; i < 4; ++i) {
    out.requested_duty[i] = clampf(requested[i], 0.0f, 100.0f);
    requested_power += watts[i] * out.requested_duty[i] / 100.0f;
  }
  const float cap = clampf(phase_cap_w, 0.0f, 500.0f);
  const float scale = requested_power > cap && requested_power > 0 ? cap / requested_power : 1.0f;
  for (uint8_t i = 0; i < 4; ++i) {
    out.allocated_duty[i] = out.requested_duty[i] * scale;
    out.allocation_deficit[i] = out.requested_duty[i] - out.allocated_duty[i];
    out.saturated[i] = out.allocation_deficit[i] > 0.01f;
    out.allocated_power_w += watts[i] * out.allocated_duty[i] / 100.0f;
  }
  return out;
}
