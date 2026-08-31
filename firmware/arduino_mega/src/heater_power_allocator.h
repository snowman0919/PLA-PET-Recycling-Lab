#pragma once

#include <stdint.h>

struct HeaterAllocation {
  float requested_duty[4];
  float allocated_duty[4];
  float allocation_deficit[4];
  float integrator_state[4];
  float allocated_power_w;
  bool saturated[4];
  bool actual_time_proportion_command[4];
};

class HeaterPowerAllocator {
 public:
  HeaterAllocation allocate(const float requested_duty[4], float phase_cap_w);
};
