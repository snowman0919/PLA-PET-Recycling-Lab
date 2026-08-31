#include <cassert>
#include <cmath>
#include <iostream>

#include "heater_power_allocator.h"

int main() {
  HeaterPowerAllocator allocator;
  const float all_cold[4] = {100, 100, 100, 100};
  auto out = allocator.allocate(all_cold, 300.0f);
  assert(out.allocated_power_w <= 300.001f);
  for (uint8_t i = 0; i < 4; ++i) {
    assert(out.allocated_duty[i] < out.requested_duty[i]);
    assert(out.allocation_deficit[i] > 0 && out.saturated[i]);
  }
  const float one_cold[4] = {100, 5, 5, 5};
  out = allocator.allocate(one_cold, 300.0f);
  assert(std::fabs(out.allocated_duty[0] - 100.0f) < 0.01f);
  assert(out.allocated_power_w < 300.0f);
  out = allocator.allocate(all_cold, 500.0f);
  assert(std::fabs(out.allocated_power_w - 360.0f) < 0.01f);
  std::cout << "HEATER_ALLOCATOR_PHASE_CAP_OK\n";
}
