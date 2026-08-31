#include <cassert>
#include <iostream>

#include "heater_control.h"

int main() {
  HeaterController controller;
  TemperatureReading good{25.0f, true, false, 0};
  auto out = controller.update(0, good, 180.0f, true, true, true, 250);
  assert(out.duty_percent == 100.0f && out.fault_bits == 0);
  assert(processHeaterPhaseAllowed(MachineState::PREHEATING));
  assert(processHeaterPhaseAllowed(MachineState::EXTRUSION));
  assert(!processHeaterPhaseAllowed(MachineState::SHREDDING));
  out = controller.update(0, good, 180.0f, true, true, false, 500);
  assert((out.fault_bits & HEATER_PERMISSION_MISMATCH) != 0);
  assert(out.duty_percent == 0);
  assert(!controller.clearFault(false, true));
  assert(controller.clearFault(true, true));

  HeaterController anti_windup;
  HeaterOutput throttled{};
  for (uint32_t now = 250; now <= 10000; now += 250) {
    throttled = anti_windup.update(0, good, 180.0f, true, true, true, now);
    throttled = anti_windup.applyAllocation(0, 10.0f, now);
  }
  assert(throttled.allocation_deficit_percent > 0 && throttled.saturation_state);
  TemperatureReading at_target{180.0f, true, false, 10250};
  for (uint32_t now = 10250; now <= 70250; now += 250) {
    anti_windup.update(0, at_target, 180.0f, true, true, true, now);
    throttled = anti_windup.applyAllocation(0, 10.0f, now);
  }
  assert(throttled.requested_duty_percent < 20.0f);  // Applied-duty feedback unwinds denied demand.

  HeaterController stuck_on_guard;
  TemperatureReading heater_off{40.0f, true, false, 1};
  stuck_on_guard.update(0, heater_off, 180.0f, false, true, true, 1);
  heater_off.celsius += HEATER_UNEXPECTED_RISE_C + 1.0f;
  out = stuck_on_guard.update(0, heater_off, 180.0f, false, true, true,
                              1 + HEATER_UNEXPECTED_RISE_DWELL_MS);
  assert((out.fault_bits & HEATER_UNEXPECTED_RISE) != 0);  // Independent off-state rise path.

  TemperatureReading open{-273.0f, false, true, 750};
  out = controller.update(1, open, 195.0f, true, true, true, 750);
  assert((out.fault_bits & HEATER_SENSOR_OPEN) != 0);
  assert((out.fault_bits & HEATER_SENSOR_RANGE) != 0);
  assert(out.duty_percent == 0);
  std::cout << "HEATER_PID_TIME_PROPORTION_PROTECTIONS_OK\n";
}
