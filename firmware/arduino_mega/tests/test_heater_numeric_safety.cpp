#include <cassert>
#include <cmath>
#include <limits>
#include <iostream>
#include "heater_control.h"

int main() {
  const float invalid[] = {std::numeric_limits<float>::quiet_NaN(),
      std::numeric_limits<float>::infinity(),
      -std::numeric_limits<float>::infinity()};
  for (float value : invalid) {
    HeaterController controller;
    TemperatureReading reading{value, true, false, 250};
    const auto out = controller.update(0, reading, 180, true, true, true, 250);
    assert(out.fault_bits != 0 && out.duty_percent == 0);
    assert(std::isfinite(out.duty_percent));
    const auto applied = controller.applyAllocation(0, 100, 251);
    assert(applied.allocated_duty_percent == 0 && !applied.time_proportion_on);
  }
  for (float target : invalid) {
    HeaterController controller;
    TemperatureReading reading{25, true, false, 250};
    const auto out = controller.update(0, reading, target, true, true, true, 250);
    assert(out.fault_bits != 0 && out.duty_percent == 0);
    assert(std::isfinite(out.integrator_state));
  }
  for (float allocation : invalid) {
    HeaterController controller;
    TemperatureReading reading{25, true, false, 250};
    controller.update(0, reading, 180, true, true, true, 250);
    const auto applied = controller.applyAllocation(0, allocation, 251);
    assert(applied.fault_bits != 0 && applied.allocated_duty_percent == 0);
    assert(!applied.time_proportion_on);
  }
  HeaterController global;
  TemperatureReading valid{25, true, false, 250};
  TemperatureReading open{25, false, true, 250};
  global.update(0, valid, 180, true, true, true, 250);
  global.update(1, open, 195, true, true, true, 250);
  const auto after_fault = global.applyAllocation(0, 100, 251);
  assert(after_fault.fault_bits != 0 && after_fault.allocated_duty_percent == 0);
  assert(!after_fault.time_proportion_on);
  assert(!global.clearFault(false, true));
  std::cout << "HEATER_NUMERIC_AND_GLOBAL_LATCH_PASS cases=10\n";
}
